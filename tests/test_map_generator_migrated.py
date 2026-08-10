"""bigville R45 (block 340000): the TOWN MAP GENERATOR -- programmatic generation from a
spec + seed, with strong fixed-points, building interiors, and affordance presets. The map
is the world, so the generator is a world-BUILDER (no agent decisions). Gates mirror
BIGVILLE_MAP_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_map_generator import BigvilleMapGenerator, PRESETS   # noqa: E402


# ------------------------------------------------------ G-deterministic
def test_the_map_is_deterministic_given_a_seed():
    assert BigvilleMapGenerator(seed=7).generate().fingerprint() == \
           BigvilleMapGenerator(seed=7).generate().fingerprint(), "same seed -> same town"
    assert BigvilleMapGenerator(seed=7).generate().fingerprint() != \
           BigvilleMapGenerator(seed=42).generate().fingerprint(), "a different seed -> a different fill"


# ------------------------------------------------------ G-fixed-points-always-present (headline)
def test_the_fixed_points_are_present_under_every_seed():
    for seed in (0, 1, 7, 42, 999):
        g = BigvilleMapGenerator(seed=seed).generate()
        # the church, with Mary and her PRIVATE counsel room and a bell
        assert "counsel" in g.rooms("Church") and g.room_is_private("Church", "counsel"), \
            "the church always has Mary's private counsel room"
        assert g.staff_of("Church") == "Mary"
        assert "Bell" in [t for t, _ in g.affordances("Church")], "and a bell"
        # the inn (commercial kitchen), the jail (cells), the market, the council hall
        assert g.has_kitchen("Inn") and g.rooms("Jail").count("cell") == 2
        assert g.place_kind("Market") == "market" and g.place_kind("Council Hall") == "council_hall"


# ------------------------------------------------------ G-houses-vary-cooking (headline)
def test_houses_may_or_may_not_have_cooking_facilities():
    g = BigvilleMapGenerator(seed=7).generate()
    houses = [p for p in g.places() if g.place_kind(p) == "house"]
    cooking = [p for p in houses if g.has_kitchen(p)]
    bare = [p for p in houses if not g.has_kitchen(p)]
    assert cooking and bare, f"some houses cook, some don't: cook={cooking} bare={bare}"
    # a house with no kitchen affords no heated Station -- it genuinely cannot cook
    assert g.kitchen_station(bare[0]) is None, "a kitchenless house has no cooking Station"


# ------------------------------------------------------ G-presets-differ
def test_kitchen_presets_have_tiered_defaults():
    assert (PRESETS["CommercialKitchen"][0][1]["prep_power"]
            > PRESETS["NormalKitchen"][0][1]["prep_power"]
            > PRESETS["PoorKitchen"][0][1]["prep_power"]), "commercial > normal > poor"
    g = BigvilleMapGenerator(seed=7).generate()
    assert g.prep_power("Inn") == PRESETS["CommercialKitchen"][0][1]["prep_power"], \
        "the inn is fitted with a commercial kitchen by the spec"


# ------------------------------------------------------ G-affordances-reuse-real-station (headline)
def test_a_generated_kitchen_affords_a_real_fs_prepare_station():
    g = BigvilleMapGenerator(seed=7).generate()
    st = g.kitchen_station("Inn")
    attrs = g.eng.node(st)["attrs"]
    # exactly the keys fs_prepare (bigville_foodstuff) reads on a station
    for key in ("heat", "prep_power", "fuel", "fuel_cost"):
        assert key in attrs, f"the affordance is a real Station usable by fs_prepare: missing {key}"
    assert float(attrs["heat"]) >= 1.0, "a kitchen station has heat (fs_prepare can COOK on it)"
    # confirm the food seed's cook rule actually reads these keys (composition, not reinvention)
    fs = json.load(open(os.path.join(_ROOT, "seeds", "bigville_foodstuff.json")))
    prep = json.dumps([r for r in fs["rules"] if r["name"] == "fs_prepare"][0])
    for key in ("heat", "prep_power", "fuel", "fuel_cost"):
        assert key in prep, f"fs_prepare reads Station.{key} -- the generated kitchen is compatible"


# ------------------------------------------------------ G-add-to-the-generator (source audit)
def test_the_map_is_data_driven_not_hand_edited():
    src = open(os.path.join(_ROOT, "worlds", "bigville_map_generator.py")).read()
    # a world builder: no rule engine, no agent decisions
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"the map builder must not run a rule engine: {forbidden}"
    # the town is DATA: a preset library + a spec, edited in one place, not hand-placed per house
    assert {"CommercialKitchen", "NormalKitchen", "PoorKitchen"} <= set(PRESETS), \
        "kitchen tiers are presets you add once, not hand-edited per building"
    from worlds.bigville_map_generator import DEFAULT_SPEC
    assert "fixed_points" in DEFAULT_SPEC and "houses" in DEFAULT_SPEC, \
        "fixed-points and house distributions are spec data"
    assert DEFAULT_SPEC["houses"]["kitchen_prob_by_wealth"], \
        "'houses may or may not have cooking facilities' is a spec distribution, not code"
