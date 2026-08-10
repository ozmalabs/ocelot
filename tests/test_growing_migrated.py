"""bigville R67 (block 383000): the season drives the harvest -- weather_factor is DERIVED from the
real seasonal weather (temperature/rain/sun), closing the weather->farm hook. Gates mirror wf_growing.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_growing_world import BigvilleGrowingWorld as Grow   # noqa: E402


def _season(temp, rain, sun):
    w = Grow(); w.add_farm("Manor"); w.add_field("Manor", "north", fertility=10.0, per_worker=1.0)
    w.hire_worker("Manor", "Hob")
    w.set_season(temperature=temp, rain=rain, sun=sun); w.harvest("Manor", "north")
    return w


# ------------------------------------------------------ G-good-season-yields-more (headline)
def test_a_good_season_yields_more_than_a_cold_drought():
    good = _season(20.0, 4.0, 0.8)         # warm, rain, sun
    poor = _season(3.0, 0.5, 0.2)          # cold, dry, dull
    assert good.weather_factor() > 1.0 and poor.weather_factor() < 0.5, "the season sets the growing factor"
    assert good.food_out("Manor") > poor.food_out("Manor") * 2, "a good season brings in far more than a cold drought"


# ------------------------------------------------------ G-weather-factor-is-derived (headline)
def test_the_weather_factor_is_derived_not_the_default():
    w = _season(18.0, 3.0, 0.7)
    assert w.weather_factor() != 1.0, "weather_factor is derived from the season, not left at the default 1.0"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_growing():
    src = open(os.path.join(_ROOT, "worlds", "bigville_growing_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_growing.json")))
    wf = json.dumps([r for r in seed["rules"] if r["name"] == "wf_growing"][0])
    assert "temperature" in wf and "rain" in wf and "sun" in wf and "weather_factor" in wf, \
        "the growing factor is derived from the season's temperature, rain, and sun"
