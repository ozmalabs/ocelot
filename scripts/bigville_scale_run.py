"""bigville_scale_run -- the SCALE-VERIFICATION probe (block 248000, Deliverable 2).

Ramps N over the proven scaffold's interaction loop (perception + drama + journal
+ newspaper) and MEASURES the realized interaction-ops per tick vs N. Fits the
log-log slope with a bootstrap CI, for two arms:

  * sparse    (HEADLINE) -- proximity/LOS-gated realized perception pairs.
  * all_pairs (CONTROL)  -- the gate removed: N*(N-1). MUST measure slope ~2.0,
                            proving the instrument distinguishes linear from
                            quadratic; the sparse arm must be CI-separated below it.

Pre-registered in BIGVILLE_SCALE_PREREG.md. Pure measurement + counting; no agent
decisions. Writes results/bigville_scale/results.json.
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

from worlds.bigville_scale_world import (                    # noqa: E402
    BigvilleScaleWorld, draw_population, population_param_sd, PERC_WINDOW)

# ---- pre-registered instrument (BIGVILLE_SCALE_PREREG.md) -----------------
N_GRID = [5, 10, 15, 20, 25, 30]
R_PLACEMENTS = 30
T_TICKS = 12
K0 = 2.5
OCC_DENSITY = 0.08
SEED_BASE = 248000
N_BOOT = 2000
OUT_DIR = os.path.join(_ROOT, "results", "bigville_scale")
CANONICAL_SO = os.path.join(  # the SHARED engine -- must never be written through
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
    """slope of ys ~ xs (least squares)."""
    x = np.asarray(xs, float); y = np.asarray(ys, float)
    xm = x.mean(); ym = y.mean()
    denom = ((x - xm) ** 2).sum()
    return float(((x - xm) * (y - ym)).sum() / denom)


def measure_arm(arm, place_seed_base):
    """For each N: R placements, each running T ticks of the full loop; collect
    per-placement mean realized-ops + per-placement mean wall-clock (ms)."""
    per_n_ops = {}     # N -> [mean_ops per placement]
    per_n_wall = {}    # N -> [mean_wall_ms per placement]
    for N in N_GRID:
        ops_list = []; wall_list = []
        for r in range(R_PLACEMENTS):
            seed = place_seed_base + N * 1000 + r
            w = BigvilleScaleWorld(N, arm=arm, k0=K0, occ_density=OCC_DENSITY,
                                   place_seed=seed)
            w.run(T=T_TICKS)
            ops_list.append(w.mean_ops())
            wall_list.append(w.mean_wall_ms())
            w.close()
        per_n_ops[N] = ops_list
        per_n_wall[N] = wall_list
    return per_n_ops, per_n_wall


def fit_with_ci(per_n_ops):
    """Point slope = OLS on log(mean_ops(N)) ~ log(N). CI = bootstrap resampling
    placements. Returns (slope, lo, hi, mean_ops_by_N)."""
    logN = [np.log(N) for N in N_GRID]
    means = {N: float(np.mean(per_n_ops[N])) for N in N_GRID}
    point = _ols_slope(logN, [np.log(means[N]) for N in N_GRID])
    rng = np.random.default_rng(SEED_BASE + 777)
    slopes = []
    for _ in range(N_BOOT):
        ys = []
        for N in N_GRID:
            arr = np.asarray(per_n_ops[N], float)
            samp = rng.choice(arr, size=len(arr), replace=True)
            ys.append(np.log(samp.mean()))
        slopes.append(_ols_slope(logN, ys))
    lo, hi = np.percentile(slopes, [2.5, 97.5])
    return point, float(lo), float(hi), means


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    t_start = time.time()
    canon_start = _md5(CANONICAL_SO)
    own_md5 = _md5(OWN_SO)

    # ---- the two arms -----------------------------------------------------
    sparse_ops, sparse_wall = measure_arm("sparse", SEED_BASE)
    allp_ops, allp_wall = measure_arm("all_pairs", SEED_BASE)

    s_slope, s_lo, s_hi, s_means = fit_with_ci(sparse_ops)
    a_slope, a_lo, a_hi, a_means = fit_with_ci(allp_ops)
    separated = s_hi < a_lo

    # ---- population variance (G-population-not-cloned) --------------------
    pop = draw_population(30, seed=SEED_BASE, sigma_scale=1.0)
    pop_sd = population_param_sd(pop)
    clones = draw_population(30, seed=SEED_BASE, sigma_scale=0.0)
    clone_sd = population_param_sd(clones)

    canon_end = _md5(CANONICAL_SO)

    result = dict(
        block=SEED_BASE,
        prereg="BIGVILLE_SCALE_PREREG.md",
        instrument=dict(N_grid=N_GRID, R_placements=R_PLACEMENTS, T_ticks=T_TICKS,
                        k0=K0, occ_density=OCC_DENSITY, perc_window=PERC_WINDOW,
                        n_bootstrap=N_BOOT, torus=True, constant_density=True),
        sparse=dict(slope=s_slope, ci95=[s_lo, s_hi], mean_ops_by_N=s_means,
                    per_capita={str(N): s_means[N] / N for N in N_GRID},
                    wall_ms_by_N={str(N): float(np.mean(sparse_wall[N])) for N in N_GRID}),
        all_pairs=dict(slope=a_slope, ci95=[a_lo, a_hi], mean_ops_by_N=a_means,
                       wall_ms_by_N={str(N): float(np.mean(allp_wall[N])) for N in N_GRID}),
        separated=bool(separated),
        population=dict(param_sd_sigma1=pop_sd, param_sd_sigma0=clone_sd,
                        max_clone_sd=float(max(clone_sd.values())),
                        min_sigma1_sd=float(min(pop_sd.values()))),
        gates=dict(
            # G-linear (pre-registered): the FITTED (point) sparse slope < 1.5.
            g_linear=bool(s_slope < 1.5),
            g_linear_ci_upper_lt_1_5=bool(s_hi < 1.5),        # stricter diagnostic
            g_instrument_allpairs_is_2=bool(1.8 <= a_slope <= 2.2),
            g_instrument_separated=bool(separated),
            g_population_not_cloned=bool(min(pop_sd.values()) > 0.0
                                         and max(clone_sd.values()) < 1e-9),
        ),
        discipline=dict(
            own_so_md5=own_md5,
            baseline_245_246_own_md5="10f65be659e0d9a9290aff39f7f5b92a",
            source_match_own=bool(own_md5 == "10f65be659e0d9a9290aff39f7f5b92a"),
            canonical_so_md5_start=canon_start,
            canonical_so_md5_end=canon_end,
            canonical_unchanged=bool(canon_start == canon_end),
        ),
        wall_seconds=time.time() - t_start,
    )
    # per-placement raw (reproducibility)
    result["raw"] = dict(
        sparse_ops={str(N): sparse_ops[N] for N in N_GRID},
        all_pairs_ops={str(N): allp_ops[N] for N in N_GRID})

    with open(os.path.join(OUT_DIR, "results.json"), "w") as f:
        json.dump(result, f, indent=2)

    # ---- console summary --------------------------------------------------
    print("=" * 68)
    print("BIGVILLE SCALE-VERIFICATION (block 248000)")
    print("=" * 68)
    print("N grid:", N_GRID, "| R placements:", R_PLACEMENTS, "| T ticks:", T_TICKS)
    print("\nSPARSE (headline) realized-ops per tick:")
    for N in N_GRID:
        print("  N=%2d  mean_ops=%8.2f  per_capita=%.3f  wall=%.2fms" % (
            N, s_means[N], s_means[N] / N, float(np.mean(sparse_wall[N]))))
    print("  slope = %.3f  CI95 = [%.3f, %.3f]" % (s_slope, s_lo, s_hi))
    print("\nALL-PAIRS (control) realized-ops per tick:")
    for N in N_GRID:
        print("  N=%2d  mean_ops=%8.2f" % (N, a_means[N]))
    print("  slope = %.3f  CI95 = [%.3f, %.3f]" % (a_slope, a_lo, a_hi))
    print("\nseparated (sparse hi < allpairs lo): %s  (%.3f < %.3f)"
          % (separated, s_hi, a_lo))
    print("\npopulation param sd (sigma=1) min=%.4f ; clone (sigma=0) max=%.2e"
          % (min(pop_sd.values()), max(clone_sd.values())))
    print("\nGATES:")
    for k, v in result["gates"].items():
        print("  %-32s %s" % (k, "PASS" if v else "FAIL"))
    print("\nDISCIPLINE:")
    print("  own .so md5        :", own_md5, "(source_match=own:",
          result["discipline"]["source_match_own"], ")")
    print("  canonical start==end:", result["discipline"]["canonical_unchanged"],
          "(", canon_start, ")")
    print("\nwrote", os.path.join(OUT_DIR, "results.json"),
          "in %.1fs" % result["wall_seconds"])


if __name__ == "__main__":
    main()
