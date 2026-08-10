"""bigville R56/R58 (blocks 369000, 371000): weather is real, changing, EMBODIED, and ESTIMATED
FROM THE SEASON at the sim's own timescale. The town runs on its own clock, so a real-date
forecast is the wrong instrument -- the weather is generated from the sim's season phase (warm
sunny summers, cold cloudy wet winters), deterministically. An agent outside is exposed (wet in
the rain, hot in the sun, cold on a cold day); one inside a building stays dry and warm. Gates
mirror the seed + generator.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_weather_world import BigvilleWeatherWorld as Weather, seasonal_weather   # noqa: E402


def _town():
    w = Weather()
    w.add_place("Field", sheltered=False)
    w.add_place("Cottage", sheltered=True, indoor_temp=20.0)
    w.add_agent("Ploughman"); w.add_agent("Clerk")
    w.put("Ploughman", "Field"); w.put("Clerk", "Cottage")
    return w


# ------------------------------------------------------ G-summer-warmer-than-winter (headline)
def test_the_weather_is_estimated_from_the_season():
    summer = [seasonal_weather(d) for d in range(195, 205)]     # around the hottest sim-day
    winter = [seasonal_weather(d) for d in range(15, 25)]       # around the coldest
    st = sum(x[0] for x in summer) / 10; wt = sum(x[0] for x in winter) / 10
    sc = sum(x[3] for x in summer) / 10; wc = sum(x[3] for x in winter) / 10
    assert st > wt + 10.0, "summer is much warmer than winter (a real seasonal curve)"
    assert sc < wc, "summer is sunnier (less cloud); winter is cloudier"


# ------------------------------------------------------ G-deterministic-no-wall-clock
def test_the_same_sim_day_gives_the_same_weather():
    assert seasonal_weather(42) == seasonal_weather(42), "reproducible: a function of the sim-day only"
    assert seasonal_weather(42) != seasonal_weather(43), "yet it varies day to day"


# ------------------------------------------------------ G-outside-wet-inside-dry (headline)
def test_a_rainy_day_wets_the_outdoor_worker_and_not_the_indoor_one():
    w = _town()
    w.set_day(temperature=8.0, rain=12.0, sun=0.1, cloud=0.9)
    assert w.wetness("Ploughman") == 12.0 and w.is_exposed("Ploughman"), "outside in the rain -> wet"
    assert w.wetness("Clerk") == 0.0 and not w.is_exposed("Clerk"), "inside -> dry (sheltered)"
    assert w.felt_temp("Clerk") == 20.0, "inside -> warm (the indoor temperature), whatever the weather"


# ------------------------------------------------------ G-sun-load-heats-the-outdoors (headline)
def test_the_sun_load_heats_those_outside():
    w = _town()
    w.set_day(temperature=26.0, rain=0.0, sun=1.0, cloud=0.0)
    assert w.felt_temp("Ploughman") == 34.0, "outside felt_temp = ambient (26) + sun load (1.0 * 8)"
    assert w.felt_temp("Clerk") == 20.0, "inside stays at the indoor temperature -- comfortable"


# ------------------------------------------------------ G-come-in-out-of-the-rain
def test_coming_indoors_dries_you_off():
    w = _town()
    w.set_day(temperature=8.0, rain=12.0, sun=0.1, cloud=0.9)
    assert w.wetness("Ploughman") == 12.0
    w.put("Ploughman", "Cottage")
    w.set_day(temperature=8.0, rain=0.0, sun=0.1, cloud=0.5)
    assert w.wetness("Ploughman") == 9.0 and w.felt_temp("Ploughman") == 20.0, "indoors you dry off and warm up"


# ------------------------------------------------------ G-a-generated-season-drives-the-body
def test_a_generated_winter_run_leaves_the_outdoor_worker_cold_and_wet():
    w = _town()
    w.run_days(range(15, 25))          # a generated winter run
    assert w.felt_temp("Ploughman") < 10.0 and w.wetness("Ploughman") > 0.0, "outside: cold and wet by winter's end"
    assert w.felt_temp("Clerk") == 20.0 and w.wetness("Clerk") == 0.0, "inside: warm and dry throughout"


# ------------------------------------------------------ G-no-python-decision + not-fetched (source audit)
def test_no_python_decides_and_the_weather_is_not_a_real_date_fetch():
    src = open(os.path.join(_ROOT, "worlds", "bigville_weather_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    # the town runs on its own clock -- no real-date forecast fetch
    for fetched in ("open-meteo", "urllib", "fetch_forecast", "api.open"):
        assert fetched.lower() not in src.lower(), f"weather must be estimated from the season, not fetched: {fetched}"
    assert "seasonal_weather" in src, "the weather is generated from the sim's season phase"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_weather.json")))
    out = json.dumps([r for r in seed["rules"] if r["name"] == "we_outside"][0])
    assert "rain" in out and "temperature" in out and "sun" in out, "models ambient temperature, rain, sun load"
    assert "sheltered" in out, "exposure is gated on being outside (unsheltered) -- the map provides shelter"
