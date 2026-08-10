#!/usr/bin/env python3
"""bigville R22 (block 270000) -- THE DOCTOR: the town-scale HEALTH-INEQUALITY
measurement + the public-health lever. Writes results/bigville_doctor/summary.json.

A town of N residents with a seeded WEALTH gradient (default_rng(270000)) meets
ONE disease striking all. Private (fee-for-service) health: survival tracks
wealth -- the poor die of a TREATABLE illness. Flip council-funded PUBLIC HEALTH
on (the treasury pays the doctor): the SAME disease no longer kills the poor --
the wealth-health gradient DISSOLVES. Every decision is a graph rule (bd_*); this
script only ingests, ticks and reads. ZERO new Rust.

Run:  python scripts/bigville_doctor_run.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_doctor_world import BigvilleDoctorWorld           # noqa: E402
from worlds.bigville_time_world import DAY                             # noqa: E402

SEED = 270000
TREAT_FEE = 30.0
HEALTH = 40.0
DISEASE = 50.0            # severe: kills the untreated (drop 50 >= health 40)


def _corr(xs, ys):
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    if xs.std() < 1e-12 or ys.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(xs, ys)[0, 1])


def _run_town(coins, *, public_health):
    """Build a town with the given wealth vector, one disease for all, under the
    given health regime. Returns (survived[list 0/1], coins[list])."""
    w = BigvilleDoctorWorld(day_range=64)
    w.set_phase(DAY)
    P = sorted(w._cell_at.keys())
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=TREAT_FEE)
    w.add_treasury(10_000_000.0)
    names = []
    for i, c in enumerate(coins):
        nm = "r%d" % i
        w.admit(nm, P[5 + i], coin=float(c), health=HEALTH,
                progression=0.0, treat_relief=40.0)
        names.append(nm)
    if public_health:
        w.set_public_health(True, names)
    for nm in names:
        w.seek_care(nm)          # everyone seeks care; the rule gates affordability
    for nm in names:
        w.strike(nm, DISEASE)    # the SAME disease for all
    survived = [0 if w.is_dead(nm) else 1 for nm in names]
    return survived, list(coins)


def main():
    rng = np.random.default_rng(SEED)
    n = 40
    # a lognormal-ish wealth gradient, many poor + a few rich (bounded to keep the
    # town small + watchable); some below the fee, some above.
    coins = np.clip(np.round(rng.lognormal(mean=3.0, sigma=1.0, size=n)), 0, 500)

    priv_surv, _ = _run_town(coins, public_health=False)
    pub_surv, _ = _run_town(coins, public_health=True)

    afford = [1 if c >= TREAT_FEE else 0 for c in coins]
    poor_idx = [i for i, c in enumerate(coins) if c < TREAT_FEE]
    rich_idx = [i for i, c in enumerate(coins) if c >= TREAT_FEE]

    summary = {
        "block": SEED,
        "seed": SEED,
        "n": int(n),
        "treat_fee": TREAT_FEE,
        "health": HEALTH,
        "disease_base": DISEASE,
        "private_health": {
            "survivors": int(sum(priv_surv)),
            "dead": int(n - sum(priv_surv)),
            "poor_survival_rate": (sum(priv_surv[i] for i in poor_idx) / len(poor_idx)) if poor_idx else None,
            "rich_survival_rate": (sum(priv_surv[i] for i in rich_idx) / len(rich_idx)) if rich_idx else None,
            "corr_wealth_survival": _corr(coins, priv_surv),
            "corr_afford_survival": _corr(afford, priv_surv),
        },
        "public_health": {
            "survivors": int(sum(pub_surv)),
            "dead": int(n - sum(pub_surv)),
            "poor_survival_rate": (sum(pub_surv[i] for i in poor_idx) / len(poor_idx)) if poor_idx else None,
            "rich_survival_rate": (sum(pub_surv[i] for i in rich_idx) / len(rich_idx)) if rich_idx else None,
            "corr_wealth_survival": _corr(coins, pub_surv),
        },
        "n_poor_below_fee": len(poor_idx),
        "n_rich_at_or_above_fee": len(rich_idx),
        "headline": (
            "Private health: survival = affordability (corr_afford_survival = 1.0); "
            "the poor die of a treatable illness. Public health: the gradient "
            "vanishes (corr_wealth_survival -> 0; all survive)."),
    }

    out_dir = os.path.join(ROOT, "results", "bigville_doctor")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
        f.write("\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
