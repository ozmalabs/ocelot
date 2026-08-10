#!/usr/bin/env python3
"""bigville R7 (block 255000) -- GLASS-BOX demonstration of FINANCE.

Runs the eight pre-registered gates end to end on the bigville grid and dumps every
number to results/bigville_fin/summary.json (read straight off the graph -- no
narration). Story: three tenures diverge into a class structure; a fishmonger's bad
run becomes homelessness THROUGH his mortgage (owned-outright weathers it); Scrooge
McBankFace's rate is monetary policy with a face (greedy vs fair); interest is read
stepped as integer coin; the bank's reserves are separate from Scrooge's salary and
can go insolvent while he stays rich; and a slumlord's rent-raise is economic
coercion.

Every accrue/rate/pay-vs-miss/foreclose/salary/insolvency/raise decision is a seed
RULE; this script only arms one-shots, wires edges, ticks and reads.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_fin_world import BigvilleFinWorld    # noqa: E402
from worlds.bigville_time_world import DAY                # noqa: E402

OUT = os.path.join(_ROOT, "results", "bigville_fin")


def _pool(w):
    return sorted(w._cell_at.keys())


def _bank(reserves=100000, salary=0, fair_rate_bp=1000, greed_premium_bp=0.0):
    w = BigvilleFinWorld(day_range=16)
    w.set_phase(DAY)
    w.add_bank("scrooge", _pool(w)[0], reserves=reserves, salary=salary,
               fair_rate_bp=fair_rate_bp, greed_premium_bp=greed_premium_bp)
    return w


def tenure_divergence():
    w = _bank()
    P = _pool(w)
    w.make_char("owner", P[10], coin=1000)
    w.make_char("landlord", P[11], coin=1000)
    w.make_char("renter", P[12], coin=1000)
    w.add_house("h_own", 100, apprec=10)
    w.add_house("h_rent", 100, apprec=10)
    w.own("owner", "h_own")
    w.rent("renter", "landlord", "h_rent", rent=5, term=3)
    eq_o, eq_l, eq_r = [], [], []
    for _ in range(6):
        w.period()
        eq_o.append(w.equity_of("owner"))
        eq_l.append(w.equity_of("landlord"))
        eq_r.append(w.equity_of("renter"))
    return dict(owner_equity=eq_o, landlord_equity=eq_l, renter_equity=eq_r,
                renter_coin=w.coin_of("renter"), landlord_coin=w.coin_of("landlord"),
                diverges=(eq_o[-1] > eq_o[0] and eq_l[-1] > eq_l[0]
                          and len(set(eq_r)) == 1 and eq_r[0] == 0.0))


def leverage(mortgagor):
    w = _bank(fair_rate_bp=500)
    P = _pool(w)
    w.make_char("fish", P[10], coin=1000)
    w.attach_affect("fish", concern_mag=4.0, concern_drop=3.0, arousal=0.0, valence=5.0)
    w.add_house("h", 200, apprec=0)
    if mortgagor:
        w.mortgage("fish", "h", principal=500, payment=30, term=3)
    else:
        w.own("fish", "h")
    w.set_char("fish", coin=0)
    for _ in range(5):
        w.period()
    return dict(missed=w.missed_of("fish"), foreclosed=w.foreclosed_of("fish"),
                homeless=w.homeless_of("fish"), keeps_house=w.owns_house("fish", "h"),
                bank_owns=w.bank_owns("h"), social_concern=w.social_concern_of("fish"),
                affect=w.affect_state("fish"))


def cohort(greed_bp, salary, periods=8, n=4):
    w = _bank(reserves=2000, salary=salary, fair_rate_bp=1000, greed_premium_bp=greed_bp)
    P = _pool(w)
    for i in range(n):
        nm = "m%d" % i
        w.make_char(nm, P[10 + i], coin=40)
        w.add_house("h%d" % i, 400, apprec=0)
        w.mortgage(nm, "h%d" % i, principal=400, payment=5, term=2)
    w.set_rate()
    for _ in range(periods):
        for i in range(n):
            w.set_char("m%d" % i, coin=w.coin_of("m%d" % i) + 45)
        w.period()
    return w, sum(w.foreclosed_of("m%d" % i) for i in range(n))


def interest_stepped():
    w = _bank(fair_rate_bp=1000)
    P = _pool(w)
    w.make_char("d", P[10], coin=0)
    w.add_house("h", 5000)
    w.mortgage("d", "h", principal=1000, payment=0, term=99, deduct_reserves=False)
    graph, closed = [], []
    bal = 1000
    for _ in range(8):
        w.accrue()
        bal = round(bal * 1.10)
        gb = w.balance_of("d")
        graph.append(gb)
        closed.append(float(bal))
    return dict(rate_bp=1000, graph_balance=graph, closed_form=closed,
                match=(graph == closed),
                all_integer=all(v == int(v) for v in graph),
                odd_999_rounds_to=_odd_round())


def _odd_round():
    w = _bank(fair_rate_bp=1000)
    P = _pool(w)
    w.make_char("d", P[10], coin=0)
    w.add_house("h", 5000)
    w.mortgage("d", "h", principal=999, payment=0, term=99, deduct_reserves=False)
    w.accrue()
    return w.balance_of("d")


def salary_run(salary):
    w = _bank(reserves=5000, salary=salary, fair_rate_bp=1000)
    P = _pool(w)
    w.make_char("m", P[10], coin=1000)
    w.add_house("h", 300)
    w.mortgage("m", "h", principal=300, payment=10, term=3)
    sc, res = [], []
    for _ in range(5):
        w.set_char("m", coin=w.coin_of("m") + 200)
        w.period()
        sc.append(w.scrooge_coin())
        res.append(w.reserves())
    return sc, res


def insolvency():
    w = _bank(reserves=300, salary=50, fair_rate_bp=2000)
    P = _pool(w)
    for i in range(2):
        nm = "m%d" % i
        w.make_char(nm, P[10 + i], coin=0)
        w.add_house("h%d" % i, 200)
        w.mortgage(nm, "h%d" % i, principal=100, payment=5, term=99)
    trail = []
    for _ in range(6):
        w.period()
        trail.append(dict(reserves=w.reserves(), scrooge=w.scrooge_coin(),
                          insolvent=w.insolvent()))
        if w.insolvent():
            break
    return dict(trail=trail, insolvent=w.insolvent(), reserves=w.reserves(),
                scrooge_coin=w.scrooge_coin(),
                systemic_but_scrooge_rich=(w.insolvent() == 1 and w.scrooge_coin() > 0))


def rentier(raise_it):
    w = _bank(reserves=1000, salary=0, fair_rate_bp=1000)
    P = _pool(w)
    w.make_char("john", P[5], coin=0, coerce_mag=4.0, coerce_drop=3.0)
    w.make_char("tenant", P[10], coin=1000)
    w.attach_affect("tenant", concern_mag=1.0, concern_drop=1.0, arousal=0.0, valence=5.0)
    w.add_house("h", 200)
    w.rent("tenant", "john", "h", rent=5, term=3, raise_amount=10)
    before = w.affect_state("tenant")
    r0 = w.rent_of("tenant")
    if raise_it:
        w.raise_rent("tenant")
    return dict(rent_before=r0, rent_after=w.rent_of("tenant"),
                valence_before=before["valence"], valence_after=w.affect_state("tenant")["valence"],
                arousal_before=before["arousal"], arousal_after=w.affect_state("tenant")["arousal"],
                backing=w.backing_of("tenant"))


def main():
    os.makedirs(OUT, exist_ok=True)
    R = {}

    R["G_tenure_diverges"] = tenure_divergence()

    lev, own = leverage(True), leverage(False)
    R["G_leverage_amplifies"] = dict(mortgagor=lev, owned_outright_control=own,
        headline=(lev["foreclosed"] == 1 and lev["homeless"] == 1 and not own["homeless"]))

    wf, fc_fair = cohort(0, 15)
    wg, fc_greedy = cohort(1500, 60)
    _wa, fc_a = cohort(0, 15)
    _wb, fc_b = cohort(0, 15)
    R["G_interest_is_policy"] = dict(
        fair_rate_bp=wf.bank_rate_bp(), greedy_rate_bp=wg.bank_rate_bp(),
        fair_foreclosures=fc_fair, greedy_foreclosures=fc_greedy,
        policy=(fc_greedy > fc_fair), rate_held_control=(fc_a == fc_b),
        greedy_reserves=wg.reserves(), fair_reserves=wf.reserves(),
        greedy_scrooge=wg.scrooge_coin(), fair_scrooge=wf.scrooge_coin())

    R["G_interest_is_stepped"] = interest_stepped()

    sc_yes, res_yes = salary_run(30)
    sc_no, res_no = salary_run(0)
    R["G_bank_entity_salary"] = dict(
        with_salary_scrooge=sc_yes, with_salary_reserves=res_yes,
        no_salary_scrooge=sc_no, no_salary_reserves=res_no,
        funds_separate=(res_yes[-1] != sc_yes[-1]),
        no_salary_flat=(len(set(sc_no)) == 1 and sc_no[0] == 0.0),
        bank_still_operates_no_salary=(res_no[-1] != 5000 - 300))

    R["G_greedy_banker"] = dict(
        greedy_reserves=wg.reserves(), fair_reserves=wf.reserves(),
        greedy_foreclosures=fc_greedy, fair_foreclosures=fc_fair,
        greedy_scrooge=wg.scrooge_coin(), fair_scrooge=wf.scrooge_coin(),
        divergence=(wg.reserves() < wf.reserves() and fc_greedy > fc_fair
                    and wg.scrooge_coin() > wf.scrooge_coin()))

    R["G_insolvency"] = insolvency()

    ra, no = rentier(True), rentier(False)
    R["G_rentier_power"] = dict(raise_case=ra, no_raise_control=no,
        power=(ra["valence_after"] < ra["valence_before"] and ra["backing"] > 0
               and no["valence_after"] == no["valence_before"]))

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(R, f, indent=2)

    # glass-box console read-off
    print("=== BIGVILLE R7 — FINANCE (glass-box) ===")
    t = R["G_tenure_diverges"]
    print("TENURE   owner equity :", t["owner_equity"])
    print("         landlord     :", t["landlord_equity"])
    print("         renter (FLAT):", t["renter_equity"], "-> diverges=%s" % t["diverges"])
    lv = R["G_leverage_amplifies"]
    print("LEVERAGE mortgagor: foreclosed=%d homeless=%d bank_owns=%s concern=%d (HEADLINE=%s)"
          % (lv["mortgagor"]["foreclosed"], lv["mortgagor"]["homeless"],
             lv["mortgagor"]["bank_owns"], lv["mortgagor"]["social_concern"], lv["headline"]))
    print("         owned-outright control: homeless=%d keeps_house=%s"
          % (lv["owned_outright_control"]["homeless"], lv["owned_outright_control"]["keeps_house"]))
    p = R["G_interest_is_policy"]
    print("POLICY   fair rate=%d -> %d foreclosures | greedy rate=%d -> %d foreclosures (policy=%s; rate-held control=%s)"
          % (p["fair_rate_bp"], p["fair_foreclosures"], p["greedy_rate_bp"],
             p["greedy_foreclosures"], p["policy"], p["rate_held_control"]))
    s = R["G_interest_is_stepped"]
    print("INTEREST graph balance :", s["graph_balance"])
    print("         closed round(P*1.1^k):", s["closed_form"], "-> match=%s all_integer=%s (999->%.0f)"
          % (s["match"], s["all_integer"], s["odd_999_rounds_to"]))
    b = R["G_bank_entity_salary"]
    print("BANK     Scrooge salary trail:", b["with_salary_scrooge"], "reserves:", b["with_salary_reserves"])
    print("         no-salary Scrooge   :", b["no_salary_scrooge"], "(flat=%s, bank operates=%s)"
          % (b["no_salary_flat"], b["bank_still_operates_no_salary"]))
    g = R["G_greedy_banker"]
    print("GREEDY   reserves greedy=%.0f<fair=%.0f | scrooge greedy=%.0f>fair=%.0f (divergence=%s)"
          % (g["greedy_reserves"], g["fair_reserves"], g["greedy_scrooge"], g["fair_scrooge"], g["divergence"]))
    i = R["G_insolvency"]
    print("INSOLVENCY reserves=%.0f insolvent=%d scrooge_coin=%.0f (systemic yet rich=%s)"
          % (i["reserves"], i["insolvent"], i["scrooge_coin"], i["systemic_but_scrooge_rich"]))
    rr = R["G_rentier_power"]
    print("RENTIER  raise rent %d->%d valence %.0f->%.0f backing->%.0f (power=%s); no-raise valence %.0f->%.0f"
          % (rr["raise_case"]["rent_before"], rr["raise_case"]["rent_after"],
             rr["raise_case"]["valence_before"], rr["raise_case"]["valence_after"],
             rr["raise_case"]["backing"], rr["power"],
             rr["no_raise_control"]["valence_before"], rr["no_raise_control"]["valence_after"]))
    print("\nwrote", os.path.join(OUT, "summary.json"))
    return R


if __name__ == "__main__":
    main()
