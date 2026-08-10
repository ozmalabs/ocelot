"""bigville_econ_run -- R4 (block 252000) glass-box DEMONSTRATION of the economy.

Reads the whole economy off the graph, nothing scripted: (1) a hungry buyer with
coin navigates to the baker during opening hours and buys bread (LOCAL exchange),
hunger drops; and (2) the fishmonger CASCADE -- a fishmonger short of coin buys
fish from the fisherman ON CREDIT, DEFAULTS past term, and the default flips the
fisherman's affect + his next credit decision (economy -> affect -> behaviour),
while the UNPAID fisherman's fish output falls next cycle vs a PAID one. Every hop
is a rule verdict read back from the substrate. Writes results/bigville_econ/demo.json.
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

from worlds.bigville_econ_world import (                        # noqa: E402
    BigvilleEconWorld, BREAD, GRAIN, FISH, BAIT, BAKING, FISHING, BAITING)
from worlds.bigville_time_world import DAY                      # noqa: E402

OUT_DIR = os.path.join(_ROOT, "results", "bigville_econ")


def demo_buy():
    w = BigvilleEconWorld(day_range=16)
    w.set_phase(DAY)
    w.make_trader("baker", (2, 2))
    w.set_skill("baker", BAKING, 3)
    w.add_shop("bakery", good=BREAD, price=4, cell=(2, 2), keeper="baker",
               activity=BAKING, input_good=GRAIN, stock=0, input_qty=2)
    w.make_trader("cust", (2, 4), coin=10, hunger_level=8, satiety=5)
    w.give_good("cust", BREAD)
    w.set_hours(1); w.refresh_open(); w.produce("bakery")
    w.set_goal("cust", (2, 2))
    hops = []
    for _ in range(20):
        if w.pos["cust"] == (2, 2):
            break
        hops += w.move_one("cust")
    produced = w.stock_of("bakery")           # baked before navigation (yield=skill=3)
    before = dict(coin=w.coin_of("cust"), hunger=w.hunger_of("cust"),
                  stock=w.stock_of("bakery"))
    w.buy("cust")
    out = dict(
        produced=produced,
        shop_open=w.shop_open("bakery"), navigated_to=list(w.pos["cust"]),
        n_hops=len(hops),
        before=before,
        after=dict(coin=w.coin_of("cust"), hunger=w.hunger_of("cust"),
                   stock=w.stock_of("bakery"), keeper_coin=w.coin_of("baker"),
                   bread_held=w.inventory_of("cust", BREAD)))
    w.close()
    return out


def demo_cascade():
    """The fishmonger cascade + the material output-falls, read off the graph."""
    def supply(fishmonger_coin, credit):
        w = BigvilleEconWorld(day_range=16)
        w.set_phase(DAY)
        w.make_trader("baitseller", (28, 2), coin=0)
        w.add_shop("baitshop", good=BAIT, price=2, cell=(28, 2), keeper="baitseller",
                   activity=BAITING, input_good=0, stock=10, input_qty=0)
        w.make_trader("fisherman", (28, 3), coin=0,
                      credit_trust=(50.0 if credit else 0.0), risk_weight=100.0,
                      sour_amount=80.0)
        w.set_skill("fisherman", FISHING, 4)
        w.add_shop("fishermanshop", good=FISH, price=5, cell=(28, 3), keeper="fisherman",
                   activity=FISHING, input_good=BAIT, stock=3, input_qty=0,
                   supplier="baitshop")
        w.make_trader("fishmonger", (28, 4), coin=float(fishmonger_coin),
                      credit_trust=0.0, credit_term=1.0)
        w.add_shop("fishmongershop", good=FISH, price=6, cell=(28, 4),
                   keeper="fishmonger", activity=0, input_good=FISH, stock=0,
                   input_qty=0, supplier="fishermanshop")
        w.refresh_open()
        return w

    # -- material output falls: PAID vs UNPAID fisherman --
    def output(coin):
        w = supply(coin, credit=False)
        w.restock("fishmongershop")
        income = w.coin_of("fisherman")
        w.restock("fishermanshop")
        b = w.stock_of("fishermanshop"); w.produce("fishermanshop")
        out = w.stock_of("fishermanshop") - b
        w.close()
        return dict(fisherman_income=income, next_output=out)

    paid = output(20)
    unpaid = output(0)

    # -- default flips the creditor's affect + refuses further credit --
    w = supply(0, credit=True)
    w.attach_creditor_affect("fisherman", concern_mag=4.0, concern_drop=3.0,
                             arousal=0.0, valence=5.0)
    w.restock("fishmongershop")               # short -> credit -> owe minted
    owe = w.owes_of("fishmonger")
    aff0 = w.affect_state("fisherman"); trust0 = w.credit_trust_of("fisherman")
    w.world_epoch = 5; w.tick_obligations()   # past term -> default -> affect flip
    default = dict(
        owe_minted=owe, owe_after=w.owes_of("fishmonger"),
        creditor_affect_before=dict(arousal=aff0["arousal"], valence=aff0["valence"]),
        creditor_affect_after=dict(arousal=w.affect_state("fisherman")["arousal"],
                                   valence=w.affect_state("fisherman")["valence"]),
        creditor_credit_trust_before=trust0,
        creditor_credit_trust_after=w.credit_trust_of("fisherman"),
        creditor_demand_cash=w.demand_cash_of("fisherman"),
        creditor_unpaid=w.unpaid_of("fisherman"))
    w.close()

    # -- sever control --
    def sever(do):
        w = supply(0, credit=True)
        w.attach_creditor_affect("fisherman", concern_mag=4.0, concern_drop=3.0,
                                 arousal=0.0, valence=5.0)
        if do:
            w.sever_supply("fishmongershop", "fishermanshop")
        w.restock("fishmongershop")
        n = len(w.owes_of("fishmonger"))
        w.world_epoch = 5; w.tick_obligations()
        a = w.affect_state("fisherman")
        w.close()
        return dict(owes=n, creditor_arousal=a["arousal"])

    return dict(material_output_falls=dict(paid=paid, unpaid=unpaid),
                default_affect_flip=default,
                sever_control=dict(edge_present=sever(False), edge_severed=sever(True)))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    result = dict(block=252000, prereg="BIGVILLE_ECON_PREREG.md",
                  buy=demo_buy(), cascade=demo_cascade())
    with open(os.path.join(OUT_DIR, "demo.json"), "w") as f:
        json.dump(result, f, indent=2)

    b = result["buy"]
    print("=" * 68)
    print("BIGVILLE R4 ECONOMY -- glass-box read-off (block 252000)")
    print("=" * 68)
    print("\nG-BUY (navigate -> local exchange):")
    print("  baked %d bread (yield=skill); shop open=%d; navigated %d hops to %s"
          % (b["produced"], b["shop_open"], b["n_hops"], b["navigated_to"]))
    print("  buyer coin %g -> %g ; keeper paid %g ; stock %g -> %g ; hunger %g -> %g ; bread held %g"
          % (b["before"]["coin"], b["after"]["coin"], b["after"]["keeper_coin"],
             b["before"]["stock"], b["after"]["stock"], b["before"]["hunger"],
             b["after"]["hunger"], b["after"]["bread_held"]))

    c = result["cascade"]
    m = c["material_output_falls"]
    print("\nG-SUPPLY (material output falls, up-chain propagation):")
    print("  PAID fisherman: income=%g -> next fish output=%g"
          % (m["paid"]["fisherman_income"], m["paid"]["next_output"]))
    print("  UNPAID fisherman: income=%g -> next fish output=%g  (falls: no coin -> no bait)"
          % (m["unpaid"]["fisherman_income"], m["unpaid"]["next_output"]))
    d = c["default_affect_flip"]
    print("\nG-DEBT (default -> creditor affect flip):")
    print("  owe minted:", d["owe_minted"])
    print("  after default: defaulted=%d ; fisherman arousal %g -> %g ; valence %g -> %g"
          % (d["owe_after"][0]["defaulted"],
             d["creditor_affect_before"]["arousal"], d["creditor_affect_after"]["arousal"],
             d["creditor_affect_before"]["valence"], d["creditor_affect_after"]["valence"]))
    print("  credit_trust %g -> %g (now refuses) ; demand_cash=%d ; unpaid harm=%g"
          % (d["creditor_credit_trust_before"], d["creditor_credit_trust_after"],
             d["creditor_demand_cash"], d["creditor_unpaid"]))
    s = c["sever_control"]
    print("\nG-SEVER (propagation is edge-mediated):")
    print("  edge PRESENT: owes=%d creditor_arousal=%g   edge SEVERED: owes=%d creditor_arousal=%g"
          % (s["edge_present"]["owes"], s["edge_present"]["creditor_arousal"],
             s["edge_severed"]["owes"], s["edge_severed"]["creditor_arousal"]))
    print("\nwrote", os.path.join(OUT_DIR, "demo.json"))


if __name__ == "__main__":
    main()
