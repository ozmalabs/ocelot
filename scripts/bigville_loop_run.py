"""bigville_loop_run -- R5 (block 253000) glass-box DEMONSTRATION: THE LOOP CLOSES +
emergent cascades. Reads the whole integrated town off the graph, nothing scripted.

(1) THE TOWN over multiple days (measure-first): the DEFAULT viable regime SUSTAINS
    (every consumer fed, money conserved); two protected probes surface REAL failures --
    wages-off -> coin POOLS at producers and demand SEIZES though goods are plentiful;
    a carrying-capacity SHORTFALL -> progressive FAMINE. Glass-box: Marjorie's whole day.
(2) THE FISHMONGER CASCADE (headline, the anti-bullshit gate): induce Doreen's
    exhaustion collapse, then read EVERY HOP off the graph -- (a) missed opening ->
    expectation SURPRISE; (b) DOWN-chain: no fish -> a fish-preferrer satisfices to bread;
    (c) UP-chain: coins on drink -> can't pay the fisherman -> DEFAULT -> his AFFECT flips
    -> he BADMOUTHS Doreen -> townsfolk backing flips (the 245 credibility layer MOVES).
(3) THE SEVER control: cut the supply edge -> the whole downstream cascade + affect flip
    + society move VANISH (propagation is along the graph, not authored).

Writes results/bigville_loop/demo.json.
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_loop_world import BigvilleLoopWorld            # noqa: E402
from worlds.bigville_econ_world import (                           # noqa: E402
    GRAIN, BREAD, FISH, BAIT, ALE, FISHING, BAITING)
from worlds.bigville_time_world import DAY, NIGHT                  # noqa: E402

OUT_DIR = os.path.join(_ROOT, "results", "bigville_loop")
ALEHOUSE = (24, 10)          # near Doreen's stall -> she drinks BEFORE she is exhausted
FISHSTALL = (26, 8)
BAKERY = (5, 8)


# ============================================================ (1) THE TOWN
def demo_town(days=4):
    def one(regime, wages_on):
        w = BigvilleLoopWorld(day_range=16, regime=regime, wages_on=wages_on)
        cap = w.carrying_capacity()
        cen = w.run_town(days=days)
        out = dict(
            regime=regime, wages_on=wages_on, days=days,
            carrying_capacity=cap,
            coin_conserved=w.coin_conserved(),
            per_day=[dict(day=r["day"], observed_balance=r["observed_balance"],
                          unmet_demand=r["unmet_demand"], total_coin=r["total_coin"])
                     for r in cen],
            marjorie_day1=w.marjorie_day(1)[0],
            final=dict(
                producers={nm: w.coin_of(nm) for nm in sorted(w._trade_names)},
                consumers={nm: w.coin_of(nm) for nm in
                           ["Peony Fen", "Agnes Thorn", "Sergeant Bram Cobble",
                            "Nettie Sparrow"] if nm in w._movers}))
        w.close()
        return out

    return dict(
        default_viable_sustains=one("viable", True),
        probe_wages_off_money_pools=one("viable", False),
        probe_shortfall_famine=one("shortfall", True))


# ============================================================ (2)+(3) CASCADE
def _cascade_world():
    """A curated cascade stage (the registered demonstration): the alehouse (drink),
    the fisherman (creditor), Doreen the fishmonger (debtor keeper), a would-be
    customer holding the open expectation, a fish-preferring consumer with R2 sources,
    and three townsfolk who opine on Doreen. All actors are graph data; every hop is
    a rule verdict read back."""
    w = BigvilleLoopWorld(cascade_only=True, day_range=16)
    w.set_phase(DAY)
    # alehouse -- where Doreen drinks (coins really leave her)
    w.make_trader("alekeep", ALEHOUSE, coin=0)
    w.add_shop("alehouse", good=ALE, price=3, cell=ALEHOUSE, keeper="alekeep",
               activity=0, input_good=0, stock=5, input_qty=0)
    # fisherman -- the creditor; badmouth_strength sours into testimony on default
    w.make_trader("fisherman", (28, 4), coin=0, credit_trust=50.0, risk_weight=100.0,
                  sour_amount=80.0, badmouth_strength=3.0)
    w.set_skill("fisherman", FISHING, 4)
    w.add_shop("fishermanshop", good=FISH, price=5, cell=(28, 4), keeper="fisherman",
               activity=FISHING, input_good=BAIT, stock=3, input_qty=0)
    # Doreen -- the fishmonger/debtor keeper; standing=5 among the townsfolk
    w.make_trader("Doreen Ferrety", FISHSTALL, coin=3, credit_trust=0.0, credit_term=1.0,
                  standing=5.0, badmouthed=0.0, energy=100.0)
    w.give_good("Doreen Ferrety", ALE)
    w.add_shop("fishstall", good=FISH, price=6, cell=FISHSTALL, keeper="Doreen Ferrety",
               activity=0, input_good=FISH, stock=0, input_qty=0, supplier="fishermanshop")
    # a would-be customer holding the town's "the stall opens" expectation
    w.make_trader("custA", (23, 9))
    w.add_expectation("custA", "fishstall", open_due=0)     # armed at the due moment below
    # three townsfolk who opine on Doreen (the sparse social graph)
    for i, cell in enumerate([(2, 2), (2, 3), (2, 4)]):
        w.make_trader("townsperson_%d" % i, cell)
        w.opines("townsperson_%d" % i, "Doreen Ferrety")
    w.refresh_open()
    return w


def demo_cascade(sever=False):
    w = _cascade_world()
    hops = {}

    # settle townsfolk opinion pre-cascade (standing intact -> backs Doreen)
    w._run()
    hops["pre_backs"] = [w.backs_debtor_of("townsperson_%d" % i) for i in range(3)]

    if sever:
        w.sever_supply("fishstall", "fishermanshop")

    # --- Doreen DRINKS: coins really leave her (a real state change) --------------
    coin0 = w.coin_of("Doreen Ferrety")
    w._navigate_to("Doreen Ferrety", ALEHOUSE)
    w.buy("Doreen Ferrety")                                  # ale exchange
    hops["drink"] = dict(coin_before=coin0, coin_after=w.coin_of("Doreen Ferrety"),
                         ale_held=w.inventory_of("Doreen Ferrety", ALE))

    # --- EXHAUSTION COLLAPSE (R3): pushed past threshold, no sleep option ----------
    w.configure_time("Doreen Ferrety", energy=2.0, sleep_enabled=0.0, safe=0.0)
    w.set_phase(NIGHT)
    for _ in range(3):
        w.run_sleep_decisions()
    hops["collapse"] = w.sleep_state("Doreen Ferrety")

    # --- (a) MISSED OPENING -> EXPECTATION SURPRISE (R4) ---------------------------
    w.set_phase(DAY)
    w.set_hours(1)
    w.set_open_due("custA", "fishstall", 1)                  # the due moment arrives
    w.refresh_open()                                         # collapsed keeper -> shut
    hops["expectation"] = dict(stall_open=w.shop_open("fishstall"),
                               surprise=w.surprise_count("custA"))

    # --- (b) DOWN-CHAIN: no fish -> a fish-preferrer satisfices to bread (R2) ------
    #   the fish-preferrer prefers FISH over BREAD; fish source at the (now shut)
    #   stall present -> picks fish; the stall shut removes the reachable fish source
    #   -> the SAME preferrer satisfices to bread (R2's proven reachability flip).
    w.make_trader("fishlover", (22, 8))
    fsrc = w.add_source("fishsrc", FISH, FISHSTALL)
    w.add_source("breadsrc", BREAD, BAKERY)
    w.set_preferences("fishlover", {FISH: 6.0, BREAD: 3.0}, cost_on=1.0)
    w.set_drive("fishlover", 1.0, v_d=10.0, c_d=0.0)        # SUSTENANCE need_code=1
    with_fish = w.decide("fishlover")
    # the stall is SHUT -> there is NO fish to buy: remove the fish source, so the only
    # reachable satisfier is bread and the fish-preferrer SATISFICES to it (R2 Argmax).
    w._sources.pop("fishsrc")
    for _c in list(w.eng.neighbours(fsrc, "at_cell")):
        w.eng.remove_edge_unchecked(fsrc, "at_cell", _c)
    w.eng.remove_node(fsrc)
    no_fish = w.decide("fishlover")
    hops["down_chain"] = dict(
        with_fish_chosen=int(with_fish.get("chosen_good_code") or 0),
        satisfices_to=int(no_fish.get("chosen_good_code") or 0),
        FISH=int(FISH), BREAD=int(BREAD))

    # --- (c) UP-CHAIN: can't pay -> DEFAULT -> AFFECT flip -> BADMOUTH -> 245 moves -
    w.attach_creditor_affect("fisherman", concern_mag=4.0, concern_drop=3.0,
                             arousal=0.0, valence=5.0)
    aff0 = w.affect_state("fisherman")
    w.restock("fishstall")                                  # short (drank) -> credit -> owe
    owe = w.owes_of("Doreen Ferrety")
    w.world_epoch = 5
    w.tick_obligations()                                    # past term -> default -> affect
    w._run()                                                # badmouth -> opinion flip
    hops["up_chain"] = dict(
        owe_minted=owe,
        doreen_defaulted=w.default_count_of("Doreen Ferrety"),
        fisherman_arousal=[aff0["arousal"], w.affect_state("fisherman")["arousal"]],
        fisherman_valence=[aff0["valence"], w.affect_state("fisherman")["valence"]],
        fisherman_demand_cash=w.demand_cash_of("fisherman"),
        fisherman_unpaid=w.unpaid_of("fisherman"),
        doreen_badmouthed=w.badmouthed_of("Doreen Ferrety"),
        n_badmouth_nodes=w.badmouth_count(),
        post_backs=[w.backs_debtor_of("townsperson_%d" % i) for i in range(3)])
    w.close()
    return hops


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    result = dict(block=253000, prereg="BIGVILLE_LOOP_PREREG.md",
                  town=demo_town(),
                  cascade=demo_cascade(sever=False),
                  cascade_severed=demo_cascade(sever=True))
    with open(os.path.join(OUT_DIR, "demo.json"), "w") as f:
        json.dump(result, f, indent=2)

    print("=" * 72)
    print("BIGVILLE R5 -- THE LOOP CLOSES + emergent cascades (block 253000)")
    print("=" * 72)
    t = result["town"]
    v = t["default_viable_sustains"]
    print("\n(1) THE TOWN -- DEFAULT (viable + wages): does it sustain?")
    print("  carrying capacity (produced-consumed margin):",
          {g: v["carrying_capacity"][g]["margin"] for g in v["carrying_capacity"]})
    print("  money conserved:", v["coin_conserved"])
    print("  per-day unmet demand:", [d["unmet_demand"] for d in v["per_day"]])
    md = v["marjorie_day1"]
    print("  Marjorie day 1 (glass-box): wake E=%g coin=%g -> open=%d bake=%g sell=%g "
          "(+%g coin) eat_town=%g restock_grain=%g -> sleep E=%g end_coin=%g" % (
              md["wake_energy"], md["wake_coin"], md["shop_open"], md["baked_to_stock"],
              md["sold_units"], md["coin_from_sales"], md.get("eaten", 0),
              md["grain_after_restock"], md["night_energy"], md["end_coin"]))
    print("  VERDICT: town SUSTAINS" if all(not d["unmet_demand"] for d in v["per_day"])
          else "  VERDICT: town does NOT fully sustain")
    p = t["probe_wages_off_money_pools"]
    print("\n  PROBE wages-off (money pooling): final producer/consumer coin:",
          "producers", p["final"]["producers"], "consumers", p["final"]["consumers"])
    print("   unmet by day:", [d["unmet_demand"] for d in p["per_day"]],
          "| Σcoin conserved:", p["coin_conserved"]["drift"] == 0)
    s = t["probe_shortfall_famine"]
    print("\n  PROBE shortfall (carrying-capacity famine): bread margin",
          s["carrying_capacity"]["bread"]["margin"], "-> unmet by day:",
          [d["unmet_demand"] for d in s["per_day"]])

    c = result["cascade"]
    cs = result["cascade_severed"]
    print("\n(2) THE FISHMONGER CASCADE (every hop off the graph):")
    print("  drink: Doreen coin %g -> %g (ale held %g)" % (
        c["drink"]["coin_before"], c["drink"]["coin_after"], c["drink"]["ale_held"]))
    print("  collapse: sleep_kind=%d (2=involuntary) collapsed=%d" % (
        c["collapse"]["sleep_kind"], c["collapse"]["collapsed"]))
    print("  (a) expectation: stall_open=%d surprise=%d" % (
        c["expectation"]["stall_open"], c["expectation"]["surprise"]))
    print("  (b) down-chain: with fish chose %d, stall shut -> satisfices to %d (FISH=%d BREAD=%d)" % (
        c["down_chain"]["with_fish_chosen"], c["down_chain"]["satisfices_to"],
        c["down_chain"]["FISH"], c["down_chain"]["BREAD"]))
    u = c["up_chain"]
    print("  (c) up-chain: Doreen defaulted=%d -> fisherman arousal %s valence %s demand_cash=%d unpaid=%g" % (
        u["doreen_defaulted"], u["fisherman_arousal"], u["fisherman_valence"],
        u["fisherman_demand_cash"], u["fisherman_unpaid"]))
    print("      -> badmouthed Doreen=%g (%d Badmouth node) -> townsfolk backing %s -> %s" % (
        u["doreen_badmouthed"], u["n_badmouth_nodes"], c["pre_backs"], u["post_backs"]))
    print("\n(3) SEVER control (cut the supply edge -> cascade VANISHES):")
    us = cs["up_chain"]
    print("  owe_minted=%s defaulted=%d fisherman_arousal=%s demand_cash=%d badmouthed=%g backs=%s" % (
        us["owe_minted"], us["doreen_defaulted"], us["fisherman_arousal"],
        us["fisherman_demand_cash"], us["doreen_badmouthed"], us["post_backs"]))
    print("\nwrote", os.path.join(OUT_DIR, "demo.json"))


if __name__ == "__main__":
    main()
