"""Gates for the BIGVILLE SCALE-VERIFICATION probe (block 248000).

Pre-registered in BIGVILLE_SCALE_PREREG.md. These gates protect the deciding
numbers:
  * the instrument CAN detect quadratic (the all-pairs control measures slope ~2);
  * the sparse (realized, proximity-gated) arm is sub-quadratic (slope < 1.5) and
    CI-separated below the all-pairs control;
  * the 30-townspeople population is NOT cloned (non-zero param variance;
    sigma->0 recovers identical agents);
  * discipline: additive-only, no forbidden Python rule-engine calls in the new
    files, own engine matches the 245/246 baseline (zero Rust).

Kept FAST (small N grid, few placements) so it lives in the migrated bench.
"""
import math
import os

import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

from worlds.bigville_scale_world import BigvilleScaleWorld       # noqa: E402
import scripts.bigville_town_seed as town                        # noqa: E402


def _ols_slope(xs, ys):
    x = np.asarray(xs, float); y = np.asarray(ys, float)
    xm = x.mean(); ym = y.mean()
    return float(((x - xm) * (y - ym)).sum() / ((x - xm) ** 2).sum())


def _measure(arm, N_grid, R=8, T=3, k0=2.5):
    per_n = {}
    for N in N_grid:
        vals = []
        for r in range(R):
            w = BigvilleScaleWorld(N, arm=arm, k0=k0, place_seed=248000 + N * 1000 + r)
            w.run(T=T)
            vals.append(w.mean_ops())
            w.close()
        per_n[N] = float(np.mean(vals))
    slope = _ols_slope([math.log(N) for N in N_grid],
                       [math.log(per_n[N]) for N in N_grid])
    return slope, per_n


N_GRID = [5, 10, 20, 30]


@pytest.fixture(scope="module")
def arms():
    s_slope, s_means = _measure("sparse", N_GRID)
    a_slope, a_means = _measure("all_pairs", N_GRID)
    return dict(s_slope=s_slope, s_means=s_means, a_slope=a_slope, a_means=a_means)


def test_all_pairs_census_is_exactly_quadratic():
    """The control arm realizes EVERY ordered pair: ops == N*(N-1), exactly."""
    for N in (5, 12, 30):
        w = BigvilleScaleWorld(N, arm="all_pairs", place_seed=248000 + N)
        w.run(T=2)
        assert w.mean_ops() == N * (N - 1)
        w.close()


def test_instrument_can_detect_quadratic(arms):
    """The falsifier that MUST be able to fail: the all-pairs control measures a
    log-log slope ~2.0 -- so the instrument distinguishes linear from quadratic."""
    assert 1.8 <= arms["a_slope"] <= 2.2, arms["a_slope"]


def test_sparse_arm_is_sub_quadratic_and_separated(arms):
    """HEADLINE: realized (proximity-gated) interaction-ops grow sub-quadratically
    (slope < 1.5) and the sparse arm is slope-separated BELOW the all-pairs
    control -- realized social interaction is local/bounded-degree, not all-pairs."""
    assert arms["s_slope"] < 1.5, arms["s_slope"]
    assert arms["s_slope"] < arms["a_slope"] - 0.5, (arms["s_slope"], arms["a_slope"])


def test_sparse_degree_is_bounded(arms):
    """Bounded local degree: realized ops-per-capita stays bounded as N grows
    (it does NOT climb toward N-1, which is the all-pairs signature)."""
    per_capita = {N: arms["s_means"][N] / N for N in N_GRID}
    assert max(per_capita.values()) < 4.0, per_capita          # k0=2.5 regime
    # per-capita at N=30 is nowhere near the all-pairs (N-1)=29
    assert per_capita[30] < 5.0


def test_population_is_not_cloned():
    """G-population: heterogeneous draws => non-zero param variance; sigma->0
    recovers identical agents (the zero-variance cloning TELL)."""
    pop = town.draw_population(30, sigma_scale=1.0)
    sd = town.population_param_sd(pop)
    assert min(sd.values()) > 0.0, sd
    clones = town.draw_population(30, sigma_scale=0.0)
    csd = town.population_param_sd(clones)
    assert max(csd.values()) < 1e-9, csd


def test_seed_manifest_shape():
    """Deliverable 1: 30 inhabitants, the core roles all present, sparse
    (bounded-degree) relationship graph -- not all-pairs."""
    m = town.build_seed_manifest()
    assert len(m["inhabitants"]) == 30
    roles = {p["role"] for p in m["inhabitants"]}
    for core in ("mayor", "pastor", "reporter", "constable", "council", "clerk"):
        assert core in roles, (core, roles)
    assert sum(1 for p in m["inhabitants"] if p["role"] == "council") == 4
    # sparse ties: average degree well below N (bounded-degree village)
    deg = 2 * len(m["relationships"]) / len(m["inhabitants"])
    assert deg < 4.0, deg


def test_no_forbidden_python_rule_engine_calls():
    """Architecture rule: the new files must not run the Python rule engine or
    make agent decisions via it."""
    forbidden = ("graph_rewrite.run", "gr.run(", "._match(", "._apply(", "make_rule(")
    files = [
        os.path.join(_ROOT, "worlds", "bigville_scale_world.py"),
        os.path.join(_ROOT, "scripts", "bigville_town_seed.py"),
        os.path.join(_ROOT, "scripts", "bigville_scale_run.py"),
    ]
    for fp in files:
        src = open(fp).read()
        for tok in forbidden:
            assert tok not in src, (fp, tok)


# NOTE (supervisor, 2026-07-29): removed `test_own_engine_matches_245_246_baseline`.
# It hardcoded the authoring WORKTREE's own-build md5 (10f65be6…) and asserted the
# loaded .so equalled it — true in the worktree, FALSE on main (canonical fd82dc29…):
# a lesson-7b green-where-authored/red-where-landed defect. The "zero Rust added"
# invariant it meant to check is enforced correctly elsewhere: the empty runners/dsl
# diff + the supervisor's merge-time canonical-.so-md5-unchanged check + the
# engine-provenance gate. A per-rung shipped test must never pin a context-specific
# engine identity.
