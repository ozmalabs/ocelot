"""Confirmatory experiments for SEIZURE MODEL V2 (see SEIZURE_MODEL_V2_PREREG.md).

Two re-tests of the V1 limits, on the REAL engine (the recruitment term lives in
the `sz_settle_next_residual` DSL rule; the harness is a world adapter only):

  V2-P4  excitatory-recruitment coupling g_rec -> PRO-ICTAL (give* RISES with g_rec)
  V2-P5  heterogeneous-degree HUBS -> preferred onset locus (give* higher at a hub)

give* := largest give in the grid at which the seizure persists (persists =
mean final-60-substep n_active > 5.0), the V1 metric. Writes results/seizure_v2.json.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.seizure_engine_lattice as M

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "seizure_v2.json")

P4_GREC = [0.0, 0.025, 0.05, 0.1, 0.2, 0.4]
P4_GIVE = [1.0, 0.9, 0.8, 0.7, 0.65, 0.6, 0.575, 0.5375, 0.5, 0.45]
P4_SEEDS = [5, 6, 7]

P5_GIVE = [0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65]
P5_SEEDS = [5, 6, 7, 8, 9]
P5_GREC = 0.1
P5_HUB_K = 16
CORNER_A = (10, 10)   # dist 14.14 from center (20,20)
CORNER_B = (30, 30)   # dist 14.14 from center


def give_star(finals, gives):
    """largest give whose run persists (final_active mean > 5)."""
    best = None
    for gv, fa in sorted(zip(gives, finals), reverse=True):
        if fa > 5.0:
            best = gv if best is None else max(best, gv)
    return best


def run_p4():
    a = M.Arch()
    rows = []
    for grec in P4_GREC:
        for seed in P4_SEEDS:
            finals = []
            for gv in P4_GIVE:
                r = M.run_one(a, D=3.0, give=gv, alpha=0.5, seed=seed, g_rec=grec)
                finals.append(M.classify(r, a)["final_active"])
            gs = give_star(finals, P4_GIVE)
            rows.append({"g_rec": grec, "seed": seed, "give_star": gs,
                         "finals": dict(zip(map(str, P4_GIVE), finals))})
            print(f"[P4] g_rec={grec:<5} seed={seed} give*={gs}")
    # aggregate: median give* per g_rec (give*>=1.0 saturation reported as 1.0)
    agg = {}
    for grec in P4_GREC:
        gss = [x["give_star"] for x in rows if x["g_rec"] == grec]
        gss = [1.0 if (g is not None and g >= 1.0) else g for g in gss]
        agg[str(grec)] = {"give_star_per_seed": gss,
                          "median": float(np.median([g for g in gss if g is not None]))
                          if any(g is not None for g in gss) else None}
    return {"rows": rows, "give_star_by_grec": agg,
            "grid": {"g_rec": P4_GREC, "give": P4_GIVE, "seeds": P4_SEEDS}}


def run_p5():
    a = M.Arch()
    rows = []
    # two configs: hub at corner A (onset A=hub vs B=nonhub), and hub at corner B.
    for hub_corner, other in ((CORNER_A, CORNER_B), (CORNER_B, CORNER_A)):
        for seed in P5_SEEDS:
            for locus_name, locus in (("hub", hub_corner), ("nonhub", other)):
                finals = []
                for gv in P5_GIVE:
                    r = M.run_one(a, D=3.0, give=gv, alpha=0.5, seed=seed,
                                  g_rec=P5_GREC, hubs=[hub_corner], hub_k=P5_HUB_K,
                                  onset_rc=locus, r_onset=1.0)
                    finals.append(M.classify(r, a)["final_active"])
                gs = give_star(finals, P5_GIVE)
                rows.append({"hub_corner": hub_corner, "onset": locus_name,
                             "seed": seed, "give_star": gs,
                             "finals": dict(zip(map(str, P5_GIVE), finals))})
                print(f"[P5] hub@{hub_corner} onset={locus_name:<6} seed={seed} give*={gs}")
    # homogeneous control (no hubs) at each corner
    homog = []
    for corner in (CORNER_A, CORNER_B):
        for seed in P5_SEEDS:
            finals = []
            for gv in P5_GIVE:
                r = M.run_one(a, D=3.0, give=gv, alpha=0.5, seed=seed,
                              g_rec=P5_GREC, hubs=None, hub_k=0,
                              onset_rc=corner, r_onset=1.0)
                finals.append(M.classify(r, a)["final_active"])
            gs = give_star(finals, P5_GIVE)
            homog.append({"corner": corner, "seed": seed, "give_star": gs})
            print(f"[P5] HOMOG   corner={corner} seed={seed} give*={gs}")

    def med(sel):
        gss = [x["give_star"] for x in rows if sel(x)]
        gss = [g for g in gss if g is not None]
        return float(np.median(gss)) if gss else None
    agg = {
        "hub_onset_median_give_star": med(lambda x: x["onset"] == "hub"),
        "nonhub_onset_median_give_star": med(lambda x: x["onset"] == "nonhub"),
        "homog_median_give_star": (
            float(np.median([x["give_star"] for x in homog if x["give_star"] is not None]))
            if any(x["give_star"] is not None for x in homog) else None),
        "paired_hub_minus_nonhub": None,
    }
    # paired per (hub_corner, seed): give*(hub onset) - give*(nonhub onset)
    diffs = []
    for hc, _ in ((CORNER_A, CORNER_B), (CORNER_B, CORNER_A)):
        for seed in P5_SEEDS:
            h = next((x["give_star"] for x in rows
                      if x["hub_corner"] == hc and x["onset"] == "hub" and x["seed"] == seed), None)
            n = next((x["give_star"] for x in rows
                      if x["hub_corner"] == hc and x["onset"] == "nonhub" and x["seed"] == seed), None)
            if h is not None and n is not None:
                diffs.append(h - n)
    agg["paired_hub_minus_nonhub"] = {
        "diffs": diffs,
        "median": float(np.median(diffs)) if diffs else None,
        "n_positive": int(sum(d > 0 for d in diffs)),
        "n_total": len(diffs),
    }
    return {"rows": rows, "homog": homog, "agg": agg,
            "grid": {"give": P5_GIVE, "seeds": P5_SEEDS, "g_rec": P5_GREC,
                     "hub_k": P5_HUB_K, "corners": [CORNER_A, CORNER_B]}}


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    out = {}
    if os.path.exists(OUT):
        out = json.load(open(OUT))
    if which in ("p4", "all"):
        out["P4"] = run_p4()
        json.dump(out, open(OUT, "w"), indent=1)
    if which in ("p5", "all"):
        out["P5"] = run_p5()
        json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT)
