"""bigville R42 (blocks 333000/334000): the food lifecycle -- storage, spoilage, and
preparation BY A COOK (an agent, with skill) using a kitchen; plus AGENT-CHOSEN
quantization (a household divides a food quantum among its members, re-quantizable).
Gates mirror BIGVILLE_FOODSTUFF_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_foodstuff_world import BigvilleFoodstuffWorld   # noqa: E402


# ------------------------------------------------------ G-discrete-stock
def test_the_larder_holds_a_discrete_stock():
    w = BigvilleFoodstuffWorld()
    i = w.add_item("salt_fish", portions=3)
    assert w.portions(i) == 3, "the stock is a whole count of items"
    w.eat(i, "A")
    assert w.portions(i) == 2 and w.did_eat("A"), "eating draws one from the stock"
    w.eat(i, "A"); w.eat(i, "A"); w.eat(i, "A")
    assert w.portions(i) == 0 and not w.did_eat("A"), "an empty stock yields nothing to eat"


# ------------------------------------------------------ G-spoilage-rates
def test_foods_spoil_at_kind_specific_rates():
    w = BigvilleFoodstuffWorld()
    fast, slow, kept = w.add_item("fish"), w.add_item("grain"), w.add_item("salt_fish")
    w.tick(5)
    assert w.freshness(fast) < w.freshness(slow) < w.freshness(kept)


# ------------------------------------------------------ G-cold-storage-preserves
def test_cold_storage_slows_spoilage():
    warm = BigvilleFoodstuffWorld(cold=False); wi = warm.add_item("fish"); warm.tick(3)
    cold = BigvilleFoodstuffWorld(cold=True);  ci = cold.add_item("fish"); cold.tick(3)
    assert cold.freshness(ci) > warm.freshness(wi)


# ------------------------------------------------------ G-prep-needs-an-agent-not-a-kitchen (headline)
def test_preparation_needs_an_agent_and_can_happen_anywhere():
    # SEASON (add spices) on BARE HANDS -- no kitchen, no heat, no equipment: just an agent.
    w = BigvilleFoodstuffWorld()
    fish = w.add_item("fish"); t0 = w.taste(fish)
    w.add_cook("Bob", station="hands")
    w.season(fish, "Bob")                          # spices, on the ground
    assert w.taste(fish) > t0, "an agent can season food anywhere -- no kitchen required"
    assert w.state(fish) == "raw", "seasoning is not cooking (it improves taste, doesn't cook)"


# ------------------------------------------------------ G-cooking-needs-heat (headline)
def test_cooking_needs_a_heat_source_seasoning_does_not():
    cold = BigvilleFoodstuffWorld()
    g = cold.add_item("grain"); cold.add_cook("Cold", station="hands")
    cold.prepare(g, "Cold", kind="cook", station="hands")
    assert cold.state(g) == "raw", "you cannot COOK on bare hands -- cooking needs a fire/stove"
    warm = BigvilleFoodstuffWorld()
    g2 = warm.add_item("grain"); warm.add_cook("Hot", station="hearth")
    warm.prepare(g2, "Hot")                        # default station=hearth (heat)
    assert warm.state(g2) == "prepared", "at a fire the same grain cooks"


# ------------------------------------------------------ G-a-better-station-helps
def test_a_better_station_yields_a_better_meal():
    hearth = BigvilleFoodstuffWorld(); hi = hearth.add_item("grain"); hearth.add_cook("C", cook_skill=0.5); hearth.prepare(hi, "C")
    stove = BigvilleFoodstuffWorld(); stove.add_station("stove", heat=1.0, prep_power=1.2, fuel=10.0, fuel_cost=1.0)
    si = stove.add_item("grain"); stove.add_cook("C", cook_skill=0.5, station="stove"); stove.prepare(si, "C", station="stove")
    assert stove.taste(si) > hearth.taste(hi), "a better station (stove) draws out a better meal than a plain hearth"


# ------------------------------------------------------ G-raw-barely-nourishes-until-baked
def test_raw_grain_barely_feeds_until_a_cook_bakes_it():
    w = BigvilleFoodstuffWorld()
    raw = w.add_item("grain")
    w.eat(raw, "Hungry")                  # gnawing raw wheat -- eatable, but barely food
    assert 0.0 < w.nutrition("Hungry") < 1.0, "raw grain barely nourishes"
    assert w.illness("Hungry") > 0.0, "and eating it raw risks illness"
    w.add_cook("Mary", cook_skill=0.9)
    baked = w.add_item("grain"); w.prepare(baked, "Mary")
    w.eat(baked, "Fed")
    assert w.nutrition("Fed") > 3.0, "baked into bread it nourishes fully"
    assert w.illness("Fed") == 0.0, "and a fresh cooked meal carries no illness"


# ------------------------------------------------------ G-skill-determines-quality (headline)
def test_the_cooks_skill_determines_the_meal():
    good = BigvilleFoodstuffWorld(); gi = good.add_item("grain"); good.add_cook("Mary", cook_skill=0.9); good.prepare(gi, "Mary")
    poor = BigvilleFoodstuffWorld(); pj = poor.add_item("grain"); poor.add_cook("Bob", cook_skill=0.2); poor.prepare(pj, "Bob")
    assert good.taste(gi) > poor.taste(pj), "a skilled cook draws out more taste"
    # the meal records who made it (provenance)
    assert good.eng.node(good._items[gi])["attrs"].get("prepared_by") == "Mary"


# ------------------------------------------------------ G-cook-spends-effort-and-learns
def test_cooking_costs_effort_and_builds_skill():
    w = BigvilleFoodstuffWorld()
    w.add_cook("Mary", cook_skill=0.5, energy=10.0)
    c = w._cooks["Mary"]
    e0, s0 = float(w.eng.node(c)["attrs"]["energy"]), float(w.eng.node(c)["attrs"]["cook_skill"])
    g = w.add_item("grain"); w.prepare(g, "Mary")
    assert float(w.eng.node(c)["attrs"]["energy"]) < e0, "cooking spends the cook's effort (energy)"
    assert float(w.eng.node(c)["attrs"]["cook_skill"]) > s0, "and the cook learns by doing"


# ------------------------------------------------------ G-spoiled-persists-and-sickens (headline)
def test_spoiled_food_does_not_disappear_it_grades_badly_and_sickens():
    w = BigvilleFoodstuffWorld()
    f = w.add_item("fish", portions=3); w.tick(6)
    assert w.state(f) == "spoiled" and w.portions(f) == 3, \
        "spoiled food does NOT disappear -- it is still there in the larder"
    w.eat(f, "Beggar")                    # a desperate agent CAN eat it
    assert w.portions(f) == 2, "the spoiled food is eaten (a portion consumed), not vanished untouched"
    assert w.nutrition("Beggar") < 0.5, "but it is far LESS NUTRITIOUS (nutrition scales with freshness)"
    assert w.pleasantness("Beggar") < 0.0, "MORE UNPLEASANT (rot is disgusting)"
    assert w.illness("Beggar") > 0.0, "and it brings a CHANCE OF ILLNESS"
    # a fresh meal, by contrast, feeds well, pleases, and is safe
    g = BigvilleFoodstuffWorld(); gi = g.add_item("fish"); g.eat(gi, "Lord")
    assert g.nutrition("Lord") > w.nutrition("Beggar")
    assert g.pleasantness("Lord") > 0.0 and g.illness("Lord") == 0.0


# ------------------------------------------------------ G-illness-accumulates
def test_illness_accrues_over_repeated_bad_meals():
    w = BigvilleFoodstuffWorld()
    prev = 0.0
    for _ in range(3):
        it = w.add_item("fish"); w.tick(6)     # spoil it
        w.eat(it, "Wretch")
        assert w.illness("Wretch") >= prev, "illness accrues, meal after rotten meal"
        prev = w.illness("Wretch")
    assert prev > 0.0


# ------------------------------------------------------ G-agent-quantizes-the-food (headline)
def test_a_household_divides_a_food_quantum_among_its_members():
    w = BigvilleFoodstuffWorld()
    w.add_household("Poor", members=4, food=1.0)     # one loaf, four mouths
    w.add_household("Rich", members=4, food=4.0)     # four loaves, four mouths
    assert w.per_member("Poor") == 0.25, "one serving split four ways -> a quarter each"
    assert w.per_member("Rich") == 1.0, "abundance -> a whole serving each"


# ------------------------------------------------------ G-requantize (headline)
def test_a_household_can_requantize_its_food():
    w = BigvilleFoodstuffWorld()
    w.add_household("Fam", members=4, food=1.0)
    assert w.per_member("Fam") == 0.25
    w.requantize("Fam", 5)                            # a guest arrives -> split finer
    assert w.per_member("Fam") == 0.2, "the household re-quantizes -- the split is its own choice"
    w.set_food("Fam", 2.0)                            # more food, same 5 shares
    assert w.per_member("Fam") == 0.4, "scarcity/plenty scales the quantum -- finer under want"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_lifecycle():
    src = open(os.path.join(_ROOT, "worlds", "bigville_foodstuff_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_foodstuff.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"fs_spoil", "fs_rot", "fs_prepare", "fs_eat", "fs_nofood", "hq_ration"} <= names, names
    # preparation must be driven by an AGENT, not require a kitchen.
    prep = [r for r in seed["rules"] if r["name"] == "fs_prepare"][0]
    assert ["agent", "preparing", "item"] in prep["match"], "an AGENT must prepare the food"
    assert "Kitchen" not in json.dumps(prep) and "has_kitchen" not in json.dumps(prep), \
        "preparation must NOT require a kitchen -- only an agent (heat only if cooking)"
    assert "cook_skill" in json.dumps(prep), "the cook's skill must determine the meal"
    # the meal is GRADED against an eater (nutrition/illness), never hard-rejected for being bad.
    eat = [r for r in seed["rules"] if r["name"] == "fs_eat"][0]
    assert ["item", "eaten_by", "eater"] in eat["match"], "a meal is graded against an eater"
    assert "illness" in json.dumps(eat), "eating bad food risks illness (spoiled food is not rejected)"
