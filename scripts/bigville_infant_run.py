#!/usr/bin/env python3
"""bigville R22b (block 272000) -- INFANT MORTALITY measurement runner. Reproduces
the four headline gates on the seeded graph and dumps the measured numbers to
results/bigville_infant/summary.json. Pure world I/O over the seed rules (no agent
decision in Python); the numbers are the graph's outcome, read off.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_infant_world import BigvilleInfantWorld          # noqa: E402
from worlds.bigville_time_world import DAY                            # noqa: E402
from domains.engine_provenance import engine_provenance              # noqa: E402


def _w():
    w = BigvilleInfantWorld(day_range=16)
    w.set_phase(DAY)
    return w


def _pool(w):
    return sorted(w._cell_at.keys())


def measure():
    out = {}

    # G-infant-fragility: unseen infant dies of a small shock; adult survives.
    w = _w(); P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=10.0)
    w.add_baby("baby", P[10], coin=0.0, health=40.0, infant_fragility=40.0)
    w.admit("adult", P[11], coin=0.0, health=40.0, progression=0.0)
    w.infant_strike("baby", 20.0); w.strike("adult", 20.0)
    out["infant_fragility"] = dict(
        shock_base=20.0, fragility=40.0, health=40.0,
        infant_effective_drop=60.0, infant_dead=w.is_dead("baby"),
        adult_effective_drop=20.0, adult_dead=w.is_dead("adult"),
        adult_health=w.health_of("adult"))

    # G-well-baby-care-reduces-mortality: seen survives, unseen dies (same shock).
    w = _w(); P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=10.0)
    w.add_baby("seen", P[10], coin=100.0, health=40.0, infant_fragility=40.0)
    w.add_baby("unseen", P[11], coin=100.0, health=40.0, infant_fragility=40.0)
    w.well_baby_visit("seen")
    w.infant_strike("seen", 20.0); w.infant_strike("unseen", 20.0)
    out["wellbaby_reduces_mortality"] = dict(
        seen_well_baby=w.well_baby_of("seen"), seen_dead=w.is_dead("seen"),
        seen_health=w.health_of("seen"),
        unseen_well_baby=w.well_baby_of("unseen"), unseen_dead=w.is_dead("unseen"),
        fee_paid_by_seen=100.0 - w.coin_of("seen"), doctor_income=w.doctor_coin())

    # G-infant-mortality-tracks-wealth: cohort wealth gradient, one disease.
    coins = [0.0, 5.0, 10.0, 20.0, 29.0, 30.0, 50.0, 100.0]
    w = _w(); P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=30.0)
    names = []
    for i, c in enumerate(coins):
        nm = "b%d" % i
        w.add_baby(nm, P[10 + i], coin=c, health=40.0, infant_fragility=40.0)
        names.append(nm)
    for nm in names:
        w.well_baby_visit(nm)
    for nm in names:
        w.infant_strike(nm, 20.0)
    out["mortality_tracks_wealth"] = dict(
        wellbaby_fee=30.0, coins=coins,
        dead=[bool(w.is_dead(nm)) for nm in names],
        n_dead=int(sum(w.is_dead(nm) for nm in names)),
        infant_mortality=w.infant_mortality(names),
        survivors_min_wealth=min(c for nm, c in zip(names, coins) if not w.is_dead(nm)),
        wealth_survival_corr=w.wealth_mortality_corr(names, coins))

    # G-public-health-lever: same cohort, public well-baby care -> all survive.
    w = _w(); P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=30.0)
    w.add_treasury(10000.0)
    names = []
    for i, c in enumerate(coins):
        nm = "b%d" % i
        w.add_baby(nm, P[10 + i], coin=c, health=40.0, infant_fragility=40.0)
        names.append(nm)
    w.set_public_health(True, names)
    f0 = w.treasury_funds()
    for nm in names:
        w.well_baby_visit(nm)
    for nm in names:
        w.infant_strike(nm, 20.0)
    out["public_health_lever"] = dict(
        all_well_baby=all(w.well_baby_of(nm) for nm in names),
        infant_mortality=w.infant_mortality(names),
        wealth_survival_corr=w.wealth_mortality_corr(names, coins),
        out_of_pocket=[round(c - w.coin_of(nm), 6) for nm, c in zip(names, coins)],
        treasury_paid=round(f0 - w.treasury_funds(), 6))

    p = engine_provenance()
    out["_provenance"] = dict(short=p["short"], source_match=p["source_match"],
                              native_path=p["native_path"])
    return out


if __name__ == "__main__":
    res = measure()
    d = os.path.join(ROOT, "results", "bigville_infant")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "summary.json"), "w") as f:
        json.dump(res, f, indent=2)
        f.write("\n")
    print(json.dumps(res, indent=2))
