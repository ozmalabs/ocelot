"""waveiso_confirm — the pre-registered confirmatory run. Seeds 20000-20015.

Runs EXACTLY the tests listed in `VISION_WAVEISO_PREREG.md`. No sweeps, no
re-runs. The controls are re-measured here on a burned RNG so every number in the
results file comes from ONE process and ONE engine.

Measures the STIMULUS. No cortex, no learning rule, no probe, no arm.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# waveiso_lib calls engine_preamble() at import, BEFORE any domains.* import
# (§10.1 rule 3): the FIRST substrate_rs import binds the engine for the
# process, so a preamble that runs afterwards is a no-op that LOOKS correct.
from scripts.waveiso_lib import (anisotropy, bar_movie, centre_slice,
                                 corr_from_R, corr_length, disk_movie,
                                 eigen_report, front_stats, local_vs_global,
                                 make_world, movie_autocorr, provenance_line,
                                 radial_profile, record_bursting,
                                 structure_tensor_coherence, white_noise_movie,
                                 window_movie)

import numpy as np

HALF, RF, RMAX = 3, 7, 6
WINDOW = 2                       # WaveParams.window_steps — READ, not chosen
H = W = 64
STEPS, BURN_IN = 200, 20
SEEDS = list(range(20000, 20016))          # n=16, fixed in advance (§3.3)


def analyse(movie, label, *, raw=None):
    R, per, mu = movie_autocorr(movie, RMAX)
    rho = corr_from_R(centre_slice(R, HALF), mu)
    A2g, A2pf = local_vs_global(per, mu, HALF, m=2)
    cohL, cohG = structure_tensor_coherence(movie, RF)
    eig = eigen_report(R, mu, RF, centred=False)
    eigc = eigen_report(R, mu, RF, centred=True)
    lam, lamc = eig["eigenvalues"], eigc["eigenvalues"]
    fs = front_stats(movie)
    row = {
        "arm": label, "density": mu,
        "A2_global": A2g, "A2_perframe": A2pf,
        "A4_global": anisotropy(rho, HALF, 4),
        "A2_ring1": anisotropy(rho, HALF, 2, ring=1),
        "A2_ring2": anisotropy(rho, HALF, 2, ring=2),
        "A2_ring3": anisotropy(rho, HALF, 2, ring=3),
        "coh_local_RF": cohL, "coh_global": cohG,
        "M_eigenvalues": lam,
        "M_leading_OI": eig["leading_OI"], "M_leading_DC": eig["leading_DC"],
        "M_l1_over_l2": eig["degeneracy_l1_over_l2"],
        "M_l2_over_l3": float(lam[1] / lam[2]) if abs(lam[2]) > 1e-12 else float("inf"),
        "M_var_explained_1": eig["var_explained_1"],
        "Sigma_eigenvalues": lamc,
        "Sigma_leading_OI": eigc["leading_OI"],
        "Sigma_leading_DC": eigc["leading_DC"],
        "Sigma_l1_over_l2": eigc["degeneracy_l1_over_l2"],
        "Sigma_l2_over_l3": float(lamc[1] / lamc[2]) if abs(lamc[2]) > 1e-12 else float("inf"),
        "radial_rho": radial_profile(rho, HALF),
        "corr_length": corr_length(rho, HALF),
        "front_windowed": fs,
        "frames_dead": fs["frames_dead"],
        # the eigenvectors, so the leading one can be RENDERED
        "M_leading_vec": eig["leading_vec"],
        "Sigma_leading_vec": eigc["leading_vec"],
        "M_eigvec_OI_top6": eig["eigvec_OI_top6"],
        "M_eigvec_DC_top6": eig["eigvec_DC_top6"],
    }
    if raw is not None:
        row["front_raw"] = front_stats(raw)
    return row


def ci95(v):
    v = np.asarray(v, float)
    n = len(v)
    m = v.mean()
    if n < 2:
        return m, float("nan"), float("nan")
    se = v.std(ddof=1) / np.sqrt(n)
    # t_{0.975, 15} = 2.131 for n=16
    from math import inf
    tcrit = {15: 2.131}.get(n - 1, 1.96)
    return m, m - tcrit * se, m + tcrit * se


def main():
    prov = provenance_line()
    print(prov)
    out = {"provenance": prov, "seeds": SEEDS, "waves": [], "controls": [],
           "descriptives": {}}

    # ---- THE CONFIRMATORY ARM: fresh seeds 20000-20015 ---------------------
    for seed in SEEDS:
        w = make_world(seed, H, W)
        b = record_bursting(w, steps=STEPS, burn_in=BURN_IN)
        x = window_movie(b, WINDOW)
        out["waves"].append(analyse(x, f"waves_seed{seed}", raw=b))
        print(f"  seed {seed}: dens={out['waves'][-1]['density']:.4f} "
              f"cohL={out['waves'][-1]['coh_local_RF']:.4f} "
              f"cohG={out['waves'][-1]['coh_global']:.4f} "
              f"M_OI={out['waves'][-1]['M_leading_OI']:.4f} "
              f"M_DC={out['waves'][-1]['M_leading_DC']:.4f}")

    p = float(np.mean([r["density"] for r in out["waves"]]))
    rl = float(np.mean([r["corr_length"] for r in out["waves"]]))
    T = out["waves"][0]["front_windowed"]["n_frames"]
    print(f"# matched density p={p:.6f}; waves' own corr length={rl:.2f} cells")

    # ---- THE CONTROLS (§5), on a BURNED rng --------------------------------
    rng = np.random.default_rng(0)
    out["controls"].append(analyse(disk_movie(rng, T, H, W, p, rl),
                                   "CONTROL_disks_ISO_FLOOR"))
    out["controls"].append(analyse(white_noise_movie(rng, T, H, W, p),
                                   "CONTROL_white_noise_OOD"))
    out["controls"].append(analyse(bar_movie(rng, T, H, W, p, theta_fixed=0.0),
                                   "CONTROL_bars_fixed_0_IDEAL"))
    out["controls"].append(analyse(bar_movie(rng, T, H, W, p, theta_fixed=np.pi / 4),
                                   "CONTROL_bars_fixed_45_IDEAL"))
    out["controls"].append(analyse(bar_movie(rng, T, H, W, p, theta_fixed=None),
                                   "CONTROL_bars_random_theta_DISCRIMINATOR"))

    # ---- DECLARED SECONDARY DESCRIPTIVES -----------------------------------
    # (a) window=0 — is the DC dominance an artifact of the OR-window? Declared
    #     in the prereg's provisos, reported whatever it shows.
    w0 = make_world(SEEDS[0], H, W)
    b0 = record_bursting(w0, steps=STEPS, burn_in=BURN_IN)
    out["descriptives"]["window0"] = analyse(window_movie(b0, 0),
                                             "waves_window0_DESCRIPTIVE", raw=b0)
    # (b) 128x128 — is 64 too small for translation invariance? Declared in §2.1.
    w2 = make_world(SEEDS[0], 128, 128)
    b2 = record_bursting(w2, steps=STEPS, burn_in=BURN_IN)
    out["descriptives"]["grid128"] = analyse(window_movie(b2, WINDOW),
                                            "waves_128_DESCRIPTIVE", raw=b2)

    # ---- the read-out ------------------------------------------------------
    print(f"\n{'statistic':22s} {'mean':>9s} {'CI95_lo':>9s} {'CI95_hi':>9s}"
          f" | {'FLOOR':>9s} {'IDEAL':>9s} {'DISCRIM':>9s}")
    floor = out["controls"][0]
    ideal = out["controls"][2]
    disc = out["controls"][4]
    summary = {}
    for k in ("density", "A2_global", "A2_perframe", "A4_global",
              "coh_local_RF", "coh_global", "M_leading_OI", "M_leading_DC",
              "M_l1_over_l2", "M_l2_over_l3", "M_var_explained_1",
              "Sigma_leading_OI", "Sigma_leading_DC", "Sigma_l1_over_l2",
              "Sigma_l2_over_l3", "frames_dead"):
        v = [r[k] for r in out["waves"]]
        m, lo, hi = ci95(v)
        summary[k] = {"mean": m, "ci_lo": lo, "ci_hi": hi,
                      "floor_disks": floor[k], "ideal_bars": ideal[k],
                      "discriminator_bars_random": disc[k]}
        print(f"{k:22s} {m:9.4f} {lo:9.4f} {hi:9.4f} | "
              f"{floor[k]:9.4f} {ideal[k]:9.4f} {disc[k]:9.4f}")
    out["summary"] = summary

    print(f"\nfront_nb_raw (waves)   "
          f"{np.mean([r['front_raw']['neighbours_mean'] for r in out['waves']]):.4f}"
          f"   (thin curve ~2, solid blob ~4, scatter ~0)")
    print(f"window0 DESCRIPTIVE: M_DC={out['descriptives']['window0']['M_leading_DC']:.4f} "
          f"M_OI={out['descriptives']['window0']['M_leading_OI']:.4f} "
          f"cohL={out['descriptives']['window0']['coh_local_RF']:.4f} "
          f"dens={out['descriptives']['window0']['density']:.4f}")
    print(f"grid128 DESCRIPTIVE: M_DC={out['descriptives']['grid128']['M_leading_DC']:.4f} "
          f"M_OI={out['descriptives']['grid128']['M_leading_OI']:.4f} "
          f"cohL={out['descriptives']['grid128']['coh_local_RF']:.4f} "
          f"cohG={out['descriptives']['grid128']['coh_global']:.4f}")

    with open("results/waveiso_confirm.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote results/waveiso_confirm.json")


if __name__ == "__main__":
    main()
