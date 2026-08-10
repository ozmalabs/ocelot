"""bigville_econ_scale_run -- the R4 (block 252000) SCALE gate: the 248000 scale
probe RE-RUN with movement+ECONOMY ON.

Ramps N and measures the realized EXCHANGE-op count per tick vs N for two arms:

  * local     (HEADLINE) -- LOCAL co-located exchange. Pre-registered gate: fitted
                            log-log slope < 1.5 (SUB-QUADRATIC, because exchange is
                            local).
  * all_pairs (CONTROL / falsifier) -- a GLOBAL market clear (every buyer x every
                            shop). MUST measure slope ~2.0 and sit CI-separated
                            ABOVE the local arm. An economy-on ~2.0 would be a real
                            all-pairs bug to REPORT.

Identical instrument to 248000 (constant-density torus, OLS slope on
log(mean_ops)~log(N), 2000-sample bootstrap CI over placements). Pre-registered in
BIGVILLE_ECON_PREREG.md. Pure measurement + counting; no agent decisions. Writes
results/bigville_econ/scale.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))

from worlds.bigville_econ_scale_world import (                 # noqa: E402
    BigvilleEconScaleWorld, SHOP_DENSITY, EXCH_RANGE)

N_GRID = [5, 10, 15, 20, 25, 30]
R_PLACEMENTS = 30
T_TICKS = 12
N_BOOT = 2000
SEED_BASE = 252000
OUT_DIR = os.path.join(_ROOT, "results", "bigville_econ")
CANONICAL_SO = os.path.join(
    "/home/matt/ozma/internal/research/experiments/gamma-substrate",
    "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
OWN_SO = os.path.join(_ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")


def _md5(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return None


def _ols_slope(xs, ys):
    x = np.asarray(xs, float); y = np.asarray(ys, float)
    xm = x.mean(); ym = y.mean()
    return float(((x - xm) * (y - ym)).sum() / ((x - xm) ** 2).sum())


def measure_arm(arm):
    per_n = {}
    for N in N_GRID:
        vals = []
        for r in range(R_PLACEMENTS):
            w = BigvilleEconScaleWorld(N, arm=arm, place_seed=SEED_BASE + N * 1000 + r)
            w.run(T=T_TICKS)
            vals.append(w.mean_econ_ops())
        per_n[N] = vals
    return per_n


def fit_with_ci(per_n):
    logN = [np.log(N) for N in N_GRID]
    means = {N: float(np.mean(per_n[N])) for N in N_GRID}
    point = _ols_slope(logN, [np.log(means[N]) for N in N_GRID])
    rng = np.random.default_rng(SEED_BASE + 777)
    slopes = []
    for _ in range(N_BOOT):
        ys = [np.log(rng.choice(np.asarray(per_n[N], float),
                                size=len(per_n[N]), replace=True).mean())
              for N in N_GRID]
        slopes.append(_ols_slope(logN, ys))
    lo, hi = np.percentile(slopes, [2.5, 97.5])
    return point, float(lo), float(hi), means


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()
    canon_start = _md5(CANONICAL_SO)
    own_md5 = _md5(OWN_SO)

    local = measure_arm("local")
    allp = measure_arm("all_pairs")
    l_slope, l_lo, l_hi, l_means = fit_with_ci(local)
    a_slope, a_lo, a_hi, a_means = fit_with_ci(allp)
    separated = l_hi < a_lo
    canon_end = _md5(CANONICAL_SO)

    result = dict(
        block=SEED_BASE, prereg="BIGVILLE_ECON_PREREG.md",
        instrument=dict(N_grid=N_GRID, R_placements=R_PLACEMENTS, T_ticks=T_TICKS,
                        n_bootstrap=N_BOOT, shop_density=SHOP_DENSITY,
                        exch_range=EXCH_RANGE, torus=True, constant_density=True,
                        note="economy ON: realized co-located EXCHANGE-ops per tick"),
        local=dict(slope=l_slope, ci95=[l_lo, l_hi], mean_ops_by_N=l_means,
                   per_capita={str(N): l_means[N] / N for N in N_GRID}),
        all_pairs=dict(slope=a_slope, ci95=[a_lo, a_hi], mean_ops_by_N=a_means),
        separated=bool(separated),
        gates=dict(
            g_scale_local_subquadratic=bool(l_slope < 1.5),
            g_scale_local_ci_upper_lt_1_5=bool(l_hi < 1.5),
            g_scale_allpairs_is_2=bool(1.8 <= a_slope <= 2.2),
            g_scale_separated=bool(separated),
        ),
        discipline=dict(
            own_so_md5=own_md5,
            baseline_245_246_own_md5="10f65be659e0d9a9290aff39f7f5b92a",
            source_match_own=bool(own_md5 == "10f65be659e0d9a9290aff39f7f5b92a"),
            canonical_so_md5_start=canon_start, canonical_so_md5_end=canon_end,
            canonical_unchanged=bool(canon_start == canon_end)),
        wall_seconds=time.time() - t0)

    with open(os.path.join(OUT_DIR, "scale.json"), "w") as f:
        json.dump(result, f, indent=2)

    print("=" * 68)
    print("BIGVILLE R4 ECONOMY SCALE GATE (block 252000) -- economy ON")
    print("=" * 68)
    print("N grid:", N_GRID, "| R:", R_PLACEMENTS, "| T:", T_TICKS,
          "| shop_density:", SHOP_DENSITY)
    print("\nLOCAL (headline) realized exchange-ops per tick:")
    for N in N_GRID:
        print("  N=%2d  mean_ops=%8.2f  per_capita=%.3f" % (N, l_means[N], l_means[N] / N))
    print("  slope = %.3f  CI95 = [%.3f, %.3f]" % (l_slope, l_lo, l_hi))
    print("\nALL-PAIRS (control / falsifier):")
    for N in N_GRID:
        print("  N=%2d  mean_ops=%8.2f" % (N, a_means[N]))
    print("  slope = %.3f  CI95 = [%.3f, %.3f]" % (a_slope, a_lo, a_hi))
    print("\nseparated (local hi < allpairs lo): %s  (%.3f < %.3f)"
          % (separated, l_hi, a_lo))
    print("\nGATES:")
    for k, v in result["gates"].items():
        print("  %-34s %s" % (k, "PASS" if v else "FAIL"))
    print("\nDISCIPLINE: own .so md5", own_md5, "(source_match_own:",
          result["discipline"]["source_match_own"], ")")
    print("  canonical start==end:", result["discipline"]["canonical_unchanged"])
    print("\nwrote", os.path.join(OUT_DIR, "scale.json"), "in %.1fs" % result["wall_seconds"])


if __name__ == "__main__":
    main()
