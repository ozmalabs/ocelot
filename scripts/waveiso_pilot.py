"""waveiso_pilot — VARIANCE ONLY, on BURNED seeds 0-13. Fixes n for the
confirmatory run (§3.3). Burns nothing new.

Reports the per-seed sd of every statistic the pre-registration will read, so n
is fixed by a power analysis rather than by taste. No confirmatory seed is
touched, and no arm comparison is made here.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# waveiso_lib calls engine_preamble() at import, before any domains.* import.
from scripts.waveiso_lib import (anisotropy, centre_slice, corr_from_R,
                                 eigen_report, front_stats, local_vs_global,
                                 make_world, movie_autocorr, provenance_line,
                                 record_bursting, structure_tensor_coherence,
                                 window_movie)

import numpy as np

HALF, RF, RMAX, WINDOW = 3, 7, 6, 2
H = W = 64
STEPS, BURN_IN = 200, 20
PILOT_SEEDS = list(range(14))          # 0-13, already burned


def measure(seed):
    w = make_world(seed, H, W)
    b = record_bursting(w, steps=STEPS, burn_in=BURN_IN)
    x = window_movie(b, WINDOW)
    R, per, mu = movie_autocorr(x, RMAX)
    rho = corr_from_R(centre_slice(R, HALF), mu)
    A2g, A2pf = local_vs_global(per, mu, HALF, m=2)
    cohL, cohG = structure_tensor_coherence(x, RF)
    eig = eigen_report(R, mu, RF, centred=False)
    eigc = eigen_report(R, mu, RF, centred=True)
    lam = eig["eigenvalues"]
    return {
        "seed": seed, "density": mu,
        "A2_global": A2g, "A2_perframe": A2pf,
        "A4_global": anisotropy(rho, HALF, 4),
        "coh_local_RF": cohL, "coh_global": cohG,
        "M_leading_OI": eig["leading_OI"], "M_leading_DC": eig["leading_DC"],
        "M_l1_over_l2": eig["degeneracy_l1_over_l2"],
        "M_l2_over_l3": float(lam[1] / lam[2]),
        "Sigma_leading_OI": eigc["leading_OI"],
        "Sigma_leading_DC": eigc["leading_DC"],
        "Sigma_l1_over_l2": eigc["degeneracy_l1_over_l2"],
        "front_nb_windowed": front_stats(x)["neighbours_mean"],
        "front_nb_raw": front_stats(b)["neighbours_mean"],
        "frames_dead": front_stats(x)["frames_dead"],
    }


def main():
    print(provenance_line())
    rows = [measure(s) for s in PILOT_SEEDS]
    keys = [k for k in rows[0] if k != "seed"]
    print(f"\n{'statistic':22s} {'mean':>10s} {'sd':>10s} {'min':>10s} {'max':>10s}")
    stats = {}
    for k in keys:
        v = np.array([r[k] for r in rows], float)
        stats[k] = {"mean": float(v.mean()), "sd": float(v.std(ddof=1)),
                    "min": float(v.min()), "max": float(v.max())}
        print(f"{k:22s} {v.mean():10.4f} {v.std(ddof=1):10.4f} "
              f"{v.min():10.4f} {v.max():10.4f}")

    # n for a paired one-sample t at alpha=0.05, power 0.90, for a shift of
    # SESOI: n >= (1.96+1.28)^2 * sd^2 / SESOI^2. SESOI is set in the PREREG
    # from the CONTROLS' separation, not here.
    print("\n# n = (1.96+1.28)^2 * sd^2 / SESOI^2, per statistic; SESOI in PREREG")
    with open("results/waveiso_pilot.json", "w") as fh:
        json.dump({"provenance": provenance_line(), "rows": rows,
                   "stats": stats}, fh, indent=1)


if __name__ == "__main__":
    main()
