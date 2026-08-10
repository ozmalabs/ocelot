"""bigville: N-INPUT CATALOG-RECIPE PRODUCTION in the living economy (goods port step 2).

The abstract be_produce consumes ONE input. be_meet_input / be_recipe_done / be_reset_input port the
rich stack's an_meet/an_done checklist into the living econ: a shop produces via its real CATALOG
recipe -- consuming ALL N required inputs (all-or-nothing) then minting the output proportional to
skill. A shop's recipe (output + N inputs + need_qtys) is read from bigville_entities; adding a real
multi-ingredient trade is a catalog edit. be_produce is untouched (distinct make_armed flag).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import BigvilleEconWorld                    # noqa: E402
from worlds.bigville_time_world import DAY                                  # noqa: E402
import domains.bigville_entities as E                                       # noqa: E402

SMELT = 7.0   # a fresh activity code for the smelter


def _smelter(*, ore=4, charcoal=2, skill=1):
    # smelt_iron: ore 2 + charcoal 1 -> iron 1 -- a genuine 2-input catalog recipe
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("smith", (2, 2)); w.set_skill("smith", SMELT, skill)
    w.add_recipe_shop("smelter", "smelt_iron", cell=(2, 2), keeper="smith", price=5,
                      activity=SMELT, inputs={"ore": ore, "charcoal": charcoal})
    return w


# ------------------------------------------------------ G-all-inputs-consumed (headline)
def test_a_recipe_shop_consumes_all_n_inputs_and_makes_the_output():
    w = _smelter(ore=4, charcoal=2, skill=1)
    assert w.stock_qty("smelter") == 0.0
    w.make("smelter")
    assert w.recipe_input_qty("smelter", "ore") == 2.0, "one make consumed the recipe's 2 ore"
    assert w.recipe_input_qty("smelter", "charcoal") == 1.0, "AND its 1 charcoal (all N inputs)"
    assert w.stock_qty("smelter") == 1.0, "and minted iron (yield = skill 1) -- the CATALOG recipe drove it"
    w.make("smelter")
    assert w.stock_qty("smelter") == 2.0 and w.recipe_input_qty("smelter", "ore") == 0.0, "a second batch empties the ore"


# ------------------------------------------------------ G-all-or-nothing (headline)
def test_short_one_ingredient_consumes_nothing():
    w = _smelter(ore=4, charcoal=0)                     # plenty of ore, no charcoal
    w.make("smelter")
    assert w.stock_qty("smelter") == 0.0, "missing an ingredient -> no output"
    assert w.recipe_input_qty("smelter", "ore") == 4.0, "and the ore is UNTOUCHED -- all-or-nothing, no waste"


# ------------------------------------------------------ G-yield-scales-with-skill (headline)
def test_output_scales_with_the_keepers_skill():
    w = _smelter(ore=10, charcoal=10, skill=3)
    w.make("smelter")
    assert w.stock_qty("smelter") == 3.0, "a more skilled smith smelts more per batch (yield = skill)"
    assert w.recipe_input_qty("smelter", "ore") == 8.0, "still one recipe's worth of inputs consumed"


# ------------------------------------------------------ G-abstract-be_produce-untouched (no regression)
def test_the_one_input_be_produce_is_not_disturbed():
    from worlds.bigville_econ_world import BREAD, GRAIN, BAKING
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("baker", (2, 2)); w.set_skill("baker", BAKING, 3)
    w.add_shop("bakery", good=BREAD, price=4, cell=(2, 2), keeper="baker",
               activity=BAKING, input_good=GRAIN, stock=0, input_qty=2)
    w.refresh_open(); w.produce("bakery")              # the OLD 1-input path
    assert w.stock_qty("bakery") == 3.0, "be_produce still works -- make_armed and produce_armed never cross-fire"


# ------------------------------------------------------ G-y-tools-gate-and-wear (headline)
FORGE = 8.0


def _smithy(*, hammer=1.0, iron=5, charcoal=5, skill=1):
    # forge_knife: iron 1 + charcoal 1, TOOL = hammer -> knife
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("smith", (2, 2)); w.set_skill("smith", FORGE, skill)
    w.add_recipe_shop("smithy", "forge_knife", cell=(2, 2), keeper="smith", price=5,
                      activity=FORGE, inputs={"iron": iron, "charcoal": charcoal}, tools={"hammer": hammer})
    return w


def test_a_recipe_tool_is_required_and_wears():
    w = _smithy(hammer=1.0)
    assert w.recipe_tool_condition("smithy", "hammer") == 1.0
    w.make("smithy")
    assert w.stock_qty("smithy") == 1.0, "with iron, charcoal AND a hammer, the smith forges a knife"
    assert w.recipe_tool_condition("smithy", "hammer") < 1.0, "and the hammer wore (Y-tools wear, like the press)"


def test_a_broken_tool_blocks_the_batch_and_wastes_no_inputs():
    w = _smithy(hammer=0.0, iron=5)                    # the hammer is worn out
    w.make("smithy")
    assert w.stock_qty("smithy") == 0.0, "no working hammer -> no knife (the TOOL gates the batch)"
    assert w.recipe_input_qty("smithy", "iron") == 5.0, "and the iron is untouched -- all-or-nothing over inputs AND tools"


def test_a_tool_wears_to_breaking_then_stops_production():
    w = _smithy(hammer=0.08, iron=50, charcoal=50)     # wear_rate 0.05 -> good for 2 batches
    made = 0
    for _ in range(5):
        before = w.stock_qty("smithy"); w.make("smithy")
        if w.stock_qty("smithy") > before:
            made += 1
    assert made == 2, "the hammer forges 2 knives then breaks on the job and blocks further work"
    assert w.recipe_tool_condition("smithy", "hammer") <= 0.0, "the tool is worn out"


# ------------------------------------------------------ G-classic-shop-on-the-recipe-engine (headline; be_produce retired)
def test_a_classic_one_input_shop_now_runs_on_the_recipe_engine():
    from worlds.bigville_econ_world import BREAD, GRAIN, BAKING
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("baker", (2, 2)); w.set_skill("baker", BAKING, 3)
    w.add_shop("bakery", good=BREAD, price=4, cell=(2, 2), keeper="baker",
               activity=BAKING, input_good=GRAIN, stock=0, input_qty=2)
    w.refresh_open(); w.produce("bakery")              # produce() now arms the unified recipe engine
    assert w.stock_of("bakery") == 3 and w.input_of("bakery") == 1, \
        "a 1-input shop is the N=1 case: yield = skill (3), one grain consumed -- byte-identical to the old be_produce"
    prod = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_production.json")))
    assert "be_produce" not in {r["name"] for r in prod["rules"]}, "be_produce is retired"


# ------------------------------------------------------ G-unconscious-keeper-cannot-work (world fact)
def test_an_unconscious_keeper_cannot_work_the_craft():
    from worlds.bigville_econ_world import BREAD, GRAIN, BAKING
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("baker", (2, 2), collapsed=1.0); w.set_skill("baker", BAKING, 3)   # collapsed = unconscious
    w.add_shop("bakery", good=BREAD, price=4, cell=(2, 2), keeper="baker",
               activity=BAKING, input_good=GRAIN, stock=0, input_qty=2)
    w.refresh_open(); w.produce("bakery")
    assert w.stock_of("bakery") == 0 and w.input_of("bakery") == 2, \
        "an unconscious keeper produces nothing and consumes nothing -- you cannot work the craft collapsed (world fact)"


# ------------------------------------------------------ G-the-recipe-drives-it (source audit)
def test_production_reads_the_catalog_recipe_and_rules_decide():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_recipe.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"be_meet_input", "be_recipe_done", "be_reset_input"} <= names, "the checklist engine is three seed rules"
    logic = json.dumps([{k: r[k] for k in ("match", "where", "effects")} for r in seed["rules"]])
    for named in ("ore", "iron", "smelt", "charcoal"):
        assert named not in logic, f"the rules name no good ({named}) -- they read generic has_input/need_qty"
    src = open(os.path.join(_ROOT, "worlds", "bigville_econ_world.py")).read()
    assert 'next(r for r in E.RECIPES if r["name"] == recipe_name)' in src, "the shop reads its inputs from the catalog recipe"
