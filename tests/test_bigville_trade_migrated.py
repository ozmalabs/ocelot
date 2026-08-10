"""bigville: TRADE IS TWO ACTIONS -- a buyer PROPOSES, a seller DECIDES; and it happens WHERE THEY MEET.

A trade is not one atomic act. The buyer proposes an offer (from its expectation of who has the good); the
SELLER then decides -- accept (has it, will sell), decline (has it, won't), or the offer goes UNMET and the
buyer is SURPRISED because its expectation was wrong. And it is CO-LOCATED: you trade with a person where
they are -- you go to them (not necessarily into a shop; the person's place). A friend sharing is a seller
at price 0. These mechanism tests place buyer and seller together (they have met); the WALKING there is
tested in the unified-reasoning / delegation suites.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import BigvilleEconWorld, BREAD   # noqa: E402
from worlds.bigville_time_world import DAY                        # noqa: E402

MARKET = (14, 8)      # where buyer and seller meet
FETCH = 1.0


def _pair(*, baker_bread=5, price=1, willing=True, coin=20, together=True):
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", MARKET, coin=0)
    w.stock_person("baker", BREAD, baker_bread, sell_price=price, willing=willing)
    # the customer is WITH the baker (they have met) unless a test wants them apart
    w.make_trader("cust", MARKET if together else (20, 10), coin=coin, hunger_level=0, satiety=5)
    w.expect_source("cust", BREAD, "baker"); w.set_plan("cust", horizon=0)
    w.want_done("cust", FETCH, good=BREAD)          # the buyer wants one bread
    w.set_alive("cust", True)
    return w


# ------------------------------------------------------ G-trade-is-two-sided (headline)
def test_a_buyer_proposes_and_the_seller_accepts():
    w = _pair(baker_bread=5, price=1)
    w.run_ticks(2)                                    # the buyer proposes to the co-located baker; it decides
    assert w.offer_status("cust") == 1, "the seller ACCEPTED the offer (its own decision)"
    assert w.inventory_of("cust", BREAD) == 1, "the good moved to the buyer"
    assert w.inventory_of("baker", BREAD) == 4, "out of the seller's hands"
    assert w.coin_of("cust") == 19 and w.coin_of("baker") == 1, "coin moved the other way, at the seller's price"


def test_the_seller_can_decline_even_holding_the_good():
    w = _pair(baker_bread=5, willing=False)           # the baker has bread but won't sell
    w.run_ticks(2)
    assert w.offer_status("cust") == -2, "the seller DECLINED -- trade needs the seller's yes, it is two-sided"
    assert w.inventory_of("cust", BREAD) == 0 and w.inventory_of("baker", BREAD) == 5, "no transfer"


# ------------------------------------------------------ G-expectation-violated-surprises (headline)
def test_an_unmet_expectation_surprises_the_buyer_and_weakens_it():
    w = _pair(baker_bread=0)                           # the baker is OUT of bread
    exp0 = _expect_confidence(w, "cust")
    w.run_ticks(2)
    assert w.offer_status("cust") == -1, "the offer went unmet"
    assert w.was_surprised("cust"), "the buyer is SURPRISED -- it expected the baker to have bread"
    assert _expect_confidence(w, "cust") < exp0, "and its expectation of that source is weakened"


def _expect_confidence(w, agent):
    exps = list(w.eng.neighbours(w._movers[agent], "expects"))
    return float(w.eng.node(exps[0])["attrs"].get("confidence", 0.0)) if exps else 0.0


# ------------------------------------------------------ G-a-friend-sharing-is-a-seller-at-zero (headline)
def test_a_friend_can_share_a_seller_at_price_zero():
    w = _pair(baker_bread=3, price=0)                  # "the baker" here shares for free -- a friend
    w.run_ticks(2)
    assert w.offer_status("cust") == 1 and w.inventory_of("cust", BREAD) == 1, "a friend shares -- a trade at price 0"
    assert w.coin_of("cust") == 20, "no coin changed hands -- sharing is the zero-price case of the same trade"


# ------------------------------------------------------ G-co-location-required (headline; the map)
def test_you_must_be_WITH_the_seller_to_trade():
    w = _pair(baker_bread=5, together=False)           # buyer starts AWAY from the seller
    assert w.pos["cust"] != w.pos["baker"], "buyer and seller are in different places"
    w.run_ticks(1)
    assert w.offer_status("cust") is None or w.offer_status("cust") == 0 or w.inventory_of("cust", BREAD) == 0, \
        "one tick is not enough -- the buyer has not reached the seller yet"
    w.run_ticks(8)                                     # give it time to WALK there
    assert w.inventory_of("cust", BREAD) == 1, "having walked to the seller, the trade completes -- you go to whom you trade with"


# ------------------------------------------------------ G-two-decisions (source audit)
def test_the_proposal_and_the_acceptance_are_separate_rules():
    pursuit = json.load(open(os.path.join(_ROOT, "seeds", "bigville_pursuit.json")))
    propose = next(x for x in pursuit["rules"] if x["name"] == "pu_at_source")   # arriving = propose a trade
    assert ["add_edge", "agent", "offers", "offer"] in propose["effects"], "on arrival the buyer PROPOSES an Offer"
    trade = json.load(open(os.path.join(_ROOT, "seeds", "bigville_trade.json")))
    names = {r["name"] for r in trade["rules"]}
    assert {"tr_accept", "tr_decline", "tr_surprise"} <= names, "action 2 is the SELLER's separate decision (+ surprise)"
    acc = next(x for x in trade["rules"] if x["name"] == "tr_accept")
    assert ["buyer", "is_at", "cell"] in acc["match"] and ["seller", "is_at", "cell"] in acc["match"], \
        "acceptance requires buyer and seller to be CO-LOCATED -- the trade happens where they meet"
