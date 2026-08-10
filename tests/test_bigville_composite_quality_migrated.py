"""bigville: COMPOSITE QUALITY = WEAKEST PART (a good is only as good as its worst ingredient).

A made good's quality is its `condition`; be_composite_quality sets it to the MINIMUM condition among
the recipe's inputs after each batch -- a cart from a worn wheel is a worn cart, a pie from stale fruit
a poor pie. Quantity is driven by skill (yield = out_qty * skill), quality by the weakest part; the two
are independent. Quality reuses `condition`, so it coheres with wear and spoilage (a made good then
wears/spoils from wherever the weakest part left it).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import BigvilleEconWorld                     # noqa: E402
from worlds.bigville_time_world import DAY                                   # noqa: E402
import domains.bigville_entities as E                                        # noqa: E402

SMELT = 7.0


def _smelter(*, ore_cond=1.0, char_cond=1.0, skill=2):
    # smelt_iron: ore 2 + charcoal 1 -> iron
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("smith", (2, 2)); w.set_skill("smith", SMELT, skill)
    w.add_recipe_shop("smelter", "smelt_iron", cell=(2, 2), keeper="smith", price=5,
                      activity=SMELT, inputs={"ore": 10, "charcoal": 10})
    w.set_input_condition("smelter", "ore", ore_cond)
    w.set_input_condition("smelter", "charcoal", char_cond)
    w.make("smelter")
    return w


# ------------------------------------------------------ G-fresh-parts-full-quality (baseline)
def test_a_good_from_sound_parts_is_full_quality():
    w = _smelter(ore_cond=1.0, char_cond=1.0)
    assert w.made_quality("smelter") == 1.0, "sound ore and charcoal -> full-quality iron"


# ------------------------------------------------------ G-weakest-part-caps-quality (headline)
def test_a_good_is_only_as_good_as_its_weakest_part():
    assert _smelter(ore_cond=0.4, char_cond=1.0).made_quality("smelter") == 0.4, "poor ore -> poor iron"
    assert _smelter(ore_cond=1.0, char_cond=0.6).made_quality("smelter") == 0.6, "poor charcoal -> the charcoal caps it"
    assert _smelter(ore_cond=0.3, char_cond=0.6).made_quality("smelter") == 0.3, "two poor parts -> the WORST of them"


# ------------------------------------------------------ G-quality-independent-of-quantity (headline)
def test_skill_drives_quantity_the_weakest_part_drives_quality():
    w = _smelter(ore_cond=0.5, char_cond=1.0, skill=3)
    assert w.stock_qty("smelter") == 3.0, "a skilled smith makes MORE (yield = skill 3)"
    assert w.made_quality("smelter") == 0.5, "but no better than the weakest part -- quality and quantity are separate"


# ------------------------------------------------------ G-contamination (headline)
def test_fresh_output_into_a_degraded_pile_cannot_refresh_it():
    w = _smelter(ore_cond=1.0, char_cond=1.0)            # one fresh batch -> iron condition 1.0
    assert w.made_quality("smelter") == 1.0
    w.eng.set_attr(w._stock["smelter"], "condition", 0.3)  # the stored pile has degraded
    w.make("smelter")                                    # add a fresh batch on top of the degraded pile
    assert w.made_quality("smelter") == 0.3, \
        "putting fresh stock on a degraded pile makes the fresh worse, not the pile better -- min, not refresh"


# ------------------------------------------------------ G-rotten-ham-fresh-bread (headline)
def test_rotten_ham_and_fresh_bread_make_a_rotten_sandwich():
    r = next(x for x in E.RECIPES if x["name"] == "make_sandwich")
    assert [i[0] for i in r["in"]] == ["ham", "bread"], "a sandwich is ham + bread"
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("Cook", (2, 2)); w.set_skill("Cook", 9.0, 1)
    w.add_recipe_shop("kitchen", "make_sandwich", cell=(2, 2), keeper="Cook", price=1,
                      activity=9.0, inputs={"ham": 5, "bread": 5})
    w.set_input_condition("kitchen", "ham", 0.2)             # the ham has gone off
    w.set_input_condition("kitchen", "bread", 1.0)           # the bread is fresh
    w.make("kitchen")
    assert w.made_quality("kitchen") == 0.2, "the sandwich assumes the LOWEST input -- a rotten sandwich"


# ------------------------------------------------------ G-the-rule-decides (source audit)
def test_composite_quality_is_a_seed_rule_over_generic_condition():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_recipe.json")))
    r = next(x for x in seed["rules"] if x["name"] == "be_composite_quality")
    logic = json.dumps([{k: r[k] for k in ("match", "where", "effects")}])
    for named in ("ore", "iron", "cart", "wheel"):
        assert named not in logic, f"the rule names no good ({named}) -- it reads generic has_input/condition"
    assert '"key": "condition"' in logic, "quality IS condition -- coheres with wear + spoilage"
