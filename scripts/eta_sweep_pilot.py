"""ETA-SWEEP PILOT — burned seeds ONLY (0-7, 8D/8E's pilot block). NO hypothesis
is tested; NO confirmatory seed (24000-24999) is touched. PROTOCOL §3.3.

Fixes, IN ADVANCE of the confirmatory pre-registration:
  1. the eta GRID (which eta span the vacuous -> load-bearing -> runaway range);
  2. n, by a power analysis on sd(Delta_OSI) — the paired OSI lift;
  3. the CONVERGENCE picture per eta (drift_final vs drift_first, ||w|| move);
  4. the MAP-STRUCTURE nulls (neighbour-similarity + across-seed R vs permutation)
     so the confirmatory statistic and its null are declared, not chosen after.

Writes results/eta_sweep_pilot.json (raw, for analysis) and prints a summary.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.engine_provenance import provenance_line  # noqa: E402
from scripts.eta_sweep_lib import (  # noqa: E402
    SESOI, across_seed_R, across_seed_R_null, arm, drift_final_first,
    global_orientation_bias, neighbour_similarity, neighbour_similarity_null,
)

PILOT_SEEDS = list(range(8))                 # 0-7: ALREADY BURNED (8E's block)
ETA_GRID = [5e-4, 1e-3, 2e-3, 5e-3]          # spans the pilot's known drift range
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "eta_sweep_pilot.json")


def main() -> int:
    print("=" * 78)
    print("ETA-SWEEP PILOT — burned seeds 0-7. NO hypothesis. 24000+ UNTOUCHED.")
    print(provenance_line())
    print(f"  eta grid: {ETA_GRID}  SESOI={SESOI}")
    print("=" * 78)
    t0 = time.time()

    # untrained arm is eta-INDEPENDENT (the in-run OSI floor) — one per seed
    untr = {}
    for sd in PILOT_SEEDS:
        a = arm(sd, ETA_GRID[0], trained=False)
        untr[sd] = a
        print(f"  [floor] seed {sd}: OSI {a['osi_mean']:.4f}  dead {a['n_dead']} "
              f"|w|={a['norm0']:.3f}  ({time.time()-t0:.0f}s)")

    rec = {"provenance": provenance_line(), "seeds": PILOT_SEEDS,
           "eta_grid": ETA_GRID, "sesoi": SESOI, "floor": {}, "trained": {}}
    for sd in PILOT_SEEDS:
        u = untr[sd]
        rec["floor"][str(sd)] = {
            "osi_mean": u["osi_mean"], "osi": u["osi"].tolist(),
            "pref": u["pref"].tolist(), "pos": u["pos"].tolist(),
            "n_dead": u["n_dead"], "norm0": u["norm0"]}

    for eta in ETA_GRID:
        rec["trained"][f"{eta:.0e}"] = {}
        for sd in PILOT_SEEDS:
            a = arm(sd, eta, trained=True)
            df, d0 = drift_final_first(a["hist"])
            rec["trained"][f"{eta:.0e}"][str(sd)] = {
                "osi_mean": a["osi_mean"], "osi": a["osi"].tolist(),
                "pref": a["pref"].tolist(), "pos": a["pos"].tolist(),
                "n_dead": a["n_dead"], "norm0": a["norm0"], "norm1": a["norm1"],
                "rel_move": a["rel_move"], "dw": a["dw"],
                "drift_final": df, "drift_first": d0, "hist": a["hist"]}
            print(f"  eta {eta:.0e} seed {sd}: OSI {a['osi_mean']:.4f} "
                  f"(D {a['osi_mean']-u['osi_mean']:+.4f})  |w| {a['norm0']:.2f}->"
                  f"{a['norm1']:.2f} (move {a['rel_move']:.3f})  "
                  f"drift {d0:.4f}->{df:.4f}  dead {a['n_dead']}  "
                  f"({time.time()-t0:.0f}s)")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(rec, f)
    print(f"\n  wrote {OUT}")

    # ----- SUMMARY: the 2x2, power, and the map-structure nulls -----
    print("\n" + "=" * 78)
    print("  THE 2x2 (per eta; unit = SEED, §4)")
    print("=" * 78)
    print(f"  {'eta':>7} {'D_OSI':>9} {'sd':>7} {'n@80%':>6} {'relmove':>8} "
          f"{'driftF':>8} {'drift0':>8} {'dead':>5}")
    for eta in ETA_GRID:
        T = rec["trained"][f"{eta:.0e}"]
        d = np.array([T[str(s)]["osi_mean"] - untr[s]["osi_mean"]
                      for s in PILOT_SEEDS])
        mv = np.array([T[str(s)]["rel_move"] for s in PILOT_SEEDS])
        dfv = np.array([T[str(s)]["drift_final"] for s in PILOT_SEEDS])
        d0v = np.array([T[str(s)]["drift_first"] for s in PILOT_SEEDS])
        dead = sum(T[str(s)]["n_dead"] for s in PILOT_SEEDS)
        sd_d = float(d.std(ddof=1))
        n_need = int(np.ceil((2.8 * sd_d / SESOI) ** 2)) if sd_d > 0 else 3
        print(f"  {eta:>7.0e} {d.mean():>+9.4f} {sd_d:>7.4f} {n_need:>6d} "
              f"{mv.mean():>8.3f} {dfv.mean():>8.4f} {d0v.mean():>8.4f} {dead:>5d}")

    print("\n" + "=" * 78)
    print("  MAP STRUCTURE (trained pool; observed vs PERMUTATION null)")
    print("=" * 78)
    for eta in ETA_GRID:
        T = rec["trained"][f"{eta:.0e}"]
        prefs = np.array([T[str(s)]["pref"] for s in PILOT_SEEDS])
        pos = np.array(T[str(PILOT_SEEDS[0])]["pos"])
        rng = np.random.default_rng(12345)
        # spatial (per-seed, paired vs its own permutation null)
        nn_obs, nn_null = [], []
        for s in PILOT_SEEDS:
            p = np.array(T[str(s)]["pref"])
            nn_obs.append(neighbour_similarity(p, pos))
            m, _ = neighbour_similarity_null(p, pos, n_perm=200, rng=rng)
            nn_null.append(m)
        nn_obs = np.array(nn_obs); nn_null = np.array(nn_null)
        Robs, _ = across_seed_R(prefs)
        Rnull_m, Rnull_s = across_seed_R_null(prefs, n_perm=1000, rng=rng)
        gbias = global_orientation_bias(prefs)
        print(f"  eta {eta:.0e}: neighbour-sim obs {nn_obs.mean():+.3f} "
              f"null {nn_null.mean():+.3f} (D {(nn_obs-nn_null).mean():+.3f}, "
              f"sd {(nn_obs-nn_null).std(ddof=1):.3f})  |  across-seed R "
              f"{Robs:.3f} vs null {Rnull_m:.3f}+/-{Rnull_s:.3f}  |  "
              f"global-bias {gbias:.3f}")

    print(f"\n  TOTAL {time.time()-t0:.0f}s")
    print("""
  READING (fixed in advance):
    * The 2x2 is EMPTY if no eta has BOTH driftF -> 0 (converged) AND
      D_OSI > SESOI with cells alive (load-bearing). That is 8D's claim,
      now WITH settling — the predicted NEGATIVE.
    * If some eta is BOTH: check MAP STRUCTURE. neighbour-sim ~ null AND
      across-seed R ~ null => the orientation is a COIN FLIP (the eigenspectrum
      degeneracy realised) — NOT a working map. obs >> null on either =>
      a structured map (engineering, not paradigm).""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
