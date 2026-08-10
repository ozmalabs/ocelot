"""ETA-SWEEP — THE CONFIRMATORY RUN. Pre-registered in
`VISION_ETA_SWEEP_PREREG.md`, COMMITTED BEFORE THIS RUNS.

**CONFIRMATORY. Seeds 24000..24000+N-1 (N DECLARED IN THE PREREG), never used
for anything (12000-23999 UNTOUCHED). Runs EXACTLY the pre-registered arms.**

The 8D 2x2, WITH the settling loop terminating via cycle detection:
  (a) CONVERGENCE (§2): drift(t) = ||w(t)-w(t-D)||/||w(t)|| -> 0 over TRAIN steps
  (b) LOAD-BEARING: Delta_OSI = OSI(trained) - OSI(untrained_floor) > SESOI,
                    paired per seed, cells alive (n_dead == 0)
  (c) MAP STRUCTURE: per-cell preferred orientation — spatial organisation
                    (neighbour similarity) and across-seed reproducibility (R),
                    each vs its PERMUTATION null. A coin flip => obs ~ null.

USAGE
-----
  # shardable across cores — each shard is an INDEPENDENT process (own graphs,
  # own RNG per seed; no shared mutable state, PROTOCOL §11):
  python eta_sweep_confirm.py --lo 24000 --hi 24006      # runs seeds [lo,hi)
  ...
  python eta_sweep_confirm.py --merge results/eta_sweep_confirm_shard_*.json

Floors measured IN-RUN, per seed. `peak/base` NOT read (§1.1). Engine + seeds
recorded via provenance_line (§10).
"""
from __future__ import annotations

import argparse
import glob
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

# ==== DECLARED IN THE PREREG — FROZEN BEFORE THE RUN ========================
ETA_GRID = [1e-4, 5e-4, 1e-3, 2e-3, 5e-3]           # FINALISED FROM PILOT
N = 24                                               # FINALISED FROM PILOT (power)
SEED0 = 24000
CONVERGE_RATIO = 0.5     # converged iff drift_final < CONVERGE_RATIO * drift_first
# ===========================================================================
RESDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "results")


def _seed_record(sd):
    """Every arm for one seed: the eta-independent floor + one trained arm per
    eta. Returned as plain JSON-able dicts."""
    u = arm(sd, ETA_GRID[0], trained=False)
    out = {"floor": {
        "osi_mean": u["osi_mean"], "osi": u["osi"].tolist(),
        "pref": u["pref"].tolist(), "pos": u["pos"].tolist(),
        "n_dead": u["n_dead"], "norm0": u["norm0"]}, "trained": {}}
    for eta in ETA_GRID:
        a = arm(sd, eta, trained=True)
        df, d0 = drift_final_first(a["hist"])
        out["trained"][f"{eta:.0e}"] = {
            "osi_mean": a["osi_mean"], "osi": a["osi"].tolist(),
            "pref": a["pref"].tolist(), "pos": a["pos"].tolist(),
            "n_dead": a["n_dead"], "norm0": a["norm0"], "norm1": a["norm1"],
            "rel_move": a["rel_move"], "dw": a["dw"],
            "drift_final": df, "drift_first": d0, "hist": a["hist"]}
    return out


def run_shard(lo, hi):
    seeds = list(range(lo, hi))
    print("=" * 78)
    print(f"ETA-SWEEP CONFIRMATORY SHARD seeds {lo}..{hi-1}")
    print(provenance_line())
    print(f"  eta grid {ETA_GRID}  SESOI={SESOI}")
    print("=" * 78)
    t0 = time.time()
    rec = {"provenance": provenance_line(), "eta_grid": ETA_GRID,
           "sesoi": SESOI, "converge_ratio": CONVERGE_RATIO, "seeds": {}}
    for sd in seeds:
        rec["seeds"][str(sd)] = _seed_record(sd)
        f = rec["seeds"][str(sd)]["floor"]
        print(f"  seed {sd} done: floor OSI {f['osi_mean']:.4f} dead {f['n_dead']} "
              f"({time.time()-t0:.0f}s)")
    out = os.path.join(RESDIR, f"eta_sweep_confirm_shard_{lo}_{hi}.json")
    os.makedirs(RESDIR, exist_ok=True)
    with open(out, "w") as fh:
        json.dump(rec, fh)
    print(f"\n  wrote {out}  ({time.time()-t0:.0f}s)")
    return 0


def t_ci(x):
    x = np.asarray(x, float)
    m = x.mean()
    if len(x) < 2:
        return m, m, m
    se = x.std(ddof=1) / np.sqrt(len(x))
    return m, m - 1.96 * se, m + 1.96 * se


def merge_and_analyse(shard_glob):
    files = sorted(sum((glob.glob(g) for g in shard_glob), []))
    seeds = {}
    prov = None
    for fp in files:
        d = json.load(open(fp))
        prov = prov or d["provenance"]
        seeds.update(d["seeds"])
    seed_ids = sorted(int(s) for s in seeds)
    print("=" * 78)
    print("ETA-SWEEP CONFIRMATORY — MERGED ANALYSIS")
    print(f"  {provenance_line()}")
    print(f"  seeds {seed_ids[0]}..{seed_ids[-1]} (n={len(seed_ids)})  "
          f"from {len(files)} shards")
    print("=" * 78)
    merged = {"provenance": prov, "eta_grid": ETA_GRID, "sesoi": SESOI,
              "n": len(seed_ids), "seeds": seed_ids, "converge_ratio": CONVERGE_RATIO,
              "records": seeds}
    out = os.path.join(RESDIR, "eta_sweep_confirm.json")
    with open(out, "w") as fh:
        json.dump(merged, fh)
    print(f"  wrote {out}\n")
    analyse(merged)
    return 0


def analyse(merged):
    R = merged["records"]
    seeds = [str(s) for s in merged["seeds"]]
    floor = {s: R[s]["floor"] for s in seeds}

    print("=" * 78)
    print("  THE 2x2 (per eta; unit = SEED)")
    print("=" * 78)
    print(f"  {'eta':>7} {'D_OSI':>9} {'CI_lo':>8} {'CI_hi':>8} {'relmove':>8} "
          f"{'driftF':>8} {'drift0':>8} {'conv?':>6} {'load?':>6} {'dead':>5}")
    both = []
    for eta in merged["eta_grid"]:
        k = f"{eta:.0e}"
        d = np.array([R[s]["trained"][k]["osi_mean"] - floor[s]["osi_mean"]
                      for s in seeds])
        mv = np.array([R[s]["trained"][k]["rel_move"] for s in seeds])
        dfv = np.array([R[s]["trained"][k]["drift_final"] for s in seeds])
        d0v = np.array([R[s]["trained"][k]["drift_first"] for s in seeds])
        dead = sum(R[s]["trained"][k]["n_dead"] for s in seeds) + \
            sum(floor[s]["n_dead"] for s in seeds)
        m, lo, hi = t_ci(d)
        conv = dfv.mean() < merged["converge_ratio"] * d0v.mean()
        load = (lo > SESOI) and (dead == 0)
        both.append((eta, conv and load))
        print(f"  {eta:>7.0e} {m:>+9.4f} {lo:>+8.4f} {hi:>+8.4f} {mv.mean():>8.3f} "
              f"{dfv.mean():>8.4f} {d0v.mean():>8.4f} {str(conv):>6} {str(load):>6} "
              f"{dead:>5d}")

    # THE UNTRAINED FLOOR IS THE STRUCTURE CONTROL (pilot finding): the probe's
    # argmax-tie aliasing (8D §4) makes position -> preferred angle reproducible
    # ACROSS SEEDS *without any learning*, so a pool-shuffle null is FOOLED
    # (untrained R ~ 0.55 >> pool-null 0.42). The honest test is whether TRAINING
    # exceeds the FLOOR: Δ vs the untrained arm, paired per seed.
    pos = np.array(R[seeds[0]]["floor"]["pos"])
    fpref = np.array([R[s]["floor"]["pref"] for s in seeds])
    rng = np.random.default_rng(777)
    f_nsim = np.array([neighbour_similarity(np.array(R[s]["floor"]["pref"]), pos)
                       for s in seeds])
    Rf, _ = across_seed_R(fpref)
    print("\n" + "=" * 78)
    print("  MAP STRUCTURE — TRAINED vs the UNTRAINED FLOOR (the honest control)")
    print(f"  floor: across-seed R {Rf:.3f}   nsim {f_nsim.mean():+.3f}   "
          f"gbias {global_orientation_bias(fpref):.3f}   "
          f"(pool-null is FOOLED by probe aliasing — see prereg §2)")
    print("=" * 78)
    for eta in merged["eta_grid"]:
        k = f"{eta:.0e}"
        prefs = np.array([R[s]["trained"][k]["pref"] for s in seeds])
        t_nsim = np.array([neighbour_similarity(np.array(R[s]["trained"][k]["pref"]),
                                                pos) for s in seeds])
        dnn = t_nsim - f_nsim               # learning-induced spatial organisation
        _, nlo, nhi = t_ci(dnn)
        Rt, _ = across_seed_R(prefs)
        Rm, Rs = across_seed_R_null(prefs, n_perm=2000, rng=rng)
        gbias = global_orientation_bias(prefs)
        # STRUCTURED only if TRAINING adds structure over the untrained floor
        struct = (nlo > 0) or (Rt > Rf + 0.10)
        print(f"  eta {eta:.0e}: nsim(tr-fl) {dnn.mean():+.3f} CI[{nlo:+.3f},{nhi:+.3f}] "
              f"| R tr {Rt:.3f} vs floor {Rf:.3f} (pool-null {Rm:.3f}+/-{Rs:.3f}) "
              f"| gbias {gbias:.3f} | {'STRUCTURED' if struct else 'coin-flip'}")

    print("\n" + "=" * 78)
    print("  VERDICT")
    print("=" * 78)
    winners = [e for e, b in both if b]
    if not winners:
        print("  NO eta is BOTH convergent AND load-bearing. The 2x2 is EMPTY.")
        print("  => 8D's tension SURVIVES the settling loop. NEGATIVE (§7).")
    else:
        print(f"  eta(s) BOTH convergent AND load-bearing: {winners}")
        print("  => read MAP STRUCTURE: coin-flip = degeneracy realised (NOT a")
        print("     map); STRUCTURED = a working V1 (ENGINEERING, not paradigm).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo", type=int)
    ap.add_argument("--hi", type=int)
    ap.add_argument("--merge", nargs="+")
    a = ap.parse_args()
    if a.merge:
        return merge_and_analyse(a.merge)
    lo = a.lo if a.lo is not None else SEED0
    hi = a.hi if a.hi is not None else SEED0 + N
    return run_shard(lo, hi)


if __name__ == "__main__":
    sys.exit(main())
