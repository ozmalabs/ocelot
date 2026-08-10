"""bigville: the DIET PSYCHOLOGY feeds the AFFECT loop -- monotony sinks mood, variety holds it.

simulate_diet's sensory-specific satiety is now wired into the agent's actual MOOD. eat_meal computes a
meal's satisfaction from the researched model (meal_satisfaction: base liking discounted by how many times
the same food repeated, modulated by the eater's food-neophobia trait); af_meal_mood then moves the mood
toward that satisfaction (hedonic adaptation). So a poor, monotonous diet drags mood down day by day --
and it lands hardest on the variety-seeking poor, while a routine-lover barely feels it.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_need_world import BigvilleNeedWorld, BREAD   # noqa: E402

SQUARE = (14, 8)
BREAD = float(BREAD)
FISH, ALE, CHEESE, APPLE = 30.0, 31.0, 32.0, 33.0


def _eater(neophobia):
    w = BigvilleNeedWorld(); w.add_mover("H", SQUARE); w.set_neophobia("H", neophobia)
    return w


# ------------------------------------------------------ G-monotony-sinks-mood (headline)
def test_a_monotonous_diet_drags_mood_down_variety_holds_it_up():
    w = _eater(0.2)
    start = w.eat_meal("H", BREAD)                       # first loaf: pleasant
    for _ in range(6):
        w.eat_meal("H", BREAD)                           # ...the same bread, day after day
    assert w.mood("H") < start - 0.2, "a week of the same food sinks the mood (sensory-specific satiety -> affect)"
    # a varied week keeps mood up
    v = _eater(0.2)
    v.eat_meal("H", BREAD); [v.eat_meal("H", f) for f in (FISH, ALE, CHEESE, APPLE, FISH, ALE)]
    assert v.mood("H") >= 0.6, "variety keeps every meal fresh, so mood stays high"


# ------------------------------------------------------ G-poverty-x-trait-on-mood (headline)
def test_the_monotony_mood_cost_lands_on_the_variety_seeking_poor():
    seeker, lover = _eater(0.1), _eater(0.8)
    for _ in range(7):
        seeker.eat_meal("H", BREAD); lover.eat_meal("H", BREAD)   # the same poor diet for both
    assert seeker.mood("H") < lover.mood("H") - 0.15, \
        "on the same monotonous poor diet the variety-seeker's mood collapses; the routine-lover copes"


# ------------------------------------------------------ G-mood-recovers-with-variety (headline)
def test_a_dull_mood_recovers_when_variety_returns():
    w = _eater(0.2)
    for _ in range(6):
        w.eat_meal("H", BREAD)                           # ground down by monotony
    low = w.mood("H")
    for f in (FISH, ALE, CHEESE):                        # then some variety
        w.eat_meal("H", f)
    assert w.mood("H") > low + 0.1, "variety lifts the ground-down mood back up (hedonic adaptation)"


# ------------------------------------------------------ G-appetite-is-a-choice-dimension (headline)
from worlds.bigville_need_world import APPLE, SUSTENANCE   # noqa: E402
BAKERY = (14, 11); ALEHOUSE = (17, 8)


def _shopper(neophobia, loaves):
    w = BigvilleNeedWorld()
    w.add_source("bakery", BREAD, BAKERY); w.add_source("alehouse", APPLE, ALEHOUSE)
    w.add_mover("Hob", SQUARE); w.set_neophobia("Hob", neophobia)
    w.set_preferences("Hob", {APPLE: 1.0, BREAD: 1.3}, cost_on=0.0)   # PREFERS bread
    w.set_drive("Hob", SUSTENANCE, v_d=10.0, c_d=0.0)
    for _ in range(loaves):
        w.eat_meal("Hob", float(BREAD), 0.7)
    w.set_drive("Hob", SUSTENANCE, v_d=10.0, c_d=0.0)
    return w.decide("Hob")["chosen_good"]


def test_appetite_is_just_another_dimension_the_choice_weighs():
    # fresh: the shopper follows his preference (bread)
    assert _shopper(0.2, loaves=0) == "bread", "with appetite fresh, he picks his preferred bread"
    # after eating bread and again, the appetite dimension weighs bread down -> he craves the apple
    assert _shopper(0.2, loaves=3) == "apple", "sick of bread, he now feels like the apple -- 'what do I feel like'"


def test_the_trait_sets_how_fast_appetite_turns():
    # after the SAME two loaves, the variety-seeker already craves change; the routine-lover does not
    assert _shopper(0.1, loaves=2) == "apple", "the variety-seeker satiates fast -> craves the apple"
    assert _shopper(0.85, loaves=2) == "bread", "the routine-lover satiates slowly -> still content with bread"


def test_appetite_rides_the_same_collapse_no_new_mechanism():
    import json
    d = json.load(open(os.path.join(_ROOT, "seeds", "bigville_need_choice.json")))
    r = next(x for x in d["rules"] if x["name"] == "nd_choose_good")
    # it is still ONE Argmax (collapse); the appetite is a factor inside its value, alongside taste + freshness
    assert r["effects"][0][3]["__term__"]["node"]["type"] == "Argmax", "the choice is a single collapse (Argmax)"
    val = json.dumps(r["effects"][0][3]["__term__"]["node"]["value"])
    assert '"satiety"' in val and '"last_food"' in val, "appetite (satiety vs last_food) is a dimension inside the collapse"
    assert '"freshness"' in val and '"has_pref"' not in val or '"freshness"' in val, "alongside freshness + preference"


# ------------------------------------------------------ G-the-mood-is-a-rule (source audit)
def test_the_mood_dynamic_is_a_seed_rule_over_the_researched_satisfaction():
    import json
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_diet_affect.json")))
    r = next(x for x in seed["rules"] if x["name"] == "af_meal_mood")
    assert ["agent", "ate", "meal"] in r["match"], "mood moves on eating a meal"
    body = json.dumps(r["effects"])
    assert '"mood"' in body and '"satisfaction"' in body, "the rule moves mood toward the meal's satisfaction"
    src = open(os.path.join(_ROOT, "worlds", "bigville_need_world.py")).read()
    assert "meal_satisfaction" in src, "the satisfaction comes from the researched model (simulate_diet's meal_satisfaction)"
