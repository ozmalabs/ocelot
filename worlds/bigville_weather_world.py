"""BigvilleWeatherWorld -- bigville R56/R58 (blocks 369000, 371000): real, changing, embodied
weather ESTIMATED FROM THE SEASON at the sim's own timescale.

The town runs on its OWN clock, so a real-date forecast is the wrong instrument -- the town's
"July" is not the real July. Instead the weather is GENERATED from the sim's season phase: a
seasonal climatology (temperature on a seasonal curve, cloud/rain/sun drawn around seasonal
means) at the town's timescale, deterministically (a shader-style hash per sim-day -- reproducible,
no RNG state, no wall clock). The climate PARAMETERS are a temperate-climate profile (real
climatology informs them); the specific days are estimated, not fetched.

The embodied effect is graph-native (unchanged): an agent outside is exposed (wet in the rain,
hot in the sun, cold on a cold day); an agent inside a building stays dry and warm.

A WORLD ADAPTER. No exposure DECISION in Python -- we_* are seed rules. The adapter estimates the
season's weather (admissible world generation, like synthesizing any environmental input), places
agents inside/outside, injects the day's weather, and reads their bodies.
"""
from __future__ import annotations

import json
import math
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402

YEAR_LEN = 360        # sim-days in a sim-year (the town's calendar, not the real one)
SUN_HEAT = 8.0        # felt_temp gain per unit of sun load (mirrors the seed constant)


def _hash01(n):
    """Deterministic pseudo-random in [0,1) from an integer -- a shader-style hash. Same sim-day
    always gives the same draw (reproducible gates), no RNG state, no wall clock."""
    x = math.sin(n * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


def seasonal_weather(sim_day, *, year_len=YEAR_LEN, annual_mean_c=10.0, seasonal_amp_c=9.0,
                     hottest_doy=200, noise_c=4.0, seed=0):
    """ESTIMATE a day's weather from the SIM's season phase (not a real-date forecast). Returns
    (temperature_C, rain_mm, sun_0to1, cloud_0to1). Warm sunny summers, cold cloudy wet winters,
    day-to-day variation -- deterministic in sim_day. Temperate-climate default parameters."""
    doy = sim_day % year_len
    summ = math.cos(2.0 * math.pi * (doy - hottest_doy) / year_len)   # +1 at hottest, -1 at coldest
    k = sim_day + seed * 1000
    temp = annual_mean_c + seasonal_amp_c * summ + noise_c * (_hash01(k) - 0.5) * 2.0
    cloud_mean = min(0.9, max(0.1, 0.55 - 0.25 * summ))              # cloudier in the cold half
    cloud = min(1.0, max(0.0, cloud_mean + 0.3 * (_hash01(k + 7) - 0.5) * 2.0))
    rain = max(0.0, (cloud - 0.4)) * 20.0 * _hash01(k + 13)          # rain when it is cloudy
    sun = min(1.0, max(0.0, 1.0 - cloud))                           # daytime sun availability
    return (round(temp, 2), round(rain, 2), round(sun, 2), round(cloud, 2))


class BigvilleWeatherWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_weather"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville", "temperature": 15.0, "rain": 0.0,
                                                "sun": 0.5, "day": 0.0, "cloud": 0.5})
        self._places = {}
        self._agents = {}
        self._at = {}

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_place(self, name, *, sheltered, indoor_temp=20.0):
        p = self.eng.add_node("Place", {"name": name, "sheltered": 1.0 if sheltered else 0.0,
                                        "indoor_temp": float(indoor_temp)})
        self.eng.add_edge_unchecked(self._town, "has_place", p)
        self._places[name] = p
        return p

    def add_agent(self, name):
        a = self.eng.add_node("Agent", {"name": name, "wetness": 0.0, "felt_temp": 15.0,
                                        "exposed": 0.0, "weather_seen": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self._agents[name] = a
        return a

    def put(self, agent, place):
        """Move an agent to a place (one location at a time) -- inside a building or out of doors."""
        a = self._agents[agent]; tgt = self._places[place]
        if self._at.get(agent) is not tgt:
            if self._at.get(agent) is not None:
                self.eng.remove_edge_unchecked(a, "at", self._at[agent])
            self.eng.add_edge_unchecked(a, "at", tgt)
            self._at[agent] = tgt

    def set_day(self, *, temperature, rain, sun, cloud=0.5):
        """Inject a day's weather onto the town and settle its effects. Increments town.day so the
        epoch guard applies each day's weather exactly once per agent."""
        self.eng.set_attr(self._town, "day", float(self.eng.node(self._town)["attrs"]["day"]) + 1.0)
        self.eng.set_attr(self._town, "temperature", float(temperature))
        self.eng.set_attr(self._town, "rain", float(rain))
        self.eng.set_attr(self._town, "sun", float(sun))
        self.eng.set_attr(self._town, "cloud", float(cloud))
        self._run()

    def generate_day(self, sim_day, **climate):
        """ESTIMATE the season's weather for a sim-day and inject it (the seasonal generator, not a
        real-date fetch). Returns the (temperature, rain, sun, cloud) it estimated."""
        t, r, s, c = seasonal_weather(sim_day, **climate)
        self.set_day(temperature=t, rain=r, sun=s, cloud=c)
        return (t, r, s, c)

    def run_days(self, sim_days, **climate):
        """Drive the sim through a run of sim-days, estimating each day's weather from the season."""
        return [self.generate_day(d, **climate) for d in sim_days]

    # ------------------------------------------------- glass-box read-offs
    def wetness(self, agent): return round(float(self.eng.node(self._agents[agent])["attrs"]["wetness"]), 4)
    def felt_temp(self, agent): return round(float(self.eng.node(self._agents[agent])["attrs"]["felt_temp"]), 4)
    def is_exposed(self, agent): return float(self.eng.node(self._agents[agent])["attrs"]["exposed"]) == 1.0
