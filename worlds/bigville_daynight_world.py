"""BigvilleDayNightWorld -- bigville R59 (block 372000): the day/night cycle.

It actually gets dark, the residents notice, and it changes with the time of year. Everything
celestial is CALCULATED from the town's own clock (never fetched): daylight length is the
astronomical f(latitude, day-of-year) (long summer days, short winter nights); moon illumination
is the synodic cycle over sim-days. Cloud comes from the same seasonal weather generator, so a
clear full-moon night you can see and an overcast/new-moon night is blind.

A WORLD ADAPTER. No day/night/perception DECISION in Python -- dn_* are seed rules. The adapter
CALCULATES the sky inputs (sunrise/sunset, moon, cloud), injects them onto a Sky node, ticks, and
reads the light and who can see.
"""
from __future__ import annotations

import math
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402
from worlds.bigville_weather_world import seasonal_weather, YEAR_LEN   # noqa: E402

SYNODIC = 29.530588853        # days in a lunar cycle (the moon's period)
SEE_THRESHOLD = 0.25          # light level below which an unlit outdoor agent cannot see


def daylight_hours(latitude_deg, sim_day, *, year_len=YEAR_LEN):
    """CALCULATE the hours of daylight from latitude + day-of-year (the standard sunrise-equation
    astronomy). Long summer days, short winter nights -- a real seasonal swing, not a fetched number."""
    doy = sim_day % year_len
    lat = math.radians(latitude_deg)
    decl = math.radians(-23.44) * math.cos(2.0 * math.pi * (doy + 10) / year_len)   # solar declination
    x = max(-1.0, min(1.0, -math.tan(lat) * math.tan(decl)))
    return 24.0 * math.acos(x) / math.pi


def moon_illumination(sim_day, *, synodic=SYNODIC):
    """CALCULATE the moon's illuminated fraction from the sim-day (synodic cycle). New moon -> 0
    (dark), full moon -> 1 (bright). A pure function of the town's clock -- calculated, not fetched."""
    age = sim_day % synodic
    return (1.0 - math.cos(2.0 * math.pi * age / synodic)) / 2.0


class BigvilleDayNightWorld:
    def __init__(self, *, latitude=51.5):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_daynight"), None)
        self.latitude = float(latitude)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._sky = self.eng.add_node("Sky", {"hour": 12.0, "sunrise": 6.0, "sunset": 18.0,
                                              "moon_illum": 0.0, "cloud": 0.3, "is_night": 0.0,
                                              "light_level": 1.0, "see_threshold": SEE_THRESHOLD,
                                              "daylight_hours": 12.0})
        self.eng.add_edge_unchecked(self._town, "has_sky", self._sky)
        self._places = {}
        self._agents = {}
        self._at = {}

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_place(self, name, *, sheltered=False):
        p = self.eng.add_node("Place", {"name": name, "sheltered": 1.0 if sheltered else 0.0})
        self.eng.add_edge_unchecked(self._town, "has_place", p)
        self._places[name] = p
        return p

    def add_lamp(self, place):
        """A street lamp at a place -- unlit until the lamplighter lights it at nightfall."""
        lamp = self.eng.add_node("Lamp", {"lit": 0.0})
        self.eng.add_edge_unchecked(self._places[place], "has_lamp", lamp)
        return lamp

    def appoint_lamplighter(self, name):
        """Appoint the lamplighter (an office; composes with bigville_office). His round lights the
        lamps at night."""
        ll = self.eng.add_node("Agent", {"name": name, "role": "lamplighter"})
        self.eng.add_edge_unchecked(self._town, "has_lamplighter", ll)
        return ll

    def add_agent(self, name):
        a = self.eng.add_node("Agent", {"name": name, "sees_dark": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self._agents[name] = a
        return a

    def put(self, agent, place):
        a = self._agents[agent]; tgt = self._places[place]
        if self._at.get(agent) is not tgt:
            if self._at.get(agent) is not None:
                self.eng.remove_edge_unchecked(a, "at", self._at[agent])
            self.eng.add_edge_unchecked(a, "at", tgt)
            self._at[agent] = tgt

    def set_time(self, sim_day, hour, *, cloud=None):
        """Set the town clock to (sim_day, hour) and CALCULATE the sky: sunrise/sunset from the
        daylight length, moon illumination from the synodic cycle, cloud from the seasonal weather
        (unless overridden). Then settle the rules."""
        dl = daylight_hours(self.latitude, sim_day)
        cl = seasonal_weather(sim_day)[3] if cloud is None else float(cloud)
        for k, v in (("hour", float(hour)), ("sunrise", 12.0 - dl / 2.0), ("sunset", 12.0 + dl / 2.0),
                     ("moon_illum", moon_illumination(sim_day)), ("cloud", cl),
                     ("daylight_hours", dl)):
            self.eng.set_attr(self._sky, k, v)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def _sky_attr(self, k): return round(float(self.eng.node(self._sky)["attrs"][k]), 4)
    def light_level(self): return self._sky_attr("light_level")
    def is_night(self): return self._sky_attr("is_night") == 1.0
    def daylight_len(self): return self._sky_attr("daylight_hours")
    def moon(self): return self._sky_attr("moon_illum")
    def sees_dark(self, agent): return float(self.eng.node(self._agents[agent])["attrs"]["sees_dark"]) == 1.0
    def lamp_lit(self, lamp): return float(self.eng.node(lamp)["attrs"]["lit"]) == 1.0
