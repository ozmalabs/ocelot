#!/usr/bin/env python3
"""bigville R9 (block 257000) -- GLASS-BOX demonstration of INSTITUTIONS & FUNDING.

Runs the eight pre-registered gates end to end on the bigville grid and dumps every
number to results/bigville_fisc/summary.json (read straight off the graph -- no
narration). Story: the town's institutional TRIAD gains its two FUNDING institutions
on top of R7's bank -- the STATE (John + the council: taxes -> a treasury purse ->
the mayor's salary + the constable's wage; a captured council sets a self-serving
rate; a corrupt mayor grafts) and the CHURCH (Mary: voluntary donation -> stipend +
tied parsonage + charity; procyclical + precarious; no lever). Redistribution BREAKS
the interest-only pooling fixpoint (money velocity the readout); the compulsory tax
salary is secure where the voluntary donation stipend is not; and Mary's counselling
is co-regulation.

Every set-tax / collect / pay-salary / graft / levy / tithe / donate / stipend /
charity / defund / counsel decision is a seed RULE; this script only arms one-shots,
wires edges, ticks and reads.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_fisc_world import BigvilleFiscWorld    # noqa: E402
from worlds.bigville_time_world import DAY                  # noqa: E402

OUT = os.path.join(_ROOT, "results", "bigville_fisc")


def _world():
    w = BigvilleFiscWorld(day_range=16)
    w.set_phase(DAY)
    w.add_bank("scrooge", sorted(w._cell_at.keys())[0], reserves=3000, salary=0,
               fair_rate_bp=1000)
    return w


def _pool(w):
    return sorted(w._cell_at.keys())


def mayor_paid(collect):
    w = _world(); P = _pool(w)
    w.add_council(base_rate_bp=1000); w.add_treasury(funds=0)
    w.add_servant("john", P[5], salary=20, role=1)
    w.add_payer("land", P[10], taxable=500, coin=5000)
    w.set_tax()
    if collect:
        w.collect_taxes()
    w.pay_salaries()
    return dict(revenue=w.treasury_revenue(), john_coin=w.coin_of("john"),
                paid=w.paid_count_of("john"), unpaid=w.unpaid_of("john"),
                treasury=w.treasury_funds())


def fisc(premium):
    w = _world(); P = _pool(w)
    w.add_council(base_rate_bp=1000, capture_premium_bp=premium); w.add_treasury(funds=0)
    w.add_payer("land", P[10], taxable=500, coin=5000)
    w.set_tax(); w.collect_taxes()
    return w


def circulation(redistribute, periods=8, n=5):
    w = _world(); P = _pool(w)
    w.add_council(base_rate_bp=6000); w.add_treasury(funds=0)
    workers = []
    for i in range(n):
        w.add_worker("w%d" % i, P[10 + i], coin=100, wage=6); workers.append("w%d" % i)
    w.add_rich("scrooge_p", P[3], levy_amount=6, targets=workers, coin=0)
    w.mark_taxpayer("scrooge_p", taxable=0); w.set_tax()
    circ = []
    for _ in range(periods):
        w.levy()
        if redistribute:
            w.publish_taxables(); w.collect_taxes(); w.pay_salaries()
        circ.append(w.circulation_coin())
    return w, circ


def gov(corrupt, periods=5):
    w = _world(); P = _pool(w)
    w.add_council(base_rate_bp=2000); w.add_treasury(funds=0)
    w.add_servant("john", P[5], salary=0, role=1, corrupt=corrupt, graft_amount=40)
    w.add_servant("constable", P[6], salary=12, role=2)
    w.add_payer("land", P[10], taxable=200, coin=3000)
    w.set_tax()
    for _ in range(periods):
        w.collect_taxes(); w.graft(); w.pay_salaries()
    return w


def church(givers, *, stipend=15, charity=5):
    w = _world(); P = _pool(w)
    w.add_church(funds=0, stipend=stipend, charity_amount=charity)
    w.add_pastor("mary", P[5], safe=1, regulate_up=2, regulate_down=3)
    w.add_poor("tussock", P[6], coin=0)
    for i, g in enumerate(givers):
        w.add_giver("g%d" % i, P[10 + i], **g)
    w.gather_donations()
    return w


def power_asymmetry():
    w = _world(); P = _pool(w)
    w.add_council(base_rate_bp=2000); w.add_treasury(funds=0)
    w.add_servant("john", P[5], salary=15, role=1)
    w.add_payer("landowner", P[10], taxable=300, coin=5000)
    w.add_church(funds=0, stipend=15, charity_amount=5)
    w.add_pastor("mary", P[6], safe=1)
    w.add_giver("poor_giver", P[12], tithe_bp=1000, income=100, coin=0)
    w.add_poor("tussock", P[13], coin=0)
    w.set_tax(); w.collect_taxes(); w.pay_salaries()
    w.gather_donations(); w.pay_stipend(); w.give_charity()
    return dict(john_paid=w.paid_count_of("john"), john_unpaid=w.unpaid_of("john"),
                mary_paid=w.paid_count_of("mary"), mary_unpaid=w.unpaid_of("mary"),
                charity_failed=w.charity_failed())


def counsel(safe):
    w = _world(); P = _pool(w)
    w.add_church(funds=0, stipend=15)
    w.add_pastor("mary", P[5], safe=safe, regulate_up=2, regulate_down=3)
    w.add_distressed("joe", P[10], arousal=8.0, valence=1.0)
    before = w.affect_state("joe"); w.counsel("joe"); after = w.affect_state("joe")
    return dict(arousal_before=before["arousal"], arousal_after=after["arousal"],
                valence_before=before["valence"], valence_after=after["valence"],
                co_regulated=w.co_regulated_of("joe"))


def main():
    os.makedirs(OUT, exist_ok=True)
    R = {}

    paid, ablate = mayor_paid(True), mayor_paid(False)
    R["G_mayor_paid"] = dict(with_tax=paid, ablate_tax=ablate,
        load_bearing=(paid["john_coin"] == 20.0 and ablate["john_coin"] == 0.0
                      and ablate["unpaid"] == 1))

    wf, wc = fisc(0), fisc(2000)
    a, b = fisc(0), fisc(0)
    R["G_tax_is_council_policy"] = dict(
        fair_rate_bp=wf.tax_rate_bp(), captured_rate_bp=wc.tax_rate_bp(),
        fair_revenue=wf.treasury_revenue(), captured_revenue=wc.treasury_revenue(),
        policy=(wc.tax_rate_bp() > wf.tax_rate_bp()
                and wc.treasury_revenue() > wf.treasury_revenue()),
        rate_held_control=(a.treasury_revenue() == b.treasury_revenue()))

    wo, circ_off = circulation(False)
    wr, circ_on = circulation(True)
    R["G_redistribution_breaks_fixpoint"] = dict(
        levy_only_circulation=circ_off, redistribution_circulation=circ_on,
        levy_only_pile=wo.coin_of("scrooge_p"), redistribution_pile=wr.coin_of("scrooge_p"),
        off_pools=all(circ_off[i + 1] <= circ_off[i] for i in range(len(circ_off) - 1)),
        redistribution_sustains=(circ_on[-1] > circ_off[-1]),
        pooling_broken=(wo.coin_of("scrooge_p") > wr.coin_of("scrooge_p")),
        purse_never_overdrawn=(wr.treasury_funds() >= 0.0))

    gc, gf = gov(1), gov(0)
    R["G_mayoral_corruption"] = dict(
        corrupt_treasury=gc.treasury_funds(), fair_treasury=gf.treasury_funds(),
        corrupt_john_coin=gc.coin_of("john"), fair_john_coin=gf.coin_of("john"),
        corrupt_grafted=gc.grafted_of("john"), corrupt_constable_unpaid=gc.unpaid_of("constable"),
        fair_constable_paid=gf.paid_count_of("constable"),
        corrupt_depleted=gc.treasury_depleted(),
        divergence=(gc.treasury_funds() < gf.treasury_funds()
                    and gc.coin_of("john") > gf.coin_of("john")
                    and gc.unpaid_of("constable") == 1 and gf.unpaid_of("constable") == 0))

    donate = church([dict(tithe_bp=1000, income=100, coin=500),
                     dict(occasional=1, donate_amount=8, flush_threshold=50, coin=500),
                     dict(coin=500)])
    donate.pay_stipend()
    ablate_dev = church([dict(coin=500), dict(coin=500)])
    ablate_dev.pay_stipend()
    R["G_church_by_donation"] = dict(
        income=donate.church_income(), none_gave_nothing=(donate.coin_of("g2") == 500.0),
        mary_paid=donate.paid_count_of("mary"),
        ablate_devotion_income=ablate_dev.church_income(),
        ablate_devotion_mary_unpaid=ablate_dev.unpaid_of("mary"),
        voluntary=(donate.church_income() == 18.0 and ablate_dev.church_income() == 0.0
                   and ablate_dev.unpaid_of("mary") == 1))

    good = church([dict(tithe_bp=2000, income=200, coin=500)])
    good.pay_stipend(); good.give_charity()
    bad = church([dict(tithe_bp=2000, income=200, coin=0)])
    bad.pay_stipend(); bad.give_charity(); bad.check_parsonage()
    R["G_church_procyclical"] = dict(
        good_income=good.church_income(), good_mary_unpaid=good.unpaid_of("mary"),
        good_charity_failed=good.charity_failed(),
        downturn_income=bad.church_income(), downturn_mary_unpaid=bad.unpaid_of("mary"),
        downturn_charity_failed=bad.charity_failed(), downturn_defunct=bad.church_defunct(),
        downturn_mary_homeless=bad.homeless_of("mary"),
        procyclical=(bad.church_income() == 0.0 and bad.unpaid_of("mary") == 1
                     and bad.charity_failed() == 1 and bad.homeless_of("mary") == 1))

    R["G_power_asymmetry"] = power_asymmetry()
    R["G_power_asymmetry"]["asymmetry"] = (
        R["G_power_asymmetry"]["john_paid"] == 1 and R["G_power_asymmetry"]["mary_unpaid"] == 1)

    cs, cu = counsel(1), counsel(0)
    R["G_counselling_co_regulation"] = dict(safe=cs, unsafe_control=cu,
        co_regulation=(cs["arousal_after"] < cs["arousal_before"]
                       and cs["valence_after"] > cs["valence_before"]
                       and cs["co_regulated"] == 1
                       and cu["arousal_after"] == cu["arousal_before"]
                       and cu["co_regulated"] == 0))

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(R, f, indent=2)

    # glass-box console read-off
    print("=== BIGVILLE R9 — INSTITUTIONS & FUNDING (glass-box) ===")
    m = R["G_mayor_paid"]
    print("MAYOR    with tax: john coin=%.0f paid=%d | ablate tax: coin=%.0f unpaid=%d (load-bearing=%s)"
          % (m["with_tax"]["john_coin"], m["with_tax"]["paid"], m["ablate_tax"]["john_coin"],
             m["ablate_tax"]["unpaid"], m["load_bearing"]))
    p = R["G_tax_is_council_policy"]
    print("TAX      fair rate=%.0f rev=%.0f | captured rate=%.0f rev=%.0f (policy=%s; held control=%s)"
          % (p["fair_rate_bp"], p["fair_revenue"], p["captured_rate_bp"], p["captured_revenue"],
             p["policy"], p["rate_held_control"]))
    c = R["G_redistribution_breaks_fixpoint"]
    print("CIRC     levy-only:", c["levy_only_circulation"], "pile=%.0f" % c["levy_only_pile"])
    print("         redistrib:", c["redistribution_circulation"], "pile=%.0f (broken=%s sustains=%s)"
          % (c["redistribution_pile"], c["pooling_broken"], c["redistribution_sustains"]))
    g = R["G_mayoral_corruption"]
    print("CORRUPT  corrupt: treasury=%.0f john=%.0f constable_unpaid=%d depleted=%d | fair: treasury=%.0f (divergence=%s)"
          % (g["corrupt_treasury"], g["corrupt_john_coin"], g["corrupt_constable_unpaid"],
             g["corrupt_depleted"], g["fair_treasury"], g["divergence"]))
    d = R["G_church_by_donation"]
    print("CHURCH   income=%.0f (none gave nothing=%s) | ablate devotion: income=%.0f mary unpaid=%d (voluntary=%s)"
          % (d["income"], d["none_gave_nothing"], d["ablate_devotion_income"],
             d["ablate_devotion_mary_unpaid"], d["voluntary"]))
    pc = R["G_church_procyclical"]
    print("PROCYCL  good: income=%.0f | downturn: income=%.0f mary unpaid=%d charity failed=%d homeless=%d (procyclical=%s)"
          % (pc["good_income"], pc["downturn_income"], pc["downturn_mary_unpaid"],
             pc["downturn_charity_failed"], pc["downturn_mary_homeless"], pc["procyclical"]))
    pa = R["G_power_asymmetry"]
    print("POWER    crisis: John (tax) paid=%d | Mary (donation) unpaid=%d charity failed=%d (asymmetry=%s)"
          % (pa["john_paid"], pa["mary_unpaid"], pa["charity_failed"], pa["asymmetry"]))
    cc = R["G_counselling_co_regulation"]
    print("COUNSEL  safe: arousal %.0f->%.0f valence %.0f->%.0f coreg=%d | unsafe: arousal %.0f->%.0f coreg=%d (co-reg=%s)"
          % (cc["safe"]["arousal_before"], cc["safe"]["arousal_after"], cc["safe"]["valence_before"],
             cc["safe"]["valence_after"], cc["safe"]["co_regulated"], cc["unsafe_control"]["arousal_before"],
             cc["unsafe_control"]["arousal_after"], cc["unsafe_control"]["co_regulated"], cc["co_regulation"]))
    print("\nwrote", os.path.join(OUT, "summary.json"))
    return R


if __name__ == "__main__":
    main()
