"""waveiso_calibrate — §1 gates for the wave-isotropy instrument. BURNED SEEDS ONLY.

Runs on seeds 0-13 (already burned; declared as calibration in the ledger). No
confirmatory seed is touched here.

THE GATES, and why each exists:

  1. FLOOR — white noise, density MATCHED to the waves. An isotropic ensemble
     must read A_2 ~= 0 in BOTH the global and the local frame. This also fixes
     A_local's NOISE FLOOR, which is NOT zero: A_local is a mean of MAGNITUDES
     and is positively biased by finite sampling. Reading A_local against an
     assumed floor of 0 would manufacture "local anisotropy" out of noise.
  2. IDEAL — bars at ONE fixed orientation. Must read A_2 HIGH in both frames,
     and its leading eigenvector must be ORIENTED (OI high). If the instrument
     cannot see this, every number it produces is worthless.
  3. THE DISCRIMINATOR — bars at RANDOM per-frame orientations. Anisotropic in
     every frame, isotropic in the ensemble. MUST read global ~= floor AND
     local >> floor. This is the ONLY control that tests the local-vs-global
     claim itself; without it, "structure exists per-frame but averages away" is
     an untested property of the instrument rather than a finding.
  4. ARMS ALIVE (§1 clause 4) — "scores at the floor" is satisfied by DEATH.
     Every arm reports its density and dead-frame count. A silent arm is a
     FAILED GATE, never a good floor.

A measure that passes 1 and 2 but not 3 can still not tell "per-frame structure"
from "ensemble structure" — which is the whole question of measurement (2).
"""
from __future__ import annotations

import json

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# waveiso_lib calls engine_preamble() at import, BEFORE any domains.* import
# (§10.1 rule 3). Importing it first is therefore load-bearing, not stylistic.
from scripts.waveiso_lib import (anisotropy, bar_movie, centre_slice,
                                 corr_from_R, corr_length, disk_movie,
                                 eigen_report, front_stats, local_vs_global,
                                 make_world, movie_autocorr, provenance_line,
                                 radial_profile, record_bursting,
                                 second_moment_matrix,
                                 structure_tensor_coherence, white_noise_movie,
                                 window_movie)

import numpy as np

HALF = 3          # rf//2 for the committed rf=7 — the RF's own half-width
RF = 7            # add_units' committed default
# R must reach rf-1: the second moment needs R(d_a - d_b) and the extreme RF
# offsets differ by 6. Falls out of rf=7, not chosen.
RMAX = RF - 1
WINDOW = 2        # WaveParams.window_steps, committed default (read, not chosen)
H = W = 64        # see PREREG §2 for why 64
STEPS = 200
BURN_IN = 20


def analyse(movie, label):
    R, per, mu = movie_autocorr(movie, RMAX)
    rho = corr_from_R(centre_slice(R, HALF), mu)
    A2g, A2l = local_vs_global(per, mu, HALF, m=2)
    A4g, _ = local_vs_global(per, mu, HALF, m=4)
    coh_l, coh_g = structure_tensor_coherence(movie, RF)
    eig = eigen_report(R, mu, RF, centred=False)
    eig_c = eigen_report(R, mu, RF, centred=True)
    fs = front_stats(movie)
    return {
        "arm": label,
        "density": mu,
        "A2_global": A2g, "A2_perframe": A2l, "A4_global": A4g,
        "coh_local_RF": coh_l, "coh_global": coh_g,
        "A2_ring1": anisotropy(rho, HALF, 2, ring=1),
        "A2_ring2": anisotropy(rho, HALF, 2, ring=2),
        "A2_ring3": anisotropy(rho, HALF, 2, ring=3),
        "M_lambda1": eig["lambda1"], "M_degeneracy": eig["degeneracy_l1_over_l2"],
        "M_leading_OI": eig["leading_OI"], "M_leading_DC": eig["leading_DC"],
        "M_var_explained_1": eig["var_explained_1"],
        "Sigma_degeneracy": eig_c["degeneracy_l1_over_l2"],
        "Sigma_leading_OI": eig_c["leading_OI"],
        "Sigma_leading_DC": eig_c["leading_DC"],
        "front": fs,
        "radial_rho": radial_profile(rho, HALF),
        "corr_length": corr_length(rho, HALF),
        "leading_vec": eig["leading_vec"],
        "Sigma_leading_vec": eig_c["leading_vec"],
        "M_eigenvalues": eig["eigenvalues"],
        "Sigma_eigenvalues": eig_c["eigenvalues"],
    }


def analytic_white_noise_check(p, rf=RF):
    """THE EIGEN-INSTRUMENT AGAINST ARITHMETIC, not against my expectations.

    For iid Bernoulli(p), M = E[xx^T] = p^2 * 11^T + p(1-p) * I exactly. So
        lambda_1 = p^2 * rf^2 + p(1-p)   (the DC mode, eigenvector = constant)
        lambda_k = p(1-p)                (k >= 2, degenerate)
    A closed form the code cannot fit. If `eigen_report` disagrees with this,
    the eigen path is wrong and every eigenvalue in this rung is worthless.
    """
    n = rf * rf
    M = p * p * np.ones((n, n)) + p * (1 - p) * np.eye(n)
    lam = np.sort(np.linalg.eigvalsh(M))[::-1]
    return {"predicted_l1": p * p * n + p * (1 - p),
            "predicted_l2": p * (1 - p),
            "measured_l1": float(lam[0]), "measured_l2": float(lam[1])}


def main():
    print(provenance_line())
    rng = np.random.default_rng(0)      # burned seed
    out = []

    # ---- the WAVES themselves, on burned seeds 0-2 (calibration only) -------
    for seed in (0, 1, 2):
        w = make_world(seed, H, W)
        b = record_bursting(w, steps=STEPS, burn_in=BURN_IN)
        x = window_movie(b, WINDOW)
        out.append(analyse(x, f"waves_seed{seed}"))

    p = float(np.mean([o["density"] for o in out]))   # MATCH the controls' density
    print(f"# matched density p = {p:.6f} (from the waves themselves)")

    rl = float(np.mean([o["corr_length"] for o in out]))
    print(f"# waves' own half-height correlation length = {rl:.2f} cells "
          f"-> the disk control's radius")

    T = out[0]["front"]["n_frames"]
    # ---- GATE 1: the isotropic floor ---------------------------------------
    # THE REAL FLOOR: isotropic AND correlated. Radius from the waves' own
    # measured correlation length (above), not chosen.
    out.append(analyse(disk_movie(rng, T, H, W, p, rl), "CONTROL_disks_ISO_FLOOR"))
    # OUT-OF-DOMAIN, reported not hidden: rho ~= 0 everywhere, so A_m is a
    # ratio of noise to noise and reads ~0.5, NOT ~0. Keeps the defect visible.
    out.append(analyse(white_noise_movie(rng, T, H, W, p), "CONTROL_white_noise_OOD"))
    # ---- GATE 2: the anisotropic ideal -------------------------------------
    out.append(analyse(bar_movie(rng, T, H, W, p, theta_fixed=0.0), "CONTROL_bars_fixed_0"))
    out.append(analyse(bar_movie(rng, T, H, W, p, theta_fixed=np.pi / 4), "CONTROL_bars_fixed_45"))
    # ---- GATE 3: THE DISCRIMINATOR -----------------------------------------
    out.append(analyse(bar_movie(rng, T, H, W, p, theta_fixed=None), "CONTROL_bars_random_theta"))

    for o in out:
        print(f"{o['arm']:28s} dens={o['density']:.4f} "
              f"A2g={o['A2_global']:.4f} A2pf={o['A2_perframe']:.4f} "
              f"cohL={o['coh_local_RF']:.4f} cohG={o['coh_global']:.4f} A4g={o['A4_global']:.4f} "
              f"M_OI={o['M_leading_OI']:.4f} M_DC={o['M_leading_DC']:.4f} "
              f"M_deg={o['M_degeneracy']:.3f} Sig_OI={o['Sigma_leading_OI']:.4f} "
              f"dead={o['front']['frames_dead']} nb={o['front']['neighbours_mean']:.2f}")

    ac = analytic_white_noise_check(p)
    print(f"# ANALYTIC eigen-check (iid Bernoulli p={p:.4f}): "
          f"predicted l1={ac['predicted_l1']:.6f} measured l1={ac['measured_l1']:.6f} | "
          f"predicted l2={ac['predicted_l2']:.6f} measured l2={ac['measured_l2']:.6f}")

    with open("results/waveiso_calibrate.json", "w") as fh:
        json.dump({"provenance": provenance_line(), "arms": out,
                   "analytic_check": ac}, fh, indent=1)


if __name__ == "__main__":
    main()
