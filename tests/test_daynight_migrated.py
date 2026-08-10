"""bigville R59 (block 372000): the day/night cycle -- it gets dark, the residents notice, and it
changes with the time of year. Daylight length and moon illumination are CALCULATED from the
town's own clock (not fetched). A clear full-moon night you can see; a new-moon or overcast night
is blind. The lamplighter lights the lamps at nightfall. Gates mirror the seed + calculations.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_daynight_world import (BigvilleDayNightWorld as Day,   # noqa: E402
                                            daylight_hours, moon_illumination)

_FULL_MOON, _NEW_MOON = 15, 0     # sim-days at full / new moon


# ------------------------------------------------------ G-it-gets-dark-and-residents-notice (headline)
def test_it_gets_dark_at_night_and_the_resident_notices():
    w = Day(); w.add_place("Square"); w.add_agent("Tom"); w.put("Tom", "Square")
    w.set_time(_NEW_MOON, 12.0, cloud=0.0)          # noon
    assert not w.is_night() and not w.sees_dark("Tom"), "by day it is light -- he can see"
    w.set_time(_NEW_MOON, 23.0, cloud=0.0)          # midnight, no moon
    assert w.is_night() and w.sees_dark("Tom"), "at night with no moon it is dark -- he notices (sees_dark)"


# ------------------------------------------------------ G-a-moonlit-night-you-can-see (headline)
def test_a_clear_full_moon_night_you_can_see_but_a_new_moon_night_is_blind():
    w = Day(); w.add_place("Square"); w.add_agent("Tom"); w.put("Tom", "Square")
    w.set_time(_FULL_MOON, 23.0, cloud=0.0)         # full moon, clear
    assert w.is_night() and not w.sees_dark("Tom"), "a clear full-moon night is bright enough to see by"
    w.set_time(_NEW_MOON, 23.0, cloud=0.0)          # new moon, clear
    assert w.sees_dark("Tom"), "a new-moon night is blind -- no moon to light it"


# ------------------------------------------------------ G-cloud-blocks-the-moon (headline)
def test_an_overcast_full_moon_night_is_still_blind():
    w = Day(); w.add_place("Square"); w.add_agent("Tom"); w.put("Tom", "Square")
    w.set_time(_FULL_MOON, 23.0, cloud=0.95)        # full moon, but overcast
    assert w.sees_dark("Tom"), "cloud blocks the moon -- an overcast full-moon night is dark (moon AND cloud matter)"


# ------------------------------------------------------ G-daylight-changes-with-the-season (headline)
def test_the_daylight_length_changes_with_the_time_of_year():
    midsummer = daylight_hours(51.5, 172)
    midwinter = daylight_hours(51.5, 355)
    assert midsummer > 15.0 and midwinter < 9.0, "long summer days, short winter nights (calculated from latitude)"
    assert midsummer > midwinter + 6.0, "a real seasonal swing in day length"


# ------------------------------------------------------ G-the-moon-cycles
def test_the_moon_waxes_and_wanes():
    assert moon_illumination(_FULL_MOON) > 0.95, "full moon is bright"
    assert moon_illumination(_NEW_MOON) < 0.05, "new moon is dark"


# ------------------------------------------------------ G-the-lamplighter-earns-his-keep (headline)
def test_the_lamplighter_lights_the_lamps_and_lets_you_see():
    dark = Day(); dark.add_place("Square"); lamp = dark.add_lamp("Square")
    dark.add_agent("Tom"); dark.put("Tom", "Square")
    dark.set_time(_NEW_MOON, 23.0, cloud=0.0)       # no lamplighter appointed
    assert not dark.lamp_lit(lamp) and dark.sees_dark("Tom"), "no lamplighter -> the lamp stays dark, the street is blind"

    lit = Day(); lit.add_place("Square"); l2 = lit.add_lamp("Square")
    lit.appoint_lamplighter("Lucius"); lit.add_agent("Tom"); lit.put("Tom", "Square")
    lit.set_time(_NEW_MOON, 23.0, cloud=0.0)
    assert lit.lamp_lit(l2) and not lit.sees_dark("Tom"), "the lamplighter lights it -> the lit lamp lets you see"
    lit.set_time(_NEW_MOON, 12.0, cloud=0.0)        # noon
    assert not lit.lamp_lit(l2), "by day the lamps are doused -- no oil burnt in daylight"


# ------------------------------------------------------ G-indoors-is-candlelit
def test_indoors_you_can_see_at_night():
    w = Day(); w.add_place("Inn", sheltered=True); w.add_agent("Nan"); w.put("Nan", "Inn")
    w.set_time(_NEW_MOON, 23.0, cloud=0.0)
    assert not w.sees_dark("Nan"), "inside a building it is candlelit -- you can see whatever the sky"


# ------------------------------------------------------ G-no-python-decision + calculated-not-fetched
def test_no_python_decides_and_the_sky_is_calculated_not_fetched():
    src = open(os.path.join(_ROOT, "worlds", "bigville_daynight_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    for fetched in ("open-meteo", "urllib", "api.open", "requests.get"):
        assert fetched.lower() not in src.lower(), f"the sky is calculated from the clock, not fetched: {fetched}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_daynight.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"dn_sky", "dn_perceive", "dn_lamplighter_lights", "dn_lamp_saves"} <= names, names
    sky = json.dumps([r for r in seed["rules"] if r["name"] == "dn_sky"][0])
    assert "moon_illum" in sky and "cloud" in sky and "is_night" in sky, "light = moon and cloud at night, sun by day"
