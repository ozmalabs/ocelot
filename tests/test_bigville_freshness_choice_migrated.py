"""bigville: a shopper PREFERS THE FRESHER STALL (freshness -> the buy decision).

nd_choose_good Argmaxes over Sources by urgency * preference - travel_cost; the choice value is now
also scaled by the source's FRESHNESS, so at equal urgency and cost a shopper prefers the fresher
stall, and enough staleness overrides a mild preference. Fresh sources (freshness 1.0, the default)
are unchanged, so every existing need/choice gate is undisturbed. In the integrated town the source
freshness tracks the shop's stock condition (be_spoil); here it is set directly to prove the choice.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_need_world import BigvilleNeedWorld, APPLE, BREAD, SUSTENANCE   # noqa: E402

SQUARE = (14, 8)
BAKERY = (14, 11)      # dist 3 from the square
ALEHOUSE = (17, 8)     # dist 3 -- equidistant, so the choice turns on taste + freshness, not distance


def _shop(prefs, *, apple_fresh=1.0, bread_fresh=1.0, knows=True):
    w = BigvilleNeedWorld()
    w.add_source("bakery", BREAD, BAKERY)
    w.add_source("alehouse", APPLE, ALEHOUSE)
    w.add_mover("shopper", SQUARE)
    w.set_preferences("shopper", prefs, cost_on=0.0)          # ignore distance -- isolate taste + freshness
    w.set_drive("shopper", SUSTENANCE, v_d=10.0, c_d=0.0)
    if knows:
        w.teach_degradation("shopper")                        # HELD knowledge: this shopper cares about freshness
    w.set_source_freshness("alehouse", apple_fresh)
    w.set_source_freshness("bakery", bread_fresh)
    return w.decide("shopper")["chosen_good"]


# ------------------------------------------------------ G-prefers-fresher (headline)
def test_a_shopper_prefers_the_fresher_stall():
    equal = {APPLE: 1.0, BREAD: 1.0}
    fresh_choice = _shop(equal)                              # a tie broken deterministically
    assert _shop(equal, bread_fresh=0.2) == "apple", "when the bread has gone stale, the shopper takes the fresh apple"
    assert _shop(equal, apple_fresh=0.2) == "bread", "when the apples have gone off, the shopper takes the fresh bread"


# ------------------------------------------------------ G-freshness-overrides-mild-preference (headline)
def test_staleness_can_override_a_mild_preference():
    apple_pref = {APPLE: 1.2, BREAD: 1.0}                    # mildly prefers apple
    assert _shop(apple_pref) == "apple", "fresh: the shopper follows their preference (apple)"
    assert _shop(apple_pref, apple_fresh=0.2) == "bread", "but stale apples send even an apple-lover to the bread"


# ------------------------------------------------------ G-fresh-is-unchanged (no regression)
def test_all_fresh_sources_leave_the_choice_untouched():
    # both fresh (default 1.0) -> the choice is exactly the preference-and-cost decision as before
    assert _shop({APPLE: 2.0, BREAD: 1.0}) == "apple", "a clear apple preference still picks apple when all is fresh"
    assert _shop({APPLE: 1.0, BREAD: 2.0}) == "bread", "and a clear bread preference still picks bread"


# ------------------------------------------------------ G-decision-consults-held-knowledge (headline)
def test_a_naive_shopper_who_lacks_the_knowledge_ignores_freshness():
    equal = {APPLE: 1.0, BREAD: 1.0}
    # a KNOWER's buy decision reads its held knowledge and avoids the stale stall...
    assert _shop(equal, bread_fresh=0.2, knows=True) == "apple", "the knower takes the fresh apple over stale bread"
    # ...a NAIVE shopper (no held degradation knowledge) does NOT weigh freshness at all -- the SAME
    # decision rule, consulting what THIS shopper holds, ignores the staleness and falls back to the tie.
    knower = _shop(equal, bread_fresh=0.2, knows=True)
    naive = _shop(equal, bread_fresh=0.2, knows=False)
    assert naive != knower, "the naive shopper does not avoid the stale stall -- freshness is HELD knowledge, not innate"
    assert _shop({APPLE: 1.2, BREAD: 1.0}, apple_fresh=0.2, knows=False) == "apple", \
        "and a naive apple-lover buys the stale apples anyway -- his decision never consulted freshness"


# ------------------------------------------------------ G-learns-from-eating-spoiled (headline)
def _learner_world():
    w = BigvilleNeedWorld()
    w.add_source("bakery", BREAD, BAKERY)
    w.add_source("alehouse", APPLE, ALEHOUSE)
    w.add_mover("shopper", SQUARE)
    w.set_preferences("shopper", {APPLE: 1.0, BREAD: 1.2}, cost_on=0.0)   # mildly prefers bread
    w.set_drive("shopper", SUSTENANCE, v_d=10.0, c_d=0.0)
    w.set_source_freshness("bakery", 0.2)                # the bread has gone off
    w.set_source_freshness("alehouse", 1.0)              # the apples are fresh
    return w


def test_a_naive_shopper_buys_spoiled_food_eats_it_and_learns():
    w = _learner_world()
    assert not w.knows_degradation("shopper"), "at first the shopper knows nothing of rot"
    # 1) naive: the buy decision ignores freshness -> he buys the STALE bread (follows his preference)
    assert w.decide("shopper")["chosen_good"] == "bread", "naive -> buys the stale bread"
    # 2) he eats the spoiled bread -> the bad experience TEACHES him (self-taught, no teacher)
    assert w.eat("shopper", 0.2) is True and w.knows_degradation("shopper"), "eating spoiled food -> he LEARNS"
    # 3) now his SAME buy decision consults the freshly-held knowledge -> he avoids the stale stall
    assert w.decide("shopper")["chosen_good"] == "apple", "having learned, he now takes the fresh apple"


def test_the_learned_agent_does_not_buy_spoiled_again_but_will_under_necessity():
    w = _learner_world()
    assert w.decide("shopper")["chosen_good"] == "bread", "day 1, naive: buys the stale bread"
    w.eat("shopper", 0.2)                                     # learns
    # having learned, he avoids the stale stall day after day -- not a one-off
    for _ in range(3):
        w.set_drive("shopper", SUSTENANCE, v_d=10.0, c_d=0.0)
        assert w.decide("shopper")["chosen_good"] == "apple", "learned: never buys the stale bread again"
    # BUT the belief is a WEIGHTING, not a prohibition: with only spoiled food left, a hungry man buys it
    w.set_source_freshness("alehouse", 0.2)                   # now BOTH stalls are stale
    w.set_drive("shopper", SUSTENANCE, v_d=10.0, c_d=0.0)
    assert w.decide("shopper")["chosen_good"] == "bread", \
        "only spoiled food available -> he still buys (his preference) -- necessity over the learned aversion"


def test_a_good_meal_teaches_nothing():
    w = _learner_world()
    assert w.eat("shopper", 1.0) is False and not w.knows_degradation("shopper"), \
        "eating FRESH food is no lesson -- learning comes from the bad consequence, not from eating"


def test_learning_is_a_surprise_that_mints_an_axis_and_a_belief():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_degradation_learn.json")))
    r = next(x for x in seed["rules"] if x["name"] == "dk_learn")
    assert ["agent", "ate", "meal"] in r["match"], "learning keys on having EATEN a meal"
    where = json.dumps(r["where"])
    assert "expected_feeling" in where and "feeling" in where, "it triggers on a SURPRISE (felt worse than expected)"
    effs = json.dumps(r["effects"])
    assert '"Axis"' in effs, "it MINTS A NEW AXIS from the feeling (arbitrary, not a named concept)"
    assert '"Belief"' in effs and '"holds_belief"' in effs, "and forms a BELIEF the agent holds"
    assert "DegradationLaw" not in effs, "no pre-named law -- the knowledge is discovered, not acquired by name"


def test_the_belief_is_weighted_by_how_surprising_it_was():
    w = _learner_world()
    w.decide("shopper"); w.eat("shopper", 0.2)               # felt 0.2 vs expected 1.0 -> surprise 0.8
    belief = list(w.eng.neighbours(w._movers["shopper"], "holds_belief"))[0]
    a = w.eng.node(belief)["attrs"]
    assert a["valence"] == -1.0 and round(a["weight"], 4) == 0.8, "spoiled is bad, weighted by the surprise (0.8)"
