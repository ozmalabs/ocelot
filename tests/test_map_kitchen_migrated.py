"""bigville R45 (block 343000): the FOOD LIFECYCLE runs on the GENERATED map. A cook prepares
a meal in a kitchen the generator placed (real fs_prepare / fs_eat firing against the
generated Station); meal quality tracks the kitchen TIER; a kitchenless house cannot cook and
eats raw (poor nutrition + illness) -- the glass-box of the social determinants of health.
Gates mirror BIGVILLE_MAP_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_map_kitchen import MapKitchen   # noqa: E402


# ------------------------------------------------------ G-cook-in-a-generated-kitchen (headline)
def test_a_cook_prepares_a_meal_in_a_generated_kitchen():
    k = MapKitchen(seed=7)
    state, quality, _ = k.cook_meal("Inn", cook_skill=0.7)
    assert state == "prepared", "the real fs_prepare fires against the GENERATED Station"
    assert quality > 0.0, "the meal has a quality (cook_skill * (1 + station.prep_power))"


# ------------------------------------------------------ G-kitchen-tier-affects-the-meal
def test_the_kitchen_tier_shapes_the_meal():
    k = MapKitchen(seed=7)
    _, q_commercial, _ = k.cook_meal("Inn", cook_skill=0.7)        # commercial kitchen (prep 1.2)
    _, q_poor, _ = k.cook_meal("house1", cook_skill=0.7)           # a poor-house hearth (prep 0.3)
    assert k.gen.has_kitchen("house1"), "house1 has a (poor) kitchen at seed 7"
    assert q_commercial > q_poor, "a better kitchen draws out a better meal from the same cook"


# ------------------------------------------------------ G-kitchenless-house-and-health (headline)
def test_a_kitchenless_house_cannot_cook_and_its_food_sickens():
    k = MapKitchen(seed=7)
    assert not k.gen.has_kitchen("house2"), "house2 has no cooking facilities at seed 7"
    state, _, raw = k.cook_meal("house2", cook_skill=0.7)
    assert state == "raw", "with no heated Station the food cannot be cooked -- it stays raw"
    poor = k.eat(raw, eater="PoorFamily")
    assert poor["illness"] > 0.0, "eating it raw brings a chance of illness"
    # contrast: a cooked meal nourishes and is safe -- income -> kitchen -> nutrition/illness
    cooked_k = MapKitchen(seed=7)
    _, _, cooked = cooked_k.cook_meal("Inn", cook_skill=0.9)
    rich = cooked_k.eat(cooked, eater="Innkeeper")
    assert rich["nutrition"] > poor["nutrition"] and rich["illness"] == 0.0, \
        "the affordance distribution (who has a kitchen) drives who eats well -- determinants of health"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_the_rules_cook_the_adapter_only_wires():
    src = open(os.path.join(_ROOT, "worlds", "bigville_map_kitchen.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    assert "bigville_foodstuff" in src, "the cooking/grading is the fs_* seed rules, composed"
    fs = json.load(open(os.path.join(_ROOT, "seeds", "bigville_foodstuff.json")))
    names = {r["name"] for r in fs["rules"]}
    assert {"fs_prepare", "fs_eat"} <= names, "the generated kitchen drives the real food rules"
