"""bigville R4 (block 252000) -- ECONOMY gates: production requires SKILL; LOCAL
exchange (coin<->good, hunger drops); a sparse SUPPLY NETWORK a failure propagates
along; DEBT/obligation with a creditor AFFECT FLIP on default; store hours as an
EXPECTATION (predict-and-residual) distinct from a LAW (censure). Gates mirror
BIGVILLE_ECON_PREREG.md. No economy decision lives in Python -- every produce /
sell / credit / default / open-shut / surprise is a seed rule (source-audit below).
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import (                             # noqa: E402
    BigvilleEconWorld, BREAD, GRAIN, FISH, BAIT, BAKING, FISHING, BAITING)
from worlds.bigville_time_world import DAY, NIGHT                    # noqa: E402

BAKER_CELL = (2, 2)
CUST_START = (2, 4)


# ================================================================= G-buy headline
def test_buy_stocks_the_bag_and_eating_feeds():
    """G-buy: a hungry buyer WITH coin NAVIGATES (R1) to the baker DURING opening
    hours (R3 day clock), buys bread (LOCAL exchange) -- coin down, keeper paid,
    stock down, inventory up, but hunger UNCHANGED (buying only fills the bag).
    EATING the bread is what feeds him -- then hunger drops. Every step is a rule."""
    w = BigvilleEconWorld(day_range=16)
    w.set_phase(DAY)                                    # business hours by day
    w.make_trader("baker", BAKER_CELL)
    w.set_skill("baker", BAKING, 3)                     # competent baker
    w.add_shop("bakery", good=BREAD, price=4, cell=BAKER_CELL, keeper="baker",
               activity=BAKING, input_good=GRAIN, stock=0, input_qty=2)
    w.make_trader("cust", CUST_START, coin=10, hunger_level=8, satiety=5)
    w.give_good("cust", BREAD)
    w.set_hours(1)
    w.refresh_open()                                    # keeper awake + in hours -> OPEN
    w.produce("bakery")                                 # bakes bread from grain, yield=skill
    assert w.shop_open("bakery") == 1
    assert w.stock_of("bakery") == 3, "production yield scales with skill (3)"
    assert w.input_of("bakery") == 1, "one grain consumed"
    # NAVIGATE to the baker (R1 movement)
    w.set_goal("cust", BAKER_CELL)
    for _ in range(20):
        if w.pos["cust"] == BAKER_CELL:
            break
        w.move_one("cust")
    assert w.pos["cust"] == BAKER_CELL, "buyer navigated to the baker"
    h0 = w.hunger_of("cust")
    w.buy("cust")                                       # LOCAL exchange fires
    assert w.coin_of("cust") == 6, "coin paid (10-4)"
    assert w.coin_of("baker") == 4, "keeper received the coin"
    assert w.stock_of("bakery") == 2, "one bread sold"
    assert w.inventory_of("cust", BREAD) == 1, "buyer holds the bread"
    assert w.hunger_of("cust") == h0 == 8, "buying did NOT feed him -- hunger unchanged (bread is in the bag)"
    assert w.bought_of("cust") == 1
    # now he EATS the bread -- THIS feeds him
    w.eat("cust", BREAD)
    assert w.hunger_of("cust") == 3, "eating the bread drops hunger 8->3 (fed by the meal, not the purchase)"
    assert w.inventory_of("cust", BREAD) == 0, "and the bread is eaten (consumed from the bag)"
    w.close()


# ================================================================= G-buy controls
def _colocated_baker(**shop):
    """A baker keeper co-located with a buyer at BAKER_CELL, day/open, stocked."""
    w = BigvilleEconWorld(day_range=16)
    w.set_phase(DAY)
    kw = dict(good=BREAD, price=4, cell=BAKER_CELL, keeper="baker",
              activity=BAKING, input_good=GRAIN, stock=3, input_qty=2)
    kw.update(shop)
    w.make_trader("baker", BAKER_CELL)
    w.set_skill("baker", BAKING, 3)
    w.add_shop("bakery", **kw)
    return w


def test_buy_failing_controls():
    """G-buy failing controls -- each must actually FAIL to sell:
      * no coin (credit disabled) -> no purchase, no owes edge;
      * no baker at post -> no exchange;
      * baker with no grain -> no production;
      * stall CLOSED (keeper collapsed) -> no exchange even with stock present."""
    # -- no coin, credit disabled (credit_trust 0 -> TRUST not > 0) --
    w = _colocated_baker()
    w.make_trader("poor", BAKER_CELL, coin=2, hunger_level=8, satiety=5)  # 2 < price 4
    w.give_good("poor", BREAD)
    w.refresh_open()
    w.buy("poor")
    assert w.coin_of("poor") == 2 and w.stock_of("bakery") == 3, "no coin -> no sale"
    assert w.owes_of("poor") == [], "credit disabled -> no owes edge either"
    assert w.hunger_of("poor") == 8, "hunger unchanged"
    w.close()

    # -- no baker at post: keeper started AWAY from the shop cell --
    w = BigvilleEconWorld(day_range=16)
    w.set_phase(DAY)
    w.make_trader("baker", (28, 2))                      # keeper NOT at BAKER_CELL (grass)
    w.set_skill("baker", BAKING, 3)
    w.add_shop("bakery", good=BREAD, price=4, cell=BAKER_CELL, keeper="baker",
               activity=BAKING, input_good=GRAIN, stock=3, input_qty=2)
    w.make_trader("cust", BAKER_CELL, coin=10, hunger_level=8, satiety=5)
    w.give_good("cust", BREAD)
    w.refresh_open()
    w.buy("cust")
    assert w.stock_of("bakery") == 3 and w.coin_of("cust") == 10, "keeper absent -> no sale"
    w.close()

    # -- baker with no grain: input 0 -> production cannot fire --
    w = _colocated_baker(stock=0, input_qty=0)
    w.refresh_open()
    w.produce("bakery")
    assert w.stock_of("bakery") == 0, "no grain -> no bread produced"
    w.close()

    # -- stall CLOSED (keeper collapsed) -> no exchange even with stock --
    w = _colocated_baker()
    w.make_trader("cust", BAKER_CELL, coin=10, hunger_level=8, satiety=5)
    w.give_good("cust", BREAD)
    w.set_econ("baker", collapsed=1.0)                  # keeper collapsed (R3)
    w.refresh_open()
    assert w.shop_open("bakery") == 0, "collapsed keeper -> shop shut"
    w.buy("cust")
    assert w.stock_of("bakery") == 3 and w.coin_of("cust") == 10, "shut -> no sale"
    w.close()


# ============================================= G-supply+debt (material + affect)
def _supply_town(*, fishmonger_coin, credit=True, sever=False):
    """Three-tier supply chain: fishmonger <-supplied_by- fisherman
    <-supplied_by- baitseller. Returns the world, fully seeded, day/open."""
    w = BigvilleEconWorld(day_range=16)
    w.set_phase(DAY)
    # baitseller (tier 0): sells bait, always stocked
    w.make_trader("baitseller", (28, 2), coin=0)
    w.add_shop("baitshop", good=BAIT, price=2, cell=(28, 2), keeper="baitseller",
               activity=BAITING, input_good=0, stock=10, input_qty=0)
    # fisherman (tier 1): sells FISH produced from BAIT; starts with NO coin
    w.make_trader("fisherman", (28, 3), coin=0,
                  credit_trust=(50.0 if credit else 0.0), risk_weight=100.0, sour_amount=80.0)
    w.set_skill("fisherman", FISHING, 4)
    w.add_shop("fishermanshop", good=FISH, price=5, cell=(28, 3), keeper="fisherman",
               activity=FISHING, input_good=BAIT, stock=3, input_qty=0, supplier="baitshop")
    # fishmonger (tier 2): resells FISH bought from the fisherman
    w.make_trader("fishmonger", (28, 4), coin=float(fishmonger_coin),
                  credit_trust=0.0, default_count=0.0, credit_term=1.0)
    w.add_shop("fishmongershop", good=FISH, price=6, cell=(28, 4), keeper="fishmonger",
               activity=0, input_good=FISH, stock=0, input_qty=0, supplier="fishermanshop")
    if sever:
        w.sever_supply("fishmongershop", "fishermanshop")
    w.refresh_open()
    return w


def test_supply_debt_default_and_affect_flip():
    """G-supply+debt HEADLINE. (a) MATERIAL propagation: a fishmonger with no coin
    cannot pay the fisherman -> the fisherman goes UNPAID -> cannot buy bait
    up-chain -> his fish OUTPUT falls next cycle (< a PAID fisherman's). (b) DEBT:
    a default on an up-chain credit obligation flips the CREDITOR's affect
    (arousal up / valence down) and their next credit decision (refuse). Control:
    debtor pays -> no default, no flip."""
    # ---- (a) material output-falls: PAID vs UNPAID fisherman ----
    def next_output(fishmonger_coin):
        w = _supply_town(fishmonger_coin=fishmonger_coin, credit=False)
        w.restock("fishmongershop")                     # cycle 1: pay the fisherman (if coin)
        income = w.coin_of("fisherman")
        w.restock("fishermanshop")                      # cycle 2: fisherman buys bait (needs coin)
        before = w.stock_of("fishermanshop")
        w.produce("fishermanshop")                      # produce fish from bait (if any)
        out = w.stock_of("fishermanshop") - before
        w.close()
        return income, out

    paid_income, paid_out = next_output(20)             # fishmonger flush -> pays fisherman
    unpaid_income, unpaid_out = next_output(0)          # fishmonger broke, no credit
    assert paid_income > 0 and unpaid_income == 0, (paid_income, unpaid_income)
    assert unpaid_out < paid_out, ("unpaid fisherman output must fall", unpaid_out, paid_out)
    assert unpaid_out == 0 and paid_out == 4, (unpaid_out, paid_out)  # 0 bait vs skill=4

    # ---- (b) default flips the creditor's affect + refuses further credit ----
    w = _supply_town(fishmonger_coin=0, credit=True)    # fisherman EXTENDS credit
    w.attach_creditor_affect("fisherman", concern_mag=4.0, concern_drop=3.0,
                             arousal=0.0, valence=5.0)
    w.restock("fishmongershop")                         # short -> be_restock_credit mints owe
    owes = w.owes_of("fishmonger")
    assert len(owes) == 1 and owes[0]["amount"] == 5, owes
    aff0 = w.affect_state("fisherman")
    w.world_epoch = 5                                   # advance PAST the credit term (1)
    w.tick_obligations()                                # be_default + be_default_affect
    assert w.owes_of("fishmonger")[0]["defaulted"] == 1, "obligation defaulted"
    aff1 = w.affect_state("fisherman")
    assert aff1["arousal"] > aff0["arousal"], ("creditor arousal up", aff0, aff1)
    assert aff1["valence"] < aff0["valence"], ("creditor valence down", aff0, aff1)
    assert w.credit_trust_of("fisherman") < 0, "creditor now refuses further credit"
    assert w.demand_cash_of("fisherman") == 1
    assert w.unpaid_of("fisherman") == 5, "material harm booked"
    w.close()

    # ---- control: debtor PAYS -> no default, no affect flip ----
    w = _supply_town(fishmonger_coin=0, credit=True)
    w.attach_creditor_affect("fisherman", concern_mag=4.0, concern_drop=3.0,
                             arousal=0.0, valence=5.0)
    w.restock("fishmongershop")
    w.set_econ("fishmonger", coin=20)                   # now solvent
    w.repay("fishmonger")                               # pays the obligation before term
    assert w.owes_of("fishmonger")[0]["paid"] == 1, "obligation settled"
    w.world_epoch = 5
    w.tick_obligations()
    assert w.owes_of("fishmonger")[0]["defaulted"] == 0, "paid -> no default"
    aff = w.affect_state("fisherman")
    assert aff["arousal"] == 0.0 and aff["valence"] == 5.0, "no affect flip"
    assert w.credit_trust_of("fisherman") == 50.0, "credit unchanged"
    w.close()


def test_supply_sever_edge_no_propagation():
    """G-supply+debt sever control: with the `supplied_by` edge PRESENT, the
    fishmonger's shortfall mints an up-chain credit obligation and a default flips
    the fisherman; SEVER that edge and the obligation is never minted along it ->
    no default -> no affect flip. The propagation is edge-mediated, not scripted."""
    def run(sever):
        w = _supply_town(fishmonger_coin=0, credit=True, sever=sever)
        w.attach_creditor_affect("fisherman", concern_mag=4.0, concern_drop=3.0,
                                 arousal=0.0, valence=5.0)
        w.restock("fishmongershop")
        n_owes = len(w.owes_of("fishmonger"))
        w.world_epoch = 5
        w.tick_obligations()
        aff = w.affect_state("fisherman")
        w.close()
        return n_owes, aff

    present_owes, present_aff = run(sever=False)
    severed_owes, severed_aff = run(sever=True)
    # edge present: obligation minted along it, creditor's affect flips
    assert present_owes == 1 and present_aff["arousal"] > 0, (present_owes, present_aff)
    # edge severed: nothing propagates -- no obligation, no flip
    assert severed_owes == 0, "severed supplies edge -> no up-chain obligation"
    assert severed_aff["arousal"] == 0.0 and severed_aff["valence"] == 5.0, severed_aff


# ============================================= G-expectation (surprise, NOT censure)
def test_expectation_violation_is_surprise_not_censure():
    """G-expectation: the town HOLDS 'the stall opens at 8'. A keeper who COLLAPSED
    -> stall SHUT at the due epoch -> the held prediction is VIOLATED -> a residual
    SURPRISE is registered by would-be customers (predict-and-residual). This is a
    DIFFERENT register from a LAW violation (247 censure). Control: keeper opens on
    time -> no surprise."""
    def arm(collapsed):
        w = BigvilleEconWorld(day_range=16)
        w.set_phase(DAY)
        w.make_trader("keeper", BAKER_CELL, collapsed=float(collapsed))
        w.add_shop("bakery", good=BREAD, price=4, cell=BAKER_CELL, keeper="keeper",
                   activity=BAKING, input_good=GRAIN, stock=3, input_qty=0)
        w.make_trader("cust", (2, 4))
        w.add_expectation("cust", "bakery", open_due=1)
        w.set_hours(1)
        w.refresh_open()                                # derives open + fires surprise
        out = dict(shop_open=w.shop_open("bakery"), surprise=w.surprise_count("cust"))
        w.close()
        return out

    violated = arm(collapsed=1)                         # keeper collapsed overnight
    ontime = arm(collapsed=0)                           # keeper opens on time (control)
    assert violated["shop_open"] == 0 and violated["surprise"] == 1, violated
    assert ontime["shop_open"] == 1 and ontime["surprise"] == 0, ontime

    # register-distinctness (source-audit): the expectation RULE mints only a
    # residual SURPRISE and touches NO enforcement/censure machinery (the prose
    # description may DISCUSS the distinction; the executable rules must not carry
    # it).
    exp = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_expectation.json")))
    blob = json.dumps(exp["rules"])
    assert "Surprise" in blob and "residual" in blob
    for censure_word in ("censure", "Violation", "enforce", "backs_mary", "credibility"):
        assert censure_word not in blob, f"expectation rule leaks into the law register: {censure_word}"


# ============================================= G-scale (the all-pairs trap)
def test_scale_economy_on_is_subquadratic():
    """G-scale (LOAD-BEARING): re-run the 248000 scale probe with economy ON. LOCAL
    exchange keeps realized interaction-ops SUB-QUADRATIC (fitted log-log slope <
    1.5); the deliberate global-market-clear control measures ~2.0 and the local
    arm is CI-separated below it. An economy-on ~2.0 would be a real all-pairs
    bug."""
    from worlds.bigville_econ_scale_world import BigvilleEconScaleWorld
    N_GRID = [5, 10, 15, 20, 25, 30]
    R = 20

    def ols(xs, ys):
        x = np.asarray(xs, float); y = np.asarray(ys, float)
        xm = x.mean(); ym = y.mean()
        return float(((x - xm) * (y - ym)).sum() / ((x - xm) ** 2).sum())

    def measure(arm):
        per_n = {}
        for N in N_GRID:
            vals = []
            for r in range(R):
                world = BigvilleEconScaleWorld(N, arm=arm, place_seed=252000 + N * 1000 + r)
                world.run(T=8)
                vals.append(world.mean_econ_ops())
            per_n[N] = vals
        logN = [np.log(N) for N in N_GRID]
        means = {N: float(np.mean(per_n[N])) for N in N_GRID}
        point = ols(logN, [np.log(means[N]) for N in N_GRID])
        rng = np.random.default_rng(252000 + 777)
        slopes = []
        for _ in range(2000):
            ys = [np.log(rng.choice(per_n[N], size=len(per_n[N]), replace=True).mean())
                  for N in N_GRID]
            slopes.append(ols(logN, ys))
        lo, hi = np.percentile(slopes, [2.5, 97.5])
        return point, float(lo), float(hi)

    l_slope, l_lo, l_hi = measure("local")
    a_slope, a_lo, a_hi = measure("all_pairs")
    assert l_slope < 1.5, f"economy-on local slope must be sub-quadratic: {l_slope}"
    assert 1.8 <= a_slope <= 2.2, f"all-pairs control must measure ~2.0: {a_slope}"
    assert l_hi < a_lo, f"local must be CI-separated below all-pairs: {l_hi} !< {a_lo}"


# ============================================= discipline / source-audit
def test_decisions_are_rules_not_python():
    """Source-audit: the world adapter runs NO Python rule engine and holds no
    economy decision; every decision lives in the bigville_econ_* seeds."""
    wf = open(os.path.join(_ROOT, "worlds", "bigville_econ_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "gr._match", "gr._apply"):
        assert forbidden not in wf, f"world adapter calls a rule engine: {forbidden}"
    names = set()
    for seed in ("bigville_econ_production", "bigville_econ_exchange",
                 "bigville_econ_supply", "bigville_econ_debt", "bigville_econ_expectation",
                 "bigville_econ_recipe"):   # be_produce RETIRED -> the unified recipe engine
        d = json.load(open(os.path.join(_ROOT, "seeds", seed + ".json")))
        names |= {r["name"] for r in d["rules"]}
    # PRODUCTION is now the unified recipe engine (be_meet_input/be_recipe_done), not the old be_produce
    assert {"be_meet_input", "be_recipe_done", "be_exchange", "be_credit", "be_restock",
            "be_restock_credit", "be_repay", "be_default", "be_default_affect",
            "be_shop_open", "be_shop_shut", "be_expect_surprise"} <= names, names
    assert "be_produce" not in names, "be_produce is retired -- all production runs through the recipe engine"
    # the credit-extension decision is a decision_value (trust minus risk*defaults)
    exch = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_exchange.json")))
    cr = next(r for r in exch["rules"] if r["name"] == "be_credit")
    assert "credit_trust" in json.dumps(cr) and "default_count" in json.dumps(cr)


def test_no_new_rust_and_engine_invariant():
    """No new Rust primitive: the R4 seeds compose EXISTING DSL Terms only, and the
    engine provenance asserts the INVARIANT source_match in {own, shared} (never a
    pinned md5)."""
    from domains.engine_provenance import engine_provenance
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p
    used = set()
    for seed in ("bigville_econ_production", "bigville_econ_exchange",
                 "bigville_econ_supply", "bigville_econ_debt", "bigville_econ_expectation"):
        d = json.load(open(os.path.join(_ROOT, "seeds", seed + ".json")))
        used |= set(re.findall(r'"type":\s*"([A-Z][A-Za-z]+)"', json.dumps(d)))
    known = {"Attr", "Var", "Lit", "Plus", "Minus", "Times", "Max", "Min", "Sum",
             "Lt", "Gt", "Gte", "Eq", "And", "Or", "Not", "IfThenElse", "Exists",
             "Neighbours", "NodesOfType", "Count", "Argmax"}
    assert used <= known, f"unexpected Term(s) -- new Rust? {used - known}"
