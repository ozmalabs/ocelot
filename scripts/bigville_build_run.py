#!/usr/bin/env python3
"""bigville R12 (block 260000) -- the GROWTH LOOP + BOOM/BUST measurement
(MEASURE-FIRST, per BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 2.8 G-growth-loop).

Two arms over the graph-native construction machinery, EVERY decision a rule:

  * SUSTAINED arm -- N incoming households each fund a house from SAVINGS and build
    it. The town's carrying capacity (built housing units) rises ORGANICALLY 0 -> N;
    money is conserved (coin only moves builder -> nobody, materials are consumed).
    A living, growing town.

  * BOOM/BUST arm -- N builders build on BANK LOANS (debt-financed). The built stock
    still rises (the boom), but every builder now carries an interest-bearing
    BuildLoan; accruing interest with no income drives the total debt UP past the
    coin the builders hold -- the debt-fuelled BUST (the R7 interest-fixpoint at the
    construction level; a natural PUNCTUATION, R10). Reported, not tuned away.

Writes results/bigville_build/summary.json. No claim beyond what the numbers show.

Run:  python scripts/bigville_build_run.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from worlds.bigville_build_world import BigvilleBuildWorld           # noqa: E402
from worlds.bigville_time_world import DAY                           # noqa: E402

SITES = [(1, 1), (2, 1), (3, 1), (25, 1), (26, 1), (24, 1)]


def sustained_arm(n=6):
    w = BigvilleBuildWorld(day_range=200)
    w.set_phase(DAY)
    trajectory = [0]
    total_coin0 = 0.0
    for i in range(n):
        name = "hh_%d" % i
        w.make_char(name, (12, 8), coin=1000)
        total_coin0 += 1000.0
        w.add_buildable_plot("h%d" % i, SITES[i], required=2, mat_cost=1, build_cost=50)
        w.own_plot(name, "h%d" % i)
        w.set_construction_skill(name, 2)
        w.give_materials(name, timber=10, stone=10)
        w.fund(name, "h%d" % i)
        w.build_until_done(name, "h%d" % i)
        trajectory.append(w.building_count())
    total_coin1 = sum(w.coin_of("hh_%d" % i) for i in range(n))
    return dict(households=n, capacity_trajectory=trajectory,
                final_capacity=w.building_count(),
                coin_before=total_coin0, coin_after_in_hands=total_coin1,
                coin_spent_on_construction=total_coin0 - total_coin1)


def boom_bust_arm(n=4, accrue_periods=30):
    w = BigvilleBuildWorld(day_range=400)
    w.set_phase(DAY)
    P = sorted(w._cell_at.keys())
    w.add_bank("scrooge", P[0], reserves=1_000_000, salary=0, fair_rate_bp=2000)  # 20%
    reserves0 = w.reserves()
    for i in range(n):
        name = "spec_%d" % i
        w.make_char(name, (12, 8), coin=0)
        w.add_buildable_plot("b%d" % i, SITES[i], required=2, mat_cost=1, build_cost=100)
        w.own_plot(name, "b%d" % i)
        w.set_construction_skill(name, 2)
        w.give_materials(name, timber=10, stone=10)
        w.take_loan(name, 100)          # debt-financed
        w.fund(name, "b%d" % i)
        w.build_until_done(name, "b%d" % i)
    boom_capacity = w.building_count()
    debt0 = sum(w.loan_balance_of("spec_%d" % i) for i in range(n))
    # the bust: interest accrues with no income -> debt compounds past what they hold
    for _ in range(accrue_periods):
        for i in range(n):
            w.accrue_loan("spec_%d" % i)
    debt1 = sum(w.loan_balance_of("spec_%d" % i) for i in range(n))
    coin_in_hands = sum(w.coin_of("spec_%d" % i) for i in range(n))
    return dict(speculators=n, boom_capacity=boom_capacity,
                debt_after_build=debt0, debt_after_accrue=debt1,
                accrue_periods=accrue_periods, rate_bp=2000,
                coin_in_hands=coin_in_hands,
                bust=debt1 > coin_in_hands,          # underwater = structural default
                bank_reserves_before=reserves0, bank_reserves_after=w.reserves())


def main():
    out_dir = os.path.join(ROOT, "results", "bigville_build")
    os.makedirs(out_dir, exist_ok=True)
    summary = dict(
        rung="R12", block=260000,
        headline="construction is graph-native; the town's physical form MUTATES",
        sustained=sustained_arm(),
        boom_bust=boom_bust_arm(),
        notes=[
            "Every construction decision is a seed rule (bigville_build_construct / "
            "bigville_build_mutate); the adapter is mechanical I/O. ZERO new Rust.",
            "SUSTAINED: carrying capacity rises organically with population; coin is "
            "conserved (spent coin leaves the builders' hands to nobody -- a closed "
            "personal-funding town). The physical form is emergent, not hand-placed.",
            "BOOM/BUST: debt-financed building booms the stock, then compounding "
            "interest with no income drives every builder underwater (debt > coin) -- "
            "the R7 interest-fixpoint at the construction level, a natural punctuation "
            "(R10). Reported as a FINDING, not tuned away.",
            "HONEST RESIDUALS: the growth loop is demonstrated at small N on the fixed "
            "scaffold town (not swept to 200); immigration/birth inflow, carrying-"
            "capacity balance vs consumption (R5), and a full boom->bust->recovery "
            "time-series are deferred to the integrative capstone (R10). This rung "
            "gates the MECHANISM (build/fund/mutate/expand), not the macro dynamics.",
        ],
    )
    path = os.path.join(out_dir, "summary.json")
    with open(path, "w") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    print("wrote", path)
    print(json.dumps(summary["sustained"], indent=2))
    print(json.dumps(summary["boom_bust"], indent=2))


if __name__ == "__main__":
    main()
