#!/usr/bin/env python3
"""BLOCK 215000 -- SPITE-TO-SUCCEED measurement (powered, CIs).

Runs the pre-registered gates (SPITE_TO_SUCCEED_PREREG.md) over the graph-native
AchieveWorld adapter. Every agent decision is the seed's rule; this script only
configures the task, reads the graph's decision, and aggregates with bootstrap
CIs. Seed block 215000-215999 (base 215000).

    python3 scripts/spite_to_succeed_measure.py
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains.achieve_world import AchieveWorld   # noqa: E402

BASE = 215000
BASELINE_OUTPUT = 4   # the un-slighted optimum (argmax of 8e - e^2)


def boot_ci(xs, reps=2000, seed=BASE):
    xs = np.asarray(xs, dtype=float)
    if len(xs) == 0:
        return (0.0, 0.0, 0.0)
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(xs, size=len(xs), replace=True).mean() for _ in range(reps)])
    return (round(float(xs.mean()), 4),
            round(float(np.percentile(means, 2.5)), 4),
            round(float(np.percentile(means, 97.5)), 4))


def g_succeed(N=200):
    """Paired: control (no slight) vs slighted (witnessed) vs slighted-unwitnessed.
    rival_ach ~ U{3,4,5}, slight m ~ U{8..16}, efficacy=10."""
    rng = np.random.default_rng(BASE)
    ctrl, slig, unwit, slig_harm = [], [], [], []
    for r in range(N):
        ra = int(rng.integers(3, 6))        # {3,4,5}
        m = int(rng.integers(8, 17))        # {8..16}
        w = AchieveWorld(slights=[], efficacy=10, rival_ach=ra, observed=True)
        ctrl.append(w.decide(0)["output"]); w.close()
        w = AchieveWorld(slights=[(m, 0)], efficacy=10, rival_ach=ra, observed=True)
        d = w.decide(0); slig.append(d["output"]); slig_harm.append(d["rival_harm"]); w.close()
        w = AchieveWorld(slights=[(m, 0)], efficacy=10, rival_ach=ra, observed=False)
        unwit.append(w.decide(0)["output"]); w.close()
    uplift = [s - c for s, c in zip(slig, ctrl)]
    return {
        "N": N,
        "control_output": boot_ci(ctrl, seed=BASE + 1),
        "slighted_output": boot_ci(slig, seed=BASE + 2),
        "unwitnessed_output": boot_ci(unwit, seed=BASE + 3),
        "paired_uplift": boot_ci(uplift, seed=BASE + 4),
        "slighted_rival_harm_max": int(max(slig_harm)),        # self-benefiting => 0
        "slighted_all_kind_succeed": bool(all(h == 0 for h in slig_harm)),
    }


def g_develops():
    """Dose-response (exact), accumulation, and the scale2 decay schedule."""
    dose = []
    for m in range(0, 21, 2):
        w = AchieveWorld(slights=([(m, 0)] if m > 0 else []), efficacy=10, observed=True)
        d = w.decide(0); dose.append({"m": m, "G": d["grievance"], "output": d["output"]}); w.close()
    accum = []
    for k in (1, 2, 3):
        w = AchieveWorld(slights=[(6, 0)] * k, efficacy=10, observed=True)
        d = w.decide(0); accum.append({"slights": k, "G": d["grievance"], "output": d["output"]}); w.close()
    decay = {}
    for H in (1, 4, 16):
        row = []
        for t in range(0, 21):
            w = AchieveWorld(slights=[(16, 0)], efficacy=10, observed=True, half_life=H)
            row.append(w.decide(t)["grievance"]); w.close()
        decay[f"half_life_{H}"] = row
    monotone = all(dose[i]["output"] <= dose[i + 1]["output"] for i in range(len(dose) - 1)) \
        and dose[0]["output"] == BASELINE_OUTPUT
    # scale2 check: G(t) == 16 >> (t // H)
    scale2_ok = all(decay[f"half_life_{H}"][t] == (16 >> (t // H)) for H in (1, 4, 16) for t in range(21))
    return {"dose_response": dose, "accumulation": accum, "decay": decay,
            "monotone_and_zero_slight_is_baseline": monotone, "scale2_law_holds": scale2_ok}


def g_channel():
    """Fix witnessed grievance G=12; sweep efficacy. HIGH => succeed (output up,
    harm 0); LOW => destroy (output 0, harm up). The channel flip."""
    sweep = []
    for eff in range(0, 11):
        w = AchieveWorld(slights=[(12, 0)], efficacy=eff, observed=True)
        d = w.decide(0)
        sweep.append({"efficacy": eff, "kind_succeed": d["kind_succeed"],
                      "output": d["output"], "rival_harm": d["rival_harm"]})
        w.close()
    high = [s for s in sweep if s["efficacy"] >= 5]
    low = [s for s in sweep if s["efficacy"] < 5]
    flip = all(s["kind_succeed"] == 1 and s["rival_harm"] == 0 for s in high) \
        and all(s["kind_succeed"] == 0 and s["output"] == 0 and s["rival_harm"] > 0 for s in low)
    return {"sweep": sweep, "efficacy_flips_channel": flip}


def main():
    out = {"g_succeed": g_succeed(), "g_develops": g_develops(), "g_channel": g_channel()}
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    path = os.path.join(ROOT, "results", "spite_to_succeed.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    print("\nwrote", path)


if __name__ == "__main__":
    main()
