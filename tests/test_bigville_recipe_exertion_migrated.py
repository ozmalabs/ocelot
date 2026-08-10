"""bigville: a recipe has a STRENGTH REQUIREMENT and a STAMINA COST (the body meets the trade).

A heavy trade is not free labour. be_recipe_done now reads the keeper's BODY (has_body) and:
  * GATES on strength -- the keeper's effective strength must be >= the recipe's strength_req, or the
    batch cannot complete (you cannot forge a plough if you're not strong enough). A catalog datum
    (E.recipe_exertion): the heaviest trades sit ABOVE an average body, so only a strong/trained smith
    does them; light trades are 0 (unchanged).
  * COSTS stamina -- completing a batch spends the recipe's stamina_cost from the keeper's stamina
    RESERVE; run down the reserve and the keeper is too tired to continue until they REST.
  * makes the keeper HUNGRIER -- the stamina spent raises hunger_level (hard work needs more food).
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import domains.bigville_entities as E                       # noqa: E402
from worlds.bigville_econ_world import BigvilleEconWorld    # noqa: E402
from worlds.bigville_time_world import DAY                  # noqa: E402

FORGE = 8.0


def _forge(recipe="forge_plough", *, str_base=1.3, sta_base=1.5):
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("smith", (2, 2)); w.set_skill("smith", FORGE, 1)
    w.set_physique("smith", str_base=str_base, sta_base=sta_base)
    w.add_recipe_shop("forge", recipe, cell=(2, 2), keeper="smith", price=9,
                      activity=FORGE, inputs={"iron": 40, "charcoal": 40}, tools={"hammer": 1.0})
    w.refresh_open()
    return w


# ------------------------------------------------------ G-strength-gates-the-recipe (headline)
def test_a_weak_body_cannot_do_a_heavy_recipe_a_strong_one_can():
    assert E.recipe_exertion("forge_plough")[0] > 1.0, "the plough demands above-average strength (catalog datum)"
    weak = _forge(str_base=1.0)                              # an average body
    weak.make("forge")
    assert weak.stock_qty("forge") == 0.0, "an average smith is not strong enough to forge a plough -- no batch"
    strong = _forge(str_base=1.3)                            # a strong body
    strong.make("forge")
    assert strong.stock_qty("forge") > 0.0, "a strong smith forges it"


def test_training_strength_lets_a_body_eventually_do_it():
    w = _forge(str_base=1.05, sta_base=1.5)                  # just below the 1.2 plough requirement
    w.make("forge"); assert w.stock_qty("forge") == 0.0, "at first not quite strong enough"
    for _ in range(30):                                     # train strength on the job (strength tasks)
        w.perform_task("smith", strength=True, intensity=1.0)
    w.make("forge")
    assert w.stock_qty("forge") > 0.0, "having trained up his strength, the smith can now forge the plough"


# ------------------------------------------------------ G-stamina-cost-and-rest (headline)
def test_a_recipe_spends_stamina_and_a_tired_keeper_must_rest():
    w = _forge(str_base=1.3, sta_base=1.5)                   # capacity 1.5; plough costs 0.4/batch
    r0 = w.keeper_stamina_reserve("smith")
    w.make("forge"); r1 = w.keeper_stamina_reserve("smith")
    assert r1 < r0, "forging spends stamina from the reserve"
    made = w.stock_qty("forge")
    for _ in range(6):                                      # keep forging until too tired
        w.make("forge")
    tired = w.keeper_stamina_reserve("smith")
    assert tired < E.recipe_exertion("forge_plough")[1], "the reserve is now below one batch's cost -- too tired"
    stalled = w.stock_qty("forge")
    w.make("forge"); assert w.stock_qty("forge") == stalled, "and so the exhausted smith cannot forge another"
    w.rest("smith", 1.5)                                    # a good rest
    w.make("forge"); assert w.stock_qty("forge") > stalled, "rested, he forges again"


# ------------------------------------------------------ G-heavy-work-raises-hunger (headline)
def test_forging_makes_the_smith_hungrier():
    w = _forge(str_base=1.3, sta_base=2.0)
    h0 = w.hunger_of("smith")
    w.make("forge"); h1 = w.hunger_of("smith")
    assert h1 > h0, "a batch of heavy work raises the smith's hunger (needs more food)"
    w.make("forge")
    assert w.hunger_of("smith") > h1, "more forging, more hunger"


# ------------------------------------------------------ G-light-recipes-unchanged (no regression)
def test_a_light_recipe_has_no_strength_gate_or_stamina_cost():
    assert E.recipe_exertion("make_sandwich") == (0.0, 0.0), "a sandwich is light work"
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY); w.set_hours(1)
    w.make_trader("cook", (2, 2)); w.set_skill("cook", 9.0, 1)   # an ordinary body, skilled at cooking
    w.add_recipe_shop("kitchen", "make_sandwich", cell=(2, 2), keeper="cook", price=1,
                      activity=9.0, inputs={"ham": 5, "bread": 5})
    w.refresh_open()
    r0 = w.keeper_stamina_reserve("cook"); h0 = w.hunger_of("cook")
    w.make("kitchen")
    assert w.stock_qty("kitchen") > 0.0, "the light recipe completes for any body"
    assert w.keeper_stamina_reserve("cook") == r0 and w.hunger_of("cook") == h0, \
        "and costs no stamina and no extra hunger -- light work is unchanged"


# ------------------------------------------------------ G-demand-is-catalog-data (source audit)
def test_the_recipe_demand_is_catalog_data_and_the_gate_is_a_rule():
    import json
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_recipe.json")))
    r = next(x for x in seed["rules"] if x["name"] == "be_recipe_done")
    assert ["keeper", "has_body", "body"] in r["match"], "the completion reads the keeper's BODY"
    where = json.dumps(r["where"])
    assert "strength" in where and "strength_req" in where, "it GATES on the body's strength vs the recipe's requirement"
    assert "stamina_reserve" in where and "stamina_cost" in where, "and requires enough stamina reserve"
    effs = json.dumps(r["effects"])
    assert "stamina_reserve" in effs and "hunger_level" in effs, "completing spends the reserve AND raises hunger"
    src = open(os.path.join(_ROOT, "worlds", "bigville_econ_world.py")).read()
    assert "recipe_exertion(recipe_name)" in src, "the shop reads its physical demand from the catalog"
