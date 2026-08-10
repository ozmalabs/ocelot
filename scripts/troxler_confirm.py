#!/usr/bin/env python
"""TROXLER — the PRE-REGISTERED CONFIRMATORY RUN.

Runs EXACTLY the test declared in `VISION_TROXLER_PREREG.md`, which was committed
BEFORE this script was ever executed (PROTOCOL §3; the commit timestamp is the gate).

  n = 8, fixed in advance by the pilot on already-burned seeds 0-5.
  Seeds 15000-15007 — declared in advance, never used for anything.
  Statistic: exact two-sided SIGN TEST on the paired per-seed difference
             contrast_final(DRIFT) - contrast_final(STABILISED).
  PASS is CONJUNCTIVE (§4): p<0.01 AND arm B alive_min>0.99 AND arm B
             max_stab_err==0 AND arm A alive_min>0 at every timepoint.

No sweeps. No re-runs. A further attempt needs a NEW pre-registration.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from math import comb

import numpy as np
from domains import engine_provenance as ep
ep.engine_preamble()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import troxler_lib as T  # noqa: E402

SEEDS = list(range(15000, 15008))    # n=8, DECLARED IN THE PRE-REG
VIS = 3200                            # §2 settle, measured in advance on seed 0


def sign_test_two_sided(diffs) -> tuple[int, int, float]:
    """Exact two-sided sign test. Zeros are dropped (they favour neither side)."""
    nz = [d for d in diffs if d != 0]
    n = len(nz)
    k = sum(1 for d in nz if d > 0)
    # two-sided: sum of probabilities of outcomes at least as extreme
    p = 0.0
    for i in range(n + 1):
        pi = comb(n, i) / (2 ** n)
        if pi <= comb(n, k) / (2 ** n) + 1e-15:
            p += pi
    return k, n, min(1.0, p)


def bootstrap_ci(d, iters=20000, seed=0):
    rng = np.random.default_rng(seed)
    d = np.asarray(d, float)
    bs = rng.choice(d, size=(iters, len(d)), replace=True).mean(axis=1)
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def main():
    print(ep.provenance_line())
    print("TROXLER CONFIRMATORY RUN — VISION_TROXLER_PREREG.md")
    print(f"seeds {SEEDS[0]}-{SEEDS[-1]} (n={len(SEEDS)}), VIS_STEPS={VIS}, "
          f"CALIB_STEPS={T.CALIB_STEPS}\n")

    rows = []
    for seed in SEEDS:
        a = T.run_arm(seed, T.ARM_DRIFT, vis_steps=VIS)
        b = T.run_arm(seed, T.ARM_STABILISED, vis_steps=VIS)
        row = {
            "seed": seed,
            "mu_endo": a["mu_endo"],
            "drift_contrast_final": a["contrast_final"],
            "stab_contrast_final": b["contrast_final"],
            "diff": a["contrast_final"] - b["contrast_final"],
            "drift_contrast_t0": a["contrast_t0"],
            "stab_contrast_t0": b["contrast_t0"],
            "drift_alive_min": float(a["alive"].min()),
            "stab_alive_min": float(b["alive"].min()),
            "drift_alive_final": a["alive_final"],
            "stab_alive_final": b["alive_final"],
            "stab_max_err": b["max_stab_err"],
            "drift_max_err": a["max_stab_err"],
            "stab_mean_resp_final": b["mean_resp_final"],
            # BOTH arms' gaze, recorded separately. The FIRST run of this script
            # printed arm A's `gaze_distinct` under the label "arm B gaze still
            # moving" — the claim was TRUE (verified two ways: the arms' gaze
            # trajectories are byte-identical, and NO `ey_saw_*` rule reads
            # lum/resp/x/theta, so the walk is blind to the image) but the FIELD
            # was arm A's. A claim about arm B must be read off arm B.
            "drift_gaze_distinct": a["gaze_distinct"],
            "stab_gaze_distinct": b["gaze_distinct"],
            "stab_gaze_path_len": b["gaze_path_len"],
        }
        rows.append(row)
        print(f"seed {seed}: drift={row['drift_contrast_final']:.6f} "
              f"stab={row['stab_contrast_final']:.6f} diff={row['diff']:+.6f} | "
              f"alive_min A={row['drift_alive_min']:.3f} B={row['stab_alive_min']:.3f} | "
              f"stab_err={row['stab_max_err']:.1e} | mu={row['mu_endo']:.6f}")

    d = np.array([r["diff"] for r in rows])
    A = np.array([r["drift_contrast_final"] for r in rows])
    B = np.array([r["stab_contrast_final"] for r in rows])
    k, n, p = sign_test_two_sided(d)
    lo, hi = bootstrap_ci(d)

    print("\n" + "=" * 78)
    print("PRIMARY — exact two-sided SIGN TEST on paired diff (DRIFT - STABILISED)")
    print(f"  drift      mean={A.mean():.6f}  sd={A.std(ddof=1):.6f}")
    print(f"  stabilised mean={B.mean():.6f}  sd={B.std(ddof=1):.6f}")
    print(f"  paired diff mean={d.mean():.6f}  95% bootstrap CI [{lo:.6f}, {hi:.6f}]")
    print(f"  positive: {k}/{n}   exact two-sided p = {p:.6f}")

    print("\n§1 CLAUSE 4 — ALIVENESS PER ARM (a silent arm is a FAILED GATE)")
    print(f"  drift      alive_min over seeds: {min(r['drift_alive_min'] for r in rows):.4f}")
    print(f"  stabilised alive_min over seeds: {min(r['stab_alive_min'] for r in rows):.4f}")
    print(f"  stabilised alive_final: {min(r['stab_alive_final'] for r in rows):.4f}")
    print(f"  stabilised mean_resp(final) vs mu_endo: "
          f"{np.mean([r['stab_mean_resp_final'] for r in rows]):.6f} vs "
          f"{np.mean([r['mu_endo'] for r in rows]):.6f}")

    print("\nMIRROR CHECK — arm B must have stabilised EXACTLY")
    print(f"  max stab_err over seeds: {max(r['stab_max_err'] for r in rows):.6e}")
    print(f"  (arm A's image DOES move: max {max(r['drift_max_err'] for r in rows):.6e})")
    print("\nDITCHBURN, NOT PARALYSIS — arm B's EYE must still be MOVING, read off ARM B")
    print(f"  arm B gaze distinct cells (min over seeds): "
          f"{min(r['stab_gaze_distinct'] for r in rows)}")
    print(f"  arm B gaze path length    (min over seeds): "
          f"{min(r['stab_gaze_path_len'] for r in rows):.1f}")
    print(f"  arm A gaze distinct cells (min over seeds): "
          f"{min(r['drift_gaze_distinct'] for r in rows)}  "
          f"(identical to B: the walk is blind to the image)")

    crit = {
        "p<0.01": p < 0.01,
        "B alive_min>0.99": min(r["stab_alive_min"] for r in rows) > 0.99,
        "B stab_err==0": max(r["stab_max_err"] for r in rows) == 0.0,
        "A alive_min>0": min(r["drift_alive_min"] for r in rows) > 0.0,
    }
    print("\nDECISION RULE (CONJUNCTIVE — §4)")
    for kk, vv in crit.items():
        print(f"  {kk:20s} {vv}")
    verdict = all(crit.values())
    print(f"\n  VERDICT: {'H1 — the stabilised image FADES; the drifting one does NOT' if verdict else 'NULL / FAILED GATE'}")

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "troxler_confirm.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({"engine": ep.provenance_line(), "seeds": SEEDS, "vis_steps": VIS,
                   "rows": rows, "sign_k": k, "sign_n": n, "p": p,
                   "diff_mean": float(d.mean()), "ci": [lo, hi],
                   "criteria": crit, "verdict": bool(verdict)}, f, indent=1)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
