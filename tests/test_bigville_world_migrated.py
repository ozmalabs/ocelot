"""bigville R72 (block 390000): the canonical, data-driven, FLOAT-FREE world. Every entity comes
from the ONE data file (domains/bigville_entities.py), separate from the generic rules; commodities
are physical Stock piles, never store floats; adding a tool or recipe is pure data. Gates mirror
the data/logic separation.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_world import BigvilleWorld as World      # noqa: E402
from domains import bigville_entities as E                    # noqa: E402


def _town():
    w = World()
    w.add_actor("Wayland", role="smith"); w.add_actor("Colly", role="collier")
    for k, q in (("wood", 20), ("ore", 10), ("charcoal", 5), ("iron", 0), ("nails", 0)):
        w.set_stock(k, q)
    return w


# ------------------------------------------------------ G-entities-live-in-one-data-file (headline)
def test_every_entity_comes_from_the_single_data_file():
    w = World()
    assert w.item_kinds() == set(E.ITEMS), "the world's items are exactly the data file's ITEMS"
    assert w.recipe_names() == {r["name"] for r in E.RECIPES}, "the world's recipes are exactly the data file's RECIPES"
    for cat in (E.ITEMS, E.CONTAINERS, E.RECIPES, E.BUILDINGS):
        assert len(cat) > 0, "items, containers, recipes, and buildings are all defined as data"
    assert E.CONTAINERS["safe"]["lockable"] is True, "a safe is a lockable container -- defined in data"


# ------------------------------------------------------ G-commodities-are-physical-no-floats (headline)
def test_commodities_are_physical_stock_not_store_floats():
    w = _town()
    assert set(w.store_attrs()) == {"name"}, "the store carries NO commodity floats -- only Stock nodes hang off it"
    w.do("Colly", "burn_charcoal")
    assert w.qty("wood") == 16.0 and w.qty("charcoal") == 6.0, "a commodity is a physical pile, made by a recipe"
    src = open(os.path.join(_ROOT, "worlds", "bigville_world.py")).read()
    assert 'add_node("Stock"' in src, "commodities live on first-class Stock nodes, not store attributes"


# ------------------------------------------------------ G-a-recipe-combines-from-data
def test_a_two_input_recipe_combines_its_inputs_from_data():
    w = _town(); w.set_stock("iron", 2)
    w.do("Wayland", "forge_nails")
    assert w.qty("iron") == 1.0 and w.qty("charcoal") == 4.0 and w.qty("nails") == 5.0, \
        "forge_nails combines iron + charcoal -> nails, straight from the recipe data"


# ------------------------------------------------------ G-adding-a-tool-is-pure-data (headline)
def test_adding_a_new_tool_and_recipe_is_pure_data():
    w = _town(); w.set_stock("iron", 2)
    assert "chisel" not in w.item_kinds()
    w.add_item("chisel", {"class": "tool", "material": "metal", "verb": "carve", "base_mult": 1.4,
                          "wear_rate": 0.1, "make_minutes": 80, "make_effort": 1.2, "composite": False})
    w.add_recipe({"name": "forge_chisel", "requires": "smith", "in": [["iron", 1], ["charcoal", 1]],
                  "out": ["chisel", 1], "difficulty": 2.0, "time_minutes": 80})
    chisel = w.forge("Wayland", "forge_chisel")
    assert chisel is not None and w.tool_kind(chisel) == "chisel" and "chisel" in w.item_kinds(), \
        "a new tool combined from data runs with no code change"


# ------------------------------------------------------ G-recipes-take-time (headline; ported from worktime)
def test_a_recipe_takes_its_time_and_is_hard_work():
    w = World(); w.add_actor("Wayland", role="smith"); w.set_stock("iron", 2); w.set_stock("charcoal", 2)
    w.start("Wayland", "forge_knife")                  # 90 min -> 6 ticks
    assert w.busy("Wayland") and w.newest_tool() is None, "the smith is busy -- no knife yet"
    w.tick(3)
    assert w.busy("Wayland") and w.newest_tool() is None, "3 ticks in, still forging"
    w.tick(3)
    assert not w.busy("Wayland") and w.newest_tool() is not None, "after the full 6 ticks the knife exists"
    assert w.fatigue("Wayland") > 10.0, "and the work has tired him (difficulty accrues per tick)"


# ------------------------------------------------------ G-tools-are-discrete-with-quality (headline; ported catalog)
def test_a_forged_tool_is_a_discrete_item_whose_quality_is_the_makers_skill():
    w = World(); w.add_actor("Master", role="smith", skill=0.9); w.add_actor("Novice", role="smith", skill=0.3)
    w.set_stock("iron", 5); w.set_stock("charcoal", 5)
    w.do("Master", "forge_knife"); good = w.newest_tool()
    w.do("Novice", "forge_knife"); poor = w.newest_tool()
    assert w.tool_kind(good) == "knife" and w.tool_quality(good) == 0.9, "a discrete tool, quality = the maker's skill"
    assert w.tool_fitness(good) == 1.44 and w.tool_fitness(poor) == 0.48, "fitness = base_mult * skill (1.6 * .9 vs .3)"


# ------------------------------------------------------ G-variety-of-tools-from-data (headline)
def test_the_trades_forge_a_variety_of_tools_from_data():
    w = World(); w.add_actor("Grip", role="woodworker", skill=0.7); w.set_stock("timber", 5)
    w.do("Grip", "carve_rake"); rake = w.newest_tool()
    assert w.tool_kind(rake) == "rake" and w.tool_fitness(rake) == 0.84, "the woodworker forges a rake -- variety is data"


# ------------------------------------------------------ G-tools-wear-and-repair (headline; ported wear)
def test_a_tool_wears_with_use_breaks_and_is_repaired():
    w = World(); w.add_actor("Master", role="smith", skill=0.9); w.set_stock("iron", 5); w.set_stock("charcoal", 5)
    w.do("Master", "forge_knife"); k = w.newest_tool()
    w.use_tool(k, 3)
    assert w.tool_condition(k) == 0.7 and w.tool_fitness(k) == 1.008, "use wears it; fitness scales with condition"
    w.use_tool(k, 10)
    assert w.tool_broken(k) and w.tool_fitness(k) == 0.0, "worn out, it breaks"
    w.repair_tool("Master", k)
    assert not w.tool_broken(k) and w.tool_condition(k) == 1.0, "the smith repairs it to full"


# ------------------------------------------------------ G-batch-goods-stay-bulk
def test_a_batch_good_stays_bulk_not_a_discrete_item():
    w = World(); w.add_actor("Master", role="smith", skill=0.9); w.set_stock("iron", 5); w.set_stock("charcoal", 5)
    w.do("Master", "forge_nails")
    assert w.qty("nails") == 5.0 and w.newest_tool() is None, "nails are a bulk batch good (discrete=False), not a worn item"


# ------------------------------------------------------ G-charcoal-loop (ported from the craft/charcoal world)
def test_the_forge_burns_charcoal_made_from_wood():
    # no charcoal -> the forge cannot complete (its charcoal input is never met; it waits)
    dry = World(); dry.add_actor("Smith", role="smith", skill=0.8)
    dry.set_stock("charcoal", 0); dry.set_stock("iron", 5)
    dry.do("Smith", "forge_knife")
    assert dry.newest_tool() is None and dry.busy("Smith"), "no charcoal -> the forge cannot fire (raw wood won't do)"

    # the collier burns wood into charcoal; then the forge fires and burns a unit of it
    w = World(); w.add_actor("Colly", role="collier"); w.add_actor("Smith", role="smith", skill=0.8)
    w.set_stock("wood", 20); w.set_stock("charcoal", 0); w.set_stock("iron", 5)
    for _ in range(4):
        w.do("Colly", "burn_charcoal")
    assert w.qty("charcoal") == 4.0 and w.qty("wood") == 4.0, "wood -> charcoal (4 wood per unit)"
    w.do("Smith", "forge_knife")
    assert w.newest_tool() is not None and w.qty("charcoal") == 3.0, "with charcoal the forge fires and burns a unit"


# ------------------------------------------------------ G-composite-is-a-general-action (headline; ported craft)
def test_a_composite_tool_is_assembled_by_an_action_on_two_items_with_a_hammer():
    w = World(); w.add_actor("Smith", role="smith", skill=0.8); w.add_actor("Grip", role="woodworker", skill=0.6)
    w.set_stock("iron", 5); w.set_stock("charcoal", 5); w.set_stock("timber", 5)
    head = w.forge("Smith", "forge_pick_head")
    handle = w.forge("Grip", "carve_pick_handle")
    assert w.tool_kind(head) == "pick_head" and w.tool_quality(head) == 0.8, "the smith forges a head (a discrete component)"
    assert w.tool_quality(handle) == 0.6, "the woodworker carves a handle"
    pick = w.forge("Smith", "assemble_pick")       # assemble = an action on two ITEM inputs + a hammer
    assert w.tool_kind(pick) == "pick", "assembly is just an action (two item inputs, a hammer) -- no special rule"
    assert w.tool_quality(pick) == 0.6 and w.tool_fitness(pick) == 1.2, "a poor handle spoils it: quality = the weakest part"


def test_the_parts_are_consumed_and_the_hammer_wears_in_assembly():
    w = World(); w.add_actor("Smith", role="smith", skill=0.8); w.add_actor("Grip", role="woodworker", skill=0.6)
    w.set_stock("iron", 5); w.set_stock("charcoal", 5); w.set_stock("timber", 5)
    w.forge("Smith", "forge_pick_head"); w.forge("Grip", "carve_pick_handle")
    hammer_before = w.instrument_condition("hammer")
    w.forge("Smith", "assemble_pick")
    kinds = [w.tool_kind(t) for t in w.eng.neighbours(w._town, "has_tool_item")]
    assert kinds == ["pick"], "the head and handle were consumed into the tool -- only the pick remains"
    assert w.instrument_condition("hammer") < hammer_before, "the hammer wore, like any tool used in any action"


# ------------------------------------------------------ G-observed-demand (headline; ported produce)
def _smith():
    w = World(); w.add_actor("Smith", role="smith", skill=0.8)
    for k in ("iron", "charcoal", "timber", "ore"):
        w.set_stock(k, 50)
    return w


def test_the_maker_makes_what_he_believes_will_sell_from_observation():
    big = _smith(); big.observe("Smith", harvest=0.9, building=0.1, storage=0.1)
    assert big.belief("Smith") > 0.4 and big.decide("Smith") == "forge_scythe", \
        "observing a big harvest -> belief up -> he decides to make scythes"
    boom = _smith(); boom.observe("Smith", harvest=0.1, building=0.9, storage=0.1)
    assert boom.decide("Smith") == "forge_nails", "a building boom -> he makes nails instead (makers diverge on belief)"


def test_the_run_scales_with_demand_and_an_unsold_glut_cools_the_belief():
    w = _smith(); w.observe("Smith", harvest=0.9); w.decide("Smith"); q1 = w.want_qty("Smith")
    w.observe("Smith", harvest=0.9); w.decide("Smith"); q2 = w.want_qty("Smith")
    assert q2 > q1, "a stronger read of demand -> a bigger production run"

    glut = _smith(); glut.observe("Smith", harvest=0.9); glut.decide("Smith"); glut.produce_run("Smith")
    glut.sell("Smith", 0); glut.observe("Smith", harvest=0.9)
    sold = _smith(); sold.observe("Smith", harvest=0.9); sold.decide("Smith"); sold.produce_run("Smith")
    sold.sell("Smith", 999); sold.observe("Smith", harvest=0.9)
    assert glut.belief("Smith") < sold.belief("Smith"), "an unsold pile cools his belief vs a clean sell-through"


# ------------------------------------------------------ G-buildings-from-data (headline; folded in)
def test_the_town_installs_its_buildings_from_the_data():
    w = World()
    assert w.buildings() == set(E.BUILDINGS), "the world's buildings are exactly the data file's BUILDINGS"
    assert w.building_provides("forge") == "blacksmith" and w.building_sheltered("forge"), \
        "the forge is staffed by a blacksmith and is sheltered -- from the data"


# ------------------------------------------------------ G-container-capacity-conserved (headline; folded in)
def test_a_container_fills_up_to_capacity_and_conserves():
    w = World(); w.add_actor("Tom", role="hand"); w.set_stock("charcoal", 50)
    w.add_container("bin1", kind="bin", holds="charcoal")     # capacity 100 (volume) from data
    w.fill("Tom", "bin1", "charcoal", 30)
    assert w.contents("bin1", "charcoal") == 30.0 and w.qty("charcoal") == 20.0, "filling MOVES from the store into the bin (conserved)"
    small = World(); small.add_actor("Tom", role="hand"); small.set_stock("charcoal", 50)
    small.add_container("barrel1", kind="barrel", holds="charcoal")   # capacity 40
    small.fill("Tom", "barrel1", "charcoal", 40)              # exactly fills (40 * vol 1.0)
    assert small.contents("barrel1", "charcoal") == 40.0, "fills to capacity"
    small.fill("Tom", "barrel1", "charcoal", 1)              # one more would exceed the volume
    assert small.contents("barrel1", "charcoal") == 40.0, "will not overfill -- bounded by volume capacity"


# ------------------------------------------------------ G-the-safe-needs-the-key (headline; folded in)
def test_a_locked_safe_needs_the_key():
    w = World(); w.add_actor("Clerk", role="clerk"); w.add_actor("Tom", role="hand")
    w.set_stock("coin", 30)
    w.add_container("safe", kind="safe", holds="coin", lock_id=7.0, locked=True)
    w.fill("Tom", "safe", "coin", 30)
    assert w.contents("safe", "coin") == 0.0, "no key -> the locked safe stays shut"
    w.give_key("Clerk", opens=7.0); w.fill("Clerk", "safe", "coin", 30)
    assert w.contents("safe", "coin") == 30.0 and w.qty("coin") == 0.0, "the keyholder opens and fills it"
    w.unlock("Clerk"); w.empty("Tom", "safe", "coin", 10)
    assert w.contents("safe", "coin") == 20.0 and w.qty("coin") == 10.0, "unlocked, anyone can take from it"


# ------------------------------------------------------ G-trades-and-skills-unified (headline)
def test_a_trade_unifies_its_building_tools_and_skill():
    w = World()
    assert {"cooper", "tanner", "cobbler", "weaver", "tailor"} <= set(E.TRADES), "the new trades are data"
    assert {"cooperage", "tannery", "cobbler", "weavery", "tailorshop"} <= w.buildings(), "each trade has its building"
    coop = w.add_tradesperson("Barrow", "cooper")     # skill comes from the trade
    assert w.eng.node(coop)["attrs"]["skill"] == E.TRADES["cooper"]["base_skill"], "a tradesperson's skill is their trade's"


# ------------------------------------------------------ G-trade-chains (headline)
def test_the_new_trades_run_their_production_chains():
    w = World()
    for tr in ("cooper", "tanner", "cobbler", "weaver", "tailor"):
        w.add_tradesperson(f"{tr}1", tr)
    for k, q in (("timber", 20), ("hide", 10), ("wool", 20)):
        w.set_stock(k, q)
    # cooper: timber -> staves -> barrel
    w.do("cooper1", "rive_staves"); w.do("cooper1", "rive_staves")
    assert w.qty("stave") == 6.0 and w.tool_kind(w.forge("cooper1", "raise_barrel")) == "barrel", "cooper: staves -> barrel"
    # tanner -> cobbler: hide -> leather -> shoes
    w.do("tanner1", "tan_hide")
    assert w.qty("leather") == 1.0 and w.tool_kind(w.forge("cobbler1", "make_shoes")) == "shoes", "tanner+cobbler: hide->leather->shoes"
    # weaver -> tailor: wool -> cloth -> coat
    w.do("weaver1", "weave_cloth"); w.do("weaver1", "weave_cloth")
    assert w.qty("cloth") == 2.0 and w.tool_kind(w.forge("tailor1", "sew_coat")) == "coat", "weaver+tailor: wool->cloth->coat"


# ------------------------------------------------------ G-furniture-and-larger-tools (headline)
def test_furniture_and_larger_tools_are_made_as_data():
    w = World(); w.add_tradesperson("Joiner", "woodworker"); w.add_tradesperson("Smith", "smith")
    w.set_stock("timber", 20); w.set_stock("iron", 10); w.set_stock("charcoal", 10)
    table = w.forge("Joiner", "make_table")            # furniture
    assert w.tool_kind(table) == "table" and w.tool_fitness(table) == 0.84, "the woodworker makes furniture (a table)"
    plough = w.forge("Smith", "forge_plough")          # a larger tool
    assert w.tool_kind(plough) == "plough" and w.tool_fitness(plough) > 1.5, "the smith forges a larger tool (a plough)"


# ------------------------------------------------------ G-a-made-barrel-is-a-container (headline)
def test_a_made_barrel_is_a_usable_container():
    w = World(); w.add_tradesperson("Barrow", "cooper"); w.add_actor("Tom", role="hand")
    w.set_stock("timber", 30); w.set_stock("charcoal", 60)
    w.do("Barrow", "rive_staves"); w.do("Barrow", "rive_staves")
    barrel = w.forge("Barrow", "raise_barrel")
    assert w.tool_kind(barrel) == "barrel" and w.tool_quality(barrel) == 0.7, "the cooper makes a barrel (a discrete good)"
    w.use_as_store("mybarrel", barrel, holds="charcoal")     # the SAME node becomes a container
    w.fill("Tom", "mybarrel", "charcoal", 40)
    assert w.contents("mybarrel", "charcoal") == 40.0 and w.capacity("mybarrel") == 40.0, "its capacity is the item's data (40)"
    assert w.qty("charcoal") == 20.0, "filling moved charcoal from the store into the made barrel (conserved)"
    assert w.tool_quality(barrel) == 0.7, "it is still the SAME node -- a discrete item with quality AND a container"


def test_a_made_chest_is_a_lockable_container():
    w = World(); w.add_tradesperson("Joiner", "woodworker"); w.add_actor("Tom", role="hand")
    w.set_stock("timber", 30); w.set_stock("coin", 30)
    chest = w.forge("Joiner", "make_chest")
    w.use_as_store("mychest", chest, holds="coin", lock_id=5.0, locked=True)
    w.fill("Tom", "mychest", "coin", 20)
    assert w.contents("mychest", "coin") == 0.0, "a made chest is lockable -- no key, it stays shut"
    w.give_key("Tom", opens=5.0); w.fill("Tom", "mychest", "coin", 20)
    assert w.contents("mychest", "coin") == 20.0, "with the key it fills"


# ------------------------------------------------------ G-items-have-weight-and-size (headline)
def test_items_have_weight_and_volume():
    w = World()
    assert w.item_weight("iron") == 3.0 and w.item_volume("iron") == 0.5, "iron is dense: heavy and small"
    assert w.item_volume("timber") > w.item_volume("iron"), "timber is bulkier than iron"


# ------------------------------------------------------ G-a-container-holds-many-kinds-by-volume (headline)
def test_a_barrel_holds_multiple_kinds_bounded_by_volume():
    w = World(); w.add_actor("Tom", role="hand"); w.set_stock("charcoal", 50); w.set_stock("iron", 50)
    w.add_container("barrel1", kind="barrel", holds=["charcoal", "iron"])   # capacity 40 (volume)
    w.fill("Tom", "barrel1", "charcoal", 20)      # 20 * vol 1.0 = 20
    w.fill("Tom", "barrel1", "iron", 30)          # 30 * vol 0.5 = 15 ; total 35 <= 40
    assert w.contents("barrel1", "charcoal") == 20.0 and w.contents("barrel1", "iron") == 30.0, "a barrel holds many kinds at once"
    assert w.used_volume("barrel1") == 35.0 and w.contents_weight("barrel1") == 100.0, "capacity is by VOLUME; weight is tracked (10 + 90)"
    w.fill("Tom", "barrel1", "charcoal", 10)      # +10 volume -> 45 > 40
    assert w.contents("barrel1", "charcoal") == 20.0, "it will not overfill by volume"


# ------------------------------------------------------ G-fluids-need-a-watertight-vessel (headline)
def test_the_inn_brews_ale_and_fluids_need_a_watertight_vessel():
    w = World(); w.add_tradesperson("Hostler", "brewer"); w.add_actor("Tom", role="hand")
    w.set_stock("grain", 20); w.set_stock("water", 20)
    assert "inn" in w.buildings() and w.is_fluid("ale"), "the inn is a building; ale is a fluid"
    w.do("Hostler", "brew_ale")
    assert w.qty("ale") == 5.0 and w.qty("grain") == 17.0, "the inn brews its own ale from grain + water"
    w.add_container("cask", kind="barrel", holds=["ale"]); w.fill("Tom", "cask", "ale", 5)
    assert w.contents("cask", "ale") == 5.0, "a watertight barrel holds the ale"
    w.add_container("sack1", kind="sack", holds=["ale"]); w.fill("Tom", "sack1", "ale", 5)
    assert w.contents("sack1", "ale") == 0.0, "a sack is not watertight -- it cannot hold a fluid"


# ------------------------------------------------------ G-weight-drives-the-carry-limit (headline)
def test_a_person_carries_little_bounded_by_weight():
    w = World(); w.add_actor("Tom", role="hand"); w.set_stock("charcoal", 200); w.set_stock("iron", 200)
    w.add_carrier("bag", holds=["charcoal", "iron"], max_load=25.0)
    w.fill("Tom", "bag", "charcoal", 50)          # 50 * weight 0.5 = 25 -> fits exactly
    assert w.contents("bag", "charcoal") == 50.0 and w.contents_weight("bag") == 25.0, "a person carries up to their load (by weight)"
    w.fill("Tom", "bag", "iron", 1)               # + weight 3 -> 28 > 25
    assert w.contents("bag", "iron") == 0.0, "one more (by weight) is refused -- a person carries little"


# ------------------------------------------------------ G-a-cart-needs-wheels-and-a-horse (headline)
def test_a_cart_needs_wheels_and_a_horse_hauls_a_heavy_load():
    w = World(); w.add_tradesperson("Joiner", "woodworker"); w.add_actor("Tom", role="hand")
    w.set_stock("timber", 50); w.set_stock("iron", 200)
    w.do("Joiner", "make_wheel"); w.do("Joiner", "make_wheel")     # a cart needs 2 wheels
    cart = w.forge("Joiner", "make_cart")
    assert w.tool_kind(cart) == "cart", "the cart is made from timber + wheels"
    w.use_as_store("wagon", cart, holds=["iron"])
    assert w.max_load("wagon") == 50.0, "unhitched, the cart hauls little (push it yourself)"
    w.fill("Tom", "wagon", "iron", 100)
    assert w.contents("wagon", "iron") == 0.0, "100 iron (weight 300) is far over the unhitched load"
    w.add_animal("Dobbin", "horse"); w.hitch("Dobbin", "wagon")
    assert w.max_load("wagon") == 500.0 and w.animal_role("Dobbin") == "draught", "a hitched horse lets it haul up to its pull"
    w.fill("Tom", "wagon", "iron", 100)
    assert w.contents("wagon", "iron") == 100.0, "now the horse-drawn cart hauls the heavy load (weight 300 <= 500)"


# ------------------------------------------------------ G-animals-are-data-driven (headline)
def test_animals_are_data_driven():
    w = World()
    assert {"pig", "cow", "chicken", "horse", "dog", "cat"} <= set(E.ANIMALS), "the animals are data"
    w.add_animal("Daisy", "cow"); w.add_animal("Henny", "chicken"); w.add_animal("Hamlet", "pig")
    assert w.give_product("Daisy", "milk") == 3.0 and w.qty("milk") == 3.0, "a cow gives milk (from data)"
    assert w.give_product("Henny", "eggs") == 1.0 and w.give_product("Hamlet", "pork") == 40.0, "a hen gives eggs, a pig pork"
    w.add_animal("Rex", "dog"); w.add_animal("Puss", "cat"); w.add_animal("Dobbin", "horse")
    assert w.animal_role("Rex") == "working" and w.animal_role("Puss") == "working", "dogs and cats are working animals"
    assert w.animal_pull("Dobbin") == 500.0, "the horse is draught -- it can pull (data)"


# ------------------------------------------------------ G-animals-eat-and-starve (headline)
def test_animals_eat_their_feed_and_starve_without_it():
    fed = World(); fed.add_animal("Dobbin", "horse"); fed.set_stock("hay", 20)
    for _ in range(5):
        fed.pass_period()
    assert fed.animal_alive("Dobbin") and fed.animal_hunger("Dobbin") == 0.0, "a fed horse stays alive and satisfied"
    assert fed.qty("hay") == 5.0, "it eats its ration each period (3/period * 5 = 15 of 20)"

    starved = World(); starved.add_animal("Star", "horse"); starved.set_stock("hay", 0)
    for _ in range(4):
        starved.pass_period()
    assert not starved.animal_alive("Star"), "with no feed the horse starves past its starve_limit"


# ------------------------------------------------------ G-a-large-wagon (headline)
def test_a_large_wagon_has_four_wheels_and_hauls_more():
    w = World(); w.add_tradesperson("Joiner", "woodworker"); w.add_actor("Tom", role="hand")
    w.set_stock("timber", 60); w.set_stock("iron", 300)
    for _ in range(4):
        w.do("Joiner", "make_wheel")                 # a wagon needs 4 wheels
    wagon = w.forge("Joiner", "make_wagon")
    assert w.tool_kind(wagon) == "wagon", "the wagon is made from timber + 4 wheels"
    w.use_as_store("bigwagon", wagon, holds=["iron"])
    assert w.capacity("bigwagon") == 200.0, "a wagon is bigger than a cart (80)"
    w.add_animal("Nell", "horse"); w.hitch("Nell", "bigwagon")
    w.fill("Tom", "bigwagon", "iron", 150)
    assert w.contents("bigwagon", "iron") == 150.0, "the horse-drawn wagon hauls a large load"


# ------------------------------------------------------ G-imported-goods (headline)
def test_goods_from_outside_bigville_are_imported_and_used_locally():
    w = World()
    assert w.is_imported("ink") and w.is_imported("dye") and not w.is_imported("iron"), "ink/dye come from outside; iron is local"
    w.import_good("dye", 5); w.import_good("ink", 3)
    assert w.qty("dye") == 5.0 and w.qty("ink") == 3.0, "imported goods are acquired from outside (a merchant)"
    # a LOCAL recipe uses an import: the dyer dyes cloth with imported dye
    w.add_tradesperson("Dexter", "dyer"); w.set_stock("cloth", 5)
    cc = w.forge("Dexter", "dye_cloth")
    assert w.tool_kind(cc) == "coloured_cloth" and w.qty("dye") == 4.0, "the dyer makes coloured cloth using the imported dye"
    # paper/ink ARE real recipes -- they exist; bigville just doesn't COMMONLY KNOW them, so it imports
    assert "make_paper" in w.recipe_names() and w.item_kinds() >= {"paper", "ink"}, "the recipes exist; the goods are imported for now"


# ------------------------------------------------------ G-recipes-exist-but-may-not-be-known (headline)
def test_a_recipe_exists_but_may_not_be_known_and_is_taught_or_written():
    w = World()
    assert "make_ink" in w.recipe_names(), "make_ink is a real recipe -- it exists"
    # a common recipe is known by its trade
    w.add_tradesperson("Smith", "smith"); w.set_stock("iron", 10); w.set_stock("charcoal", 10)
    assert w.knows("Smith", "forge_knife"), "a smith commonly knows forge_knife"
    # but make_ink is not commonly known in bigville -- an inkmaker cannot make it yet
    w.add_tradesperson("Inky", "inkmaker"); w.set_stock("soot", 10); w.set_stock("oil", 10)
    assert not w.knows("Inky", "make_ink"), "make_ink is not common knowledge here"
    assert w.do("Inky", "make_ink") is False and w.qty("ink") == 0.0, "he cannot make what he does not know"
    # TAUGHT: a master who knows it teaches him
    w.add_tradesperson("Master", "inkmaker")
    w.eng.add_edge_unchecked(w._actors["Master"], "knows", w._actions["make_ink"])   # a visiting master knows it
    w.teach("Master", "Inky", "make_ink")
    assert w.knows("Inky", "make_ink") and w.do("Inky", "make_ink") and w.qty("ink") == 3.0, "taught the recipe, he can make ink"
    # WRITTEN DOWN: the master writes it; a scribe reads it and learns
    rec = w.write_recipe("Master", "make_ink"); w.add_tradesperson("Scribe", "inkmaker")
    w.read_recipe("Scribe", rec)
    assert w.knows("Scribe", "make_ink"), "a recipe written down can be read to learn it"


# ------------------------------------------------------ G-crops-and-food (headline)
def test_crops_vegetables_and_food_are_data_and_cooked():
    w = World()
    assert {"cabbage", "carrot", "onion", "potato", "turnip", "bean", "pea"} <= set(E.ITEMS), "the vegetables are data"
    w.add_tradesperson("Baker", "baker"); w.set_stock("flour", 10); w.set_stock("water", 20)
    w.do("Baker", "bake_bread")
    assert w.qty("bread") == 3.0, "the baker bakes bread from flour + water"
    w.add_tradesperson("Cook", "cook"); w.set_stock("beef", 5); w.set_stock("carrot", 5); w.set_stock("onion", 5)
    w.do("Cook", "make_stew")                     # a 4-input recipe: beef + carrot + onion + water
    assert w.qty("stew") == 3.0 and w.qty("beef") == 4.0, "the cook makes stew from meat + vegetables"


# ------------------------------------------------------ G-butchery-is-a-skill (headline)
def test_butchery_turns_an_animal_into_meat_and_is_a_skill():
    w = World(); w.add_tradesperson("Chop", "butcher"); w.add_tradesperson("Cook", "cook")
    w.add_animal("Hamlet", "pig")
    got = w.butcher("Chop", "Hamlet")
    assert got == {"pork": 40.0, "hide": 2.0} and not w.animal_alive("Hamlet"), "a butcher turns the pig into pork + hide"
    assert w.qty("pork") == 40.0, "the meat enters the store"
    w.add_animal("Bess", "cow")
    try:
        w.butcher("Cook", "Bess"); raised = False
    except AssertionError:
        raised = True
    assert raised and w.animal_alive("Bess"), "only a butcher can butcher -- it is a skill"


# ------------------------------------------------------ G-merchant-delivers-imports (headline)
def test_a_merchant_delivers_imported_goods():
    w = World()
    w.add_merchant("Marco", brings={"pepper": 5, "ink": 3, "cinnamon": 2})
    assert w.qty("pepper") == 0.0, "before delivery the goods are on the merchant's cart, not in the store"
    w.deliver("Marco")
    assert w.qty("pepper") == 5.0 and w.qty("ink") == 3.0 and w.qty("cinnamon") == 2.0, "the merchant carries the imports in"


# ------------------------------------------------------ G-books-record-and-teach-recipes (headline)
def test_a_book_is_made_records_a_recipe_and_teaches_the_reader():
    w = World(); w.add_tradesperson("Scribe", "scribe"); w.set_stock("paper", 10); w.set_stock("ink", 5)
    book = w.forge("Scribe", "bind_book")
    assert w.tool_kind(book) == "book" and w.item_weight("book") == 1.0, "a scribe binds a book (a physical good with weight)"
    w.add_tradesperson("Master", "inkmaker")
    w.eng.add_edge_unchecked(w._actors["Master"], "knows", w._actions["make_ink"])
    w.write_in_book("Master", book, "make_ink")
    assert w.book_recipe(book) == "make_ink", "the master writes a recipe he knows into the book"
    w.add_tradesperson("Student", "inkmaker"); w.read_book("Student", book)
    assert w.knows("Student", "make_ink"), "a reader learns the recipe from the book"


# ------------------------------------------------------ G-crop-lifecycle (headline)
def test_a_crop_is_sown_grows_when_watered_and_is_harvested():
    w = World(); w.set_stock("carrot_seed", 5); w.set_stock("water", 50)
    assert "wheat" in E.CROPS and E.CROPS["wheat"]["seed"] == "wheat_seed", "crops carry their seed/growth/yield as data"
    c = w.sow("Hob", "carrot")                        # carrot: 3 grow periods, 2 water each
    assert w.crop_age(c) == 0.0 and w.crop_alive(c) and w.qty("carrot_seed") == 4.0, "sowing plants a crop and uses a seed"
    for _ in range(3):
        w.pass_period()
    assert w.crop_mature(c) and w.qty("water") == 44.0, "watered each period it grows to maturity (used 2 water * 3)"
    assert w.harvest_crop(c) == 10.0 and w.qty("carrot") == 10.0, "the mature crop is harvested for its yield"


def test_an_unwatered_crop_wilts():
    w = World(); w.set_stock("carrot_seed", 5); w.set_stock("water", 0)   # no water
    c = w.sow("Hob", "carrot")
    for _ in range(3):
        w.pass_period()
    assert not w.crop_alive(c), "with no water the crop wilts and dies"


# ------------------------------------------------------ G-crops-are-seasonal (headline)
def test_crops_are_sown_only_in_their_season():
    w = World(); w.set_stock("carrot_seed", 5); w.set_stock("turnip_seed", 5)
    assert w.season() == "spring"
    assert w.sow("Hob", "carrot") is not None, "a spring crop sows in spring"
    assert w.sow("Hob", "turnip") is None, "an autumn crop (turnip) will not sow in spring"
    w.set_season("autumn")
    assert w.sow("Hob", "turnip") is not None and w.sow("Hob", "carrot") is None, "the seasons swap what can be sown"


# ------------------------------------------------------ G-residents-must-eat (headline)
def test_residents_get_hungry_eat_food_and_starve_without_it():
    fed = World(); fed.add_actor("Tom", role="hand"); fed.set_stock("bread", 20)
    for _ in range(2):                               # a couple of periods (before the bread rots away)
        fed.pass_period()
    assert fed.is_alive("Tom") and fed.hunger("Tom") == 0.0, "a fed resident stays alive and satisfied"
    assert fed.qty("bread") == 18.0, "he eats a unit of food each period (2 of 20)"

    starved = World(); starved.add_actor("Nell", role="hand")   # no food
    for _ in range(5):
        starved.pass_period()
    assert not starved.is_alive("Nell"), "with no food the resident starves past the limit"


# ------------------------------------------------------ G-adjectival-classes (headline)
def test_each_item_has_an_adjectival_class_with_stages():
    w = World()
    assert set(E.ADJECTIVES) >= {"metal", "perishable", "textile", "wood", "leather"}, "the adjective classes are data"
    assert E.ADJECTIVES["metal"] == ["pristine", "worn", "rusty", "ruined"], "metal has its own stages"
    assert E.ADJECTIVES["perishable"] == ["fresh", "stale", "rotten", "putrid"], "perishables have their own stages"
    assert w.adjectival_class("iron") == "metal" and w.adjectival_class("bread") == "perishable", "each item has a class"
    assert w.adjectival_class("coat") == "textile" and w.adjectival_class("chair") == "wood" and w.adjectival_class("boots") == "leather"


# ------------------------------------------------------ G-different-wear-and-decay-rates (headline)
def test_items_have_different_wear_and_decay_rates():
    w = World()
    assert w.item_decay_rate("bread") > w.item_decay_rate("timber") > w.item_decay_rate("knife"), \
        "food rots faster than wood rots faster than metal rusts (damage over time differs by item)"
    assert w.item_wear_rate("scythe") > w.item_wear_rate("knife"), "different items wear from use at different rates"


# ------------------------------------------------------ G-metal-rusts-with-time (headline)
def test_a_tool_decays_over_time_through_its_adjective_stages():
    w = World(); w.add_tradesperson("Smith", "smith"); w.set_stock("iron", 10); w.set_stock("charcoal", 10)
    k = w.forge("Smith", "forge_knife")
    assert w.tool_adjective(k) == "pristine", "a new knife is pristine"
    w.pass_period(15)
    assert w.tool_adjective(k) == "worn", "over time (rust) it becomes worn"
    w.pass_period(25)
    assert w.tool_adjective(k) in ("rusty", "ruined"), "and then rusty/ruined -- damage over time, not just use"


# ------------------------------------------------------ G-food-rots-and-spoils (headline)
def test_perishable_food_rots_through_its_stages_and_spoils():
    w = World(); w.set_stock("bread", 20)
    assert w.stock_adjective("bread") == "fresh", "fresh bread"
    w.pass_period(1)
    assert w.stock_adjective("bread") == "stale", "a period on -> stale"
    w.pass_period(2)
    assert w.stock_adjective("bread") in ("rotten", "putrid"), "then rotten/putrid (food rots fast)"
    w.pass_period(2)
    assert w.qty("bread") == 0.0, "fully rotted, it spoils and is discarded"


# ------------------------------------------------------ G-larder-slows-decay (headline)
def test_a_larder_keeps_food_far_longer_than_loose():
    w = World(); w.add_actor("Tom", role="hand"); w.set_stock("bread", 50)
    w.add_container("larder1", kind="larder", holds=["bread"])   # cold store, decay_factor 0.3
    w.fill("Tom", "larder1", "bread", 20)
    for _ in range(3):
        w.pass_period()
    assert w.stock_adjective("bread") == "putrid", "loose bread has rotted (putrid) after 3 periods"
    assert w.stored_adjective("larder1", "bread") == "fresh" and w.stored_condition("larder1", "bread") > 0.7, \
        "the same bread in the cold larder is still fresh (kept ~3x longer)"


# ------------------------------------------------------ G-salting-preserves (headline)
def test_salting_preserves_food():
    w = World(); w.set_stock("pork", 20); w.set_stock("bacon", 20)
    assert E.decay_rate("bacon") < E.decay_rate("pork"), "salted bacon decays far slower than fresh pork (data)"
    for _ in range(2):
        w.pass_period()
    assert w.stock_adjective("pork") == "rotten" and w.stock_adjective("bacon") == "fresh", "fresh rots; salted keeps"
    w.add_tradesperson("Cook", "cook"); w.set_stock("salt", 5)
    before = w.qty("bacon")
    w.do("Cook", "salt_pork")                          # cure pork into bacon (pork + salt -> bacon)
    assert w.qty("bacon") > before, "the cook salts pork into (slow-decaying) bacon"


# ------------------------------------------------------ G-repair-restores-condition (headline)
def test_repair_restores_a_worn_tools_condition_and_adjective():
    w = World(); w.add_tradesperson("Smith", "smith"); w.set_stock("iron", 10); w.set_stock("charcoal", 10)
    k = w.forge("Smith", "forge_knife")
    w.pass_period(30)
    assert w.tool_adjective(k) in ("rusty", "ruined"), "over time the knife rusts"
    w.repair_tool("Smith", k)
    assert w.tool_adjective(k) == "pristine" and w.tool_condition(k) == 1.0, "a repair restores it -- pristine again"


# ------------------------------------------------------ G-clothes-are-dyed-a-colour (headline)
def test_a_dye_gives_a_garment_its_colour():
    w = World(); w.add_tradesperson("Tessa", "tailor")
    w.set_stock("cloth", 20); w.set_stock("madder", 3); w.set_stock("woad", 3)
    coat = w.forge("Tessa", "sew_coat"); dress = w.forge("Tessa", "sew_dress")
    assert w.garment_colour(coat) == "", "an undyed garment has no colour"
    assert w.dye_garment("Tessa", coat, "madder") == "red", "madder dyes it red (the colour comes from the dye)"
    assert w.dye_garment("Tessa", dress, "woad") == "blue", "woad dyes it blue -- different dyes, different colours"
    assert w.qty("madder") == 2.0, "dyeing consumed one dye"


# ------------------------------------------------------ G-people-seen-wearing (headline)
def test_people_are_seen_wearing_their_clothes():
    w = World(); w.add_tradesperson("Tessa", "tailor"); w.set_stock("cloth", 20)
    coat = w.forge("Tessa", "sew_coat"); hat = w.forge("Tessa", "sew_hat")
    w.add_actor("Ned", role="hand")
    assert w.worn("Ned") == [], "before dressing, Ned wears nothing"
    w.wear("Ned", coat); w.wear("Ned", hat)
    assert sorted(w.worn("Ned")) == ["coat", "hat"], "Ned is SEEN wearing his coat and hat"
    w.take_off("Ned", hat)
    assert w.worn("Ned") == ["coat"], "take the hat off -- no longer seen wearing it"


# ------------------------------------------------------ G-clothes-protect-from-weather (headline)
def test_worn_clothes_give_environmental_protection():
    w = World(); w.add_tradesperson("Tessa", "tailor"); w.set_stock("cloth", 20)
    coat = w.forge("Tessa", "sew_coat")   # warmth 3, rain 1
    cloak = w.forge("Tessa", "sew_cloak") # warmth 2, rain 3
    w.add_actor("Ned", role="hand"); w.add_actor("Bram", role="hand")   # Bram stays naked
    w.wear("Ned", coat); w.wear("Ned", cloak)
    w.expose(cold=5.0, wet=3.0)
    assert w.chill("Ned") == 0.0 and w.soaked("Ned") == 0.0, "dressed (warmth 5, rain-cover 4): the clothes take the weather"
    assert w.chill("Bram") == 5.0 and w.soaked("Bram") == 3.0, "naked in the same weather: full chill, fully soaked"
    w.take_off("Ned", cloak); w.expose(cold=5.0, wet=3.0)
    assert w.warmth("Ned") == 3.0 and w.chill("Ned") == 2.0, "remove the cloak and protection falls -- he feels the cold"


# ------------------------------------------------------ G-plain-and-fine-clothes-exist (data headline)
def test_there_are_plain_clothes_and_fine_clothes():
    plain = {k for k, s in E.ITEMS.items() if s.get("station") == "plain"}
    fine  = {k for k, s in E.ITEMS.items() if s.get("station") == "fine"}
    assert {"smock", "tunic", "cap", "clogs"} <= plain, "simple clothes for tradespeople (plain, cheap cloth/wood)"
    assert {"gown", "doublet", "fur_cloak", "silk_shirt"} <= fine, "fancy clothes for the rich"
    assert all(E.ITEMS[k]["finery"] == 0.0 for k in ("smock", "cap", "clogs", "apron")), "plain clothes carry no finery"
    assert all(E.ITEMS[k]["finery"] >= 3.0 for k in fine), "fine clothes carry high finery"
    assert all(E.ITEMS[k]["material"] in ("silk", "velvet", "fur") for k in fine), "fine clothes are sewn from fine fabrics"


# ------------------------------------------------------ G-fine-tailoring-is-a-specialist-skill (headline)
def test_fine_tailoring_is_a_learned_specialist_skill():
    w = World(); w.add_tradesperson("Tessa", "tailor"); w.set_stock("cloth", 10); w.set_stock("silk", 6)
    assert w.knows("Tessa", "sew_smock"), "every tailor commonly knows plain sewing"
    assert not w.knows("Tessa", "sew_gown"), "fine tailoring is NOT common knowledge -- it must be learned"
    assert w.do("Tessa", "sew_gown") is False and w.qty("silk") == 6.0, "an untaught tailor cannot sew a gown"
    w.add_tradesperson("Margery", "tailor")
    w.eng.add_edge_unchecked(w._actors["Margery"], "knows", w._actions["sew_gown"])   # a master already knows it
    w.teach("Margery", "Tessa", "sew_gown")
    assert w.knows("Tessa", "sew_gown"), "taught the fine craft, Tessa now knows it"
    g = w.forge("Tessa", "sew_gown")
    assert w.garment_station(g) == "fine", "and can sew a fine gown"


# ------------------------------------------------------ G-tradesman-plain-rich-fine (headline)
def test_a_tradesman_is_plainly_dressed_and_the_rich_finely():
    w = World(); w.add_tradesperson("Tessa", "tailor"); w.set_stock("cloth", 10); w.set_stock("silk", 6)
    smock = w.forge("Tessa", "sew_smock")
    w.eng.add_edge_unchecked(w._actors["Tessa"], "knows", w._actions["sew_gown"]); gown = w.forge("Tessa", "sew_gown")
    w.add_actor("Hodge", role="hand"); w.add_actor("Lady", role="gentry")
    w.wear("Hodge", smock); w.wear("Lady", gown)
    assert w.dressed_stations("Hodge") == ["plain"] and w.finery("Hodge") == 0.0, "the tradesman wears plain, no finery"
    assert w.dressed_stations("Lady") == ["fine"] and w.finery("Lady") == 5.0, "the lady wears fine, high finery"
    assert w.finery("Lady") > w.finery("Hodge"), "finery is the observable that marks the rich from the tradesman"


# ------------------------------------------------------ G-every-material-has-scarcity (data headline)
def test_every_raw_material_has_a_general_scarcity():
    made = {r["out"][0] for r in E.RECIPES}
    raw = [k for k in E.ITEMS if k not in made]
    unpriced = [k for k in raw if k not in E.SCARCITY and "scarcity" not in E.ITEMS[k]]
    assert unpriced == [], f"every RAW material carries a general scarcity in the data; missing: {unpriced}"
    # scarcity is ordered as one expects: local < farmed < imported luxury
    assert E.scarcity("water") < E.scarcity("wool") < E.scarcity("salt") < E.scarcity("silk"), \
        "abundant local stuff is cheap, imported luxuries dear"


# ------------------------------------------------------ G-value-is-scarcity-plus-labour (headline)
def test_a_reference_value_is_calculable_from_scarcity_and_labour():
    # a RAW material's value is just its scarcity -- no labour embodied
    assert E.reference_value("silk") == E.scarcity("silk") and E.embodied_labour("silk") == 0.0, \
        "a raw material's value == its scarcity"
    # a MADE item accumulates its inputs' material + the labour of the whole chain
    coat_mat, coat_lab = E.material_value("coat"), E.embodied_labour("coat")
    assert coat_lab > 0.0, "a made coat embodies labour (sewing + weaving the cloth)"
    assert abs(E.reference_value("coat") - (coat_mat + coat_lab * E.LABOUR_RATE)) < 1e-6, \
        "reference value = embodied material scarcity + embodied labour priced at LABOUR_RATE"
    # the two components are SEPARABLE -- relative scarcity vs total labour are each calculable
    assert 0.0 < coat_mat / E.reference_value("coat") < 1.0, "relative scarcity is a calculable fraction of value"


# ------------------------------------------------------ G-value-tracks-the-chain (headline)
def test_value_reflects_scarcer_inputs_and_more_labour():
    # a fine gown (scarce imported silk + long tailoring) is worth far more than a plain smock (cheap cloth)
    assert E.reference_value("gown") > 4 * E.reference_value("smock"), "fine dress is dear; plain dress cheap"
    # embodied labour is a MINUTES total through the whole chain -- more than any single step
    assert E.embodied_labour("coat") > 150.0, "the coat's labour includes weaving its cloth, not just the sewing"
    # the world reads the same calculated value the data gives
    w = World()
    assert w.reference_value("gown") == E.reference_value("gown") and w.scarcity("silk") == 12.0, \
        "the world exposes the calculated value + scarcity"


# ------------------------------------------------------ G-recipes-have-a-min-skill (data headline)
def test_recipes_carry_a_minimum_skill_and_basic_work_is_open():
    # master/specialist work has a real floor; basic work is open (an apprentice can attempt it, badly)
    assert E.min_skill("sew_gown") >= 0.7 and E.min_skill("forge_plough") >= 0.7 and E.min_skill("make_wagon") >= 0.7, \
        "master work needs real skill"
    assert E.min_skill("sew_smock") == 0.0 and E.min_skill("forge_knife") == 0.0, \
        "basic work has no floor -- a novice can attempt it (difficulty sets how WELL, not whether)"
    w = World(); w.add_actor("Novice", role="smith", skill=0.3); w.set_stock("iron", 5); w.set_stock("charcoal", 5)
    assert w.do("Novice", "forge_knife") and w.tool_quality(w.newest_tool()) == 0.3, "a novice forges a crude knife"


# ------------------------------------------------------ G-reading-is-not-enough (headline)
def test_you_cannot_read_your_way_to_a_blacksmiths_hand():
    w = World(); w.add_actor("Nan", role="tailor", skill=0.3); w.set_stock("silk", 10)
    # Nan READS the fine-gown recipe -- she now KNOWS it, but her hand is untrained
    w.eng.add_edge_unchecked(w._actors["Nan"], "knows", w._actions["sew_gown"])
    assert w.knows("Nan", "sew_gown") and not w.can_make("Nan", "sew_gown"), "knowing it is not being able to do it"
    assert w.do("Nan", "sew_gown") is False and w.qty("silk") == 10.0, "unskilled, she cannot make the gown (silk untouched)"


# ------------------------------------------------------ G-apprenticeship-builds-skill (headline)
def test_apprenticeship_builds_the_skill_to_cross_the_floor():
    w = World()
    w.add_actor("Margery", role="tailor", skill=0.85)   # a master
    w.add_actor("Nan", role="tailor", skill=0.3)        # an apprentice who has read the recipe
    w.set_stock("silk", 10)
    w.eng.add_edge_unchecked(w._actors["Nan"], "knows", w._actions["sew_gown"])
    assert not w.can_make("Nan", "sew_gown"), "at first she is far below the floor"
    w.apprentice("Nan", "Margery")
    for _ in range(8):                                   # skill rises toward the master's, one step a period
        w.pass_period()
    assert w.skill("Nan") >= w.recipe_min_skill("sew_gown"), "apprenticed under a master, her skill crosses the floor"
    assert w.can_make("Nan", "sew_gown"), "and she can finally sew a gown"
    g = w.forge("Nan", "sew_gown")
    assert w.tool_kind(g) == "gown" and w.tool_quality(g) == w.skill("Nan"), "the gown's quality is her EARNED skill"
    # a learner never outstrips their master
    assert w.skill("Nan") <= w.skill("Margery"), "you learn up to your master, not beyond"


# ------------------------------------------------------ G-townsfolk-default-uppity (headline)
def test_townsfolk_default_uppity_but_the_tiers_still_exist():
    w = World()
    # this town is UPPITY -- a plain resident defaults to EDUCATED (reads the laws, keeps accounts)
    w.add_actor("Toff", role="hand")
    assert w.literacy_tier("Toff") == "educated" and w.can_read_law("Toff") and w.can_account("Toff"), \
        "townsfolk default to educated -- all uppity"
    # the class tiers still exist and can be requested explicitly
    w.add_actor("Hob", role="hand", station="labouring")            # a rare labourer
    w.add_tradesperson("Merek", "cooper", station="middle")         # a middling sort
    assert w.literacy_tier("Hob") == "labouring" and not w.can_read("Hob"), "an explicit labourer cannot read"
    assert w.literacy_tier("Merek") == "functional" and w.can_read("Merek") and not w.can_read_law("Merek"), \
        "an explicit middling reads notes but not the council laws"


# ------------------------------------------------------ G-written-knowledge-needs-literacy (headline)
def test_written_knowledge_needs_literacy_the_illiterate_must_be_taught():
    w = World()
    w.add_tradesperson("Scribe", "scribe")                          # literate by craft
    w.eng.add_edge_unchecked(w._actors["Scribe"], "knows", w._actions["forge_knife"])
    rec = w.write_recipe("Scribe", "forge_knife")
    assert rec is not None, "the literate scribe can write the recipe down"
    w.add_actor("Hob", role="hand", station="labouring")            # a rare illiterate labourer
    assert w.read_recipe("Hob", rec) is None and not w.knows("Hob", "forge_knife"), \
        "the labourer cannot read it -- the written word is closed to him"
    # a labourer can only be TAUGHT (orally), never read his way in
    w.teach("Scribe", "Hob", "forge_knife")
    assert w.knows("Hob", "forge_knife"), "but he can be taught the recipe by word of mouth"
    w.add_tradesperson("Merek", "cooper", station="middle")         # functional literacy
    assert w.read_recipe("Merek", rec) == "forge_knife" and w.knows("Merek", "forge_knife"), \
        "the functionally-literate cooper reads it and learns it"


# ------------------------------------------------------ G-school-raises-literacy (headline)
def test_school_raises_a_labourer_through_the_tiers_if_they_can_learn():
    w = World()
    w.add_actor("Schoolmaster", role="teacher", station="educated")
    w.add_actor("Hob", role="hand", station="labouring")            # a labourer who starts unable to read
    assert not w.can_read("Hob"), "before school, the labourer cannot read"
    w.enrol("Hob", "Schoolmaster")
    w.pass_period(3)
    assert w.can_read("Hob") and w.literacy_tier("Hob") == "functional", "a few terms of school -> functional literacy"
    w.pass_period(6)
    assert w.literacy_tier("Hob") == "educated" and w.can_read_law("Hob"), "kept at school -> educated (reads the laws)"
    # one who CANNOT learn does not progress, however long they attend
    w.add_actor("Dull", role="hand", learn=0.0); w.enrol("Dull", "Schoolmaster")
    before = w.literacy("Dull"); w.pass_period(5)
    assert w.literacy("Dull") == before, "if you cannot learn, school does not raise you"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_world():
    for f in ("worlds/bigville_world.py", "domains/bigville_entities.py"):
        src = open(os.path.join(_ROOT, f)).read()
        for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
            assert forbidden not in src, f"{f} must not run a rule engine: {forbidden}"
    ent = open(os.path.join(_ROOT, "domains", "bigville_entities.py")).read()
    for logic in ("run_rules", "add_edge", "set_attr", "force_all_dirty"):
        assert logic not in ent, f"the entity DATA file must contain no logic ({logic}) -- data only"
