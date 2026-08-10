"""bigville R52 (block 368000): REAL farms -- on the map, worked by farmhands, with livestock
that live, grow, breed, and die/are slaughtered. Understaffed fields aren't fully reaped; the
weather scales the harvest; the herd must breed to replace losses; manure closes the nutrient
loop. Gates mirror the seed description.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_farm_world import BigvilleFarmWorld as Farm   # noqa: E402


# ------------------------------------------------------ G-farm-on-the-map (headline)
def test_a_farm_is_a_place_on_the_map():
    w = Farm(); w.add_farm("Manor")
    assert w.is_farm_on_map("Manor"), "the farm is a Place{kind:farm} on the map (has_place)"


# ------------------------------------------------------ G-workers-work-the-land (headline)
def test_the_harvest_needs_farmhands():
    w = Farm(); w.add_farm("Manor")
    w.add_field("Manor", "north", area=1.0, fertility=10.0, per_worker=0.5)
    w.harvest("Manor", "north")
    assert w.food_out("Manor") == 0.0, "with no hands the crop rots -- the land must be worked"
    w.hire_worker("Manor", "Hodge"); w.hire_worker("Manor", "Giles")
    w.harvest("Manor", "north")
    assert w.food_out("Manor") == 10.0, "two farmhands bring in the full crop"


# ------------------------------------------------------ G-understaffed-partial-harvest
def test_understaffed_only_part_of_the_crop_is_brought_in():
    w = Farm(); w.add_farm("Small")
    w.add_field("Small", "f", area=1.0, fertility=10.0, per_worker=0.5)   # 2 hands = full
    w.hire_worker("Small", "Solo")
    w.harvest("Small", "f")
    assert w.last_yield("f") == 5.0, "one hand of two needed -> half the crop; the rest rots in the field"


# ------------------------------------------------------ G-weather-scales-the-harvest
def test_the_weather_scales_the_harvest():
    dry = Farm(); dry.add_farm("M"); dry.add_field("M", "f", fertility=10.0, per_worker=1.0); dry.hire_worker("M", "H")
    dry.set_weather(0.5); dry.harvest("M", "f")
    wet = Farm(); wet.add_farm("M"); wet.add_field("M", "f", fertility=10.0, per_worker=1.0); wet.hire_worker("M", "H")
    wet.set_weather(1.2); wet.harvest("M", "f")
    assert dry.last_yield("f") < wet.last_yield("f"), "a drought year yields less than a good year"


# ------------------------------------------------------ G-livestock-grow-and-breed (headline)
def test_livestock_grow_and_breed():
    w = Farm(); w.add_farm("Herd")
    w.add_animal("Herd", "Bull", sex="M", age=4, weight=8)
    w.add_animal("Herd", "Daisy", sex="F", age=4, weight=6, max_weight=10, growth=2)
    assert w.herd_size("Herd") == 2
    w.pass_season("Herd", 1)
    assert w.animal_age("Daisy") == 5.0 and w.animal_weight("Daisy") == 8.0, "animals age and grow each season"
    assert w.herd_size("Herd") == 3, "a mature dam + sire breed -- the herd grows (a calf)"
    assert w.manure("Herd") > 0.0, "living animals drop manure (the muck the fields need)"


# ------------------------------------------------------ G-slaughter-yields-meat
def test_slaughtering_an_animal_yields_meat():
    w = Farm(); w.add_farm("Herd")
    w.add_animal("Herd", "Hog", sex="M", age=4, weight=9)
    w.slaughter("Hog")
    assert not w.is_alive("Hog") and w.meat("Herd") == 9.0, "a slaughtered animal becomes meat (a food output)"


# ------------------------------------------------------ G-animals-die-of-old-age
def test_animals_die_of_old_age():
    w = Farm(); w.add_farm("Old")
    w.add_animal("Old", "Gaffer", sex="M", age=11, weight=8, lifespan=12)
    w.pass_season("Old", 2)
    assert not w.is_alive("Gaffer"), "past its lifespan the animal dies of old age"


# ------------------------------------------------------ G-loop-still-closes
def test_manure_still_closes_the_nutrient_loop():
    w = Farm(); w.add_farm("Manor"); w.hire_worker("Manor", "H")
    w.add_field("Manor", "f", area=1.0, fertility=10.0, per_worker=1.0, depletion=2.0, apply_cap=6.0)
    for _ in range(3):
        w.harvest("Manor", "f")
    assert w.fertility("f") == 4.0
    w.deliver_nightsoil("Manor", 6.0); w.fertilize("f")
    assert w.fertility("f") == 10.0, "returned manure/night-soil restores fertility (the loop closes)"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_farm():
    src = open(os.path.join(_ROOT, "worlds", "bigville_farm_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_farm.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"fm_harvest", "fm_fertilize", "fa_grow", "fa_breed", "fa_die_oldage", "fa_slaughter"} <= names, names
    harv = json.dumps([r for r in seed["rules"] if r["name"] == "fm_harvest"][0])
    assert "works" in harv and "weather_factor" in harv, "the harvest needs workers and is scaled by weather"
