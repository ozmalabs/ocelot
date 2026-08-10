"""bigville R60 (block 373000): darkness gates OUTDOOR labour -- you cannot reap a field you
cannot see. Composes bigville_farm + bigville_daynight: a farmhand in an open field is reaped by
DAY or by MOONLIGHT, but a moonless/overcast night brings nothing in; the self-lit FORGE carries
on after dark. Gates mirror the light-aware harvest.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_labour_world import BigvilleLabourWorld as Labour   # noqa: E402

_FULL_MOON, _NEW_MOON = 15, 0


def _scene():
    w = Labour()
    w.add_farm("Manor"); w.add_field("Manor", "north", fertility=10.0, per_worker=1.0)
    w.add_farmhand("Hodge", "Manor")
    w.add_forge("Forge"); w.add_smith("Wayland", "Forge")
    return w


# ------------------------------------------------------ G-reaped-by-day (headline)
def test_a_field_is_reaped_by_day():
    w = _scene()
    w.set_time(_NEW_MOON, 12.0, cloud=0.0)          # noon
    w.harvest("Manor", "north")
    assert not w.sees_dark("Hodge") and w.food_out("Manor") == 10.0, "by day he can see -- the full crop comes in"


# ------------------------------------------------------ G-cannot-reap-in-the-dark (headline)
def test_you_cannot_reap_a_field_you_cannot_see():
    w = _scene()
    w.set_time(_NEW_MOON, 23.0, cloud=0.0)          # moonless midnight
    w.harvest("Manor", "north")
    assert w.sees_dark("Hodge"), "on a moonless night the open field is dark -- he is blind"
    assert w.food_out("Manor") == 0.0, "nothing is brought in -- you cannot reap what you cannot see"


# ------------------------------------------------------ G-reaping-by-moonlight (headline)
def test_you_can_reap_by_moonlight():
    w = _scene()
    w.set_time(_FULL_MOON, 23.0, cloud=0.0)         # clear full-moon midnight
    w.harvest("Manor", "north")
    assert not w.sees_dark("Hodge"), "a clear full-moon night is bright enough to work by"
    assert w.food_out("Manor") == 10.0, "the harvest is brought in by moonlight -- the full crop"


# ------------------------------------------------------ G-overcast-blocks-the-moonlit-harvest
def test_an_overcast_full_moon_night_stops_the_harvest():
    w = _scene()
    w.set_time(_FULL_MOON, 23.0, cloud=0.95)        # full moon but overcast
    w.harvest("Manor", "north")
    assert w.sees_dark("Hodge") and w.food_out("Manor") == 0.0, "cloud blots the moon -- no reaping tonight"


# ------------------------------------------------------ G-the-forge-is-lit (headline)
def test_the_self_lit_forge_carries_on_after_dark():
    w = _scene()
    w.set_time(_NEW_MOON, 23.0, cloud=0.0)          # the same moonless night that blinds the field
    assert w.sees_dark("Hodge"), "the field hand is in the dark"
    assert not w.sees_dark("Wayland"), "but the smith at the sheltered, self-lit forge can see -- craftwork carries on"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_labour():
    src = open(os.path.join(_ROOT, "worlds", "bigville_labour_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_farm.json")))
    harv = json.dumps([r for r in seed["rules"] if r["name"] == "fm_harvest"][0])
    assert "sees_dark" in harv and "Filter" in harv, "the harvest counts only workers who can see (light-aware)"
