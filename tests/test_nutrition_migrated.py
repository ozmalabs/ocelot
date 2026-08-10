"""bigville R41 (block 332000): nutrition (density, variety, deficiency) + taste/spice + ale
(body & mind). Gates mirror BIGVILLE_NUTRITION_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_nutrition_world import BigvilleNutritionWorld   # noqa: E402


# ------------------------------------------------------ G-nutritional-density
def test_foods_differ_in_nutritional_density():
    bread = BigvilleNutritionWorld(); bread.add_agent("A"); bread.eat("A", "bread")
    gruel = BigvilleNutritionWorld(); gruel.add_agent("B"); gruel.eat("B", "gruel")
    assert bread.last_meal_energy("A") > gruel.last_meal_energy("B"), \
        "a denser food restores more energy per meal"


# ------------------------------------------------------ G-variety-matters (specific satiety)
def test_repeating_a_food_yields_diminishing_returns():
    w = BigvilleNutritionWorld(); w.add_agent("C")
    meals = []
    for _ in range(4):
        w.eat("C", "fish"); meals.append(w.last_meal_energy("C"))
    assert meals[-1] < meals[0], f"monotony erodes the reward of a repeated food: {meals}"
    # a varied diet keeps every meal satisfying (each new kind resets monotony)
    v = BigvilleNutritionWorld(); v.add_agent("D")
    varied = []
    for k in ("fish", "bread", "fish", "bread"):
        v.eat("D", k); varied.append(v.last_meal_energy("D"))
    assert all(varied[i] >= meals[-1] for i in range(len(varied))), \
        f"variety keeps meals satisfying: {varied}"


# ------------------------------------------------------ G-deficiency-from-imbalance
def test_a_diet_missing_protein_accrues_deficiency():
    poor = BigvilleNutritionWorld(); poor.add_agent("E")
    for _ in range(5):
        poor.eat("E", "bread"); poor.tick()      # energy-rich, protein-poor
    assert poor.deficiency("E") > 0.0, "a protein-poor diet accrues deficiency"
    good = BigvilleNutritionWorld(); good.add_agent("F")
    for _ in range(5):
        good.eat("F", "fish"); good.tick()        # protein-sufficient
    assert good.deficiency("F") == 0.0, "a protein-sufficient diet stays healthy"
    assert poor.mood("E") < good.mood("F"), "deficiency drags mood down"


# ------------------------------------------------------ G-ale-is-dual (headline)
def test_ale_feeds_the_body_and_the_mind():
    w = BigvilleNutritionWorld(); w.add_agent("D")
    w.eat("D", "ale"); w.tick()
    assert w.energy("D") > 0.0, "ale gives calories (body)"
    assert w.intoxication("D") > 0.0, "and intoxicates (mind)"
    assert w.mood("D") > 0.0, "intoxication lifts mood"
    assert w.focus("D") < 1.0, "and impairs focus"


# ------------------------------------------------------ G-ale-is-empty-calories
def test_ale_is_empty_calories():
    w = BigvilleNutritionWorld(); w.add_agent("G")
    for _ in range(5):
        w.eat("G", "ale"); w.tick()
    assert w.energy("G") > 0.0, "ale sustains energy"
    assert w.protein("G") == 0.0 and w.deficiency("G") > 0.0, \
        "but supplies no protein -> deficiency still accrues (ale feeds the body poorly)"


# ------------------------------------------------------ G-spice-buys-taste-and-mood (headline)
def test_spice_buys_taste_which_lifts_mood():
    plain = BigvilleNutritionWorld(); plain.add_agent("P", spice_stock=3.0)
    plain.eat("P", "gruel")
    spiced = BigvilleNutritionWorld(); spiced.add_agent("S", spice_stock=3.0)
    spiced.eat("S", "gruel", spiced=True)
    assert spiced.mood("S") > plain.mood("P"), "a spiced meal is more enjoyable -> higher mood (spice is FOR taste)"
    assert spiced.spice_stock("S") == 2.0, "spicing consumes a spice unit"
    assert plain.spice_stock("P") == 3.0, "an unspiced meal spends none"


# ------------------------------------------------------ G-spice-rescues-monotony
def test_spice_rescues_a_monotonous_diet():
    """Even the most monotonous food, spiced, still pleases -- pleasure is decoupled from the
    energy-monotony, so spice makes a boring diet bearable."""
    w = BigvilleNutritionWorld(); w.add_agent("M", spice_stock=10.0)
    for _ in range(4):
        w.eat("M", "gruel")                       # build heavy monotony (energy reward craters)
    bored_energy = w.last_meal_energy("M")
    w.eat("M", "gruel", spiced=True)              # 5th gruel, but spiced
    assert w.last_meal_energy("M") <= bored_energy + 1e-9, "the energy reward is still monotony-eroded"
    assert w.mood("M") > 0.3, "yet the spiced meal is a genuine pleasure (mood up)"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_nutrition():
    src = open(os.path.join(_ROOT, "worlds", "bigville_nutrition_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_nutrition.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"nu_eat", "nu_metabolize", "nu_deficiency", "nu_psych"} <= names, names
