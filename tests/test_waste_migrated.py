"""bigville R51 (block 362000): where does rubbish go? It does not vanish -- living produces
refuse that accumulates; unmanaged it is a health hazard; a raker carts it to the tip (moved,
not destroyed); dumping in the river relocates it as pollution. Conservation at the waste end.
Gates mirror the seed description.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_waste_world import BigvilleWasteWorld as Waste   # noqa: E402


# ------------------------------------------------------ G-rubbish-accumulates (headline)
def test_living_produces_refuse_that_accumulates():
    w = Waste()
    w.add_place("Row", occupants=6, waste_rate=0.5)
    assert w.place_refuse("Row") == 0.0
    w.live_a_day(2)
    assert w.place_refuse("Row") == 6.0, "rubbish does not vanish -- it piles up where it is made"


# ------------------------------------------------------ G-unmanaged-is-a-hazard (headline; social gradient)
def test_unmanaged_refuse_becomes_a_health_hazard():
    w = Waste(hazard_threshold=5.0)
    w.add_place("PoorRow", occupants=6, waste_rate=0.5)     # crowded -> more waste
    w.add_place("RichHouse", occupants=2, waste_rate=0.5)   # sparse -> less
    w.live_a_day(3)
    assert w.place_refuse("PoorRow") == 9.0 and w.is_hazard("PoorRow"), \
        "unmanaged refuse over the threshold is a health hazard"
    assert w.place_refuse("RichHouse") == 3.0 and not w.is_hazard("RichHouse"), \
        "the sparser house stays below the threshold -- the crowded district sickens first (a gradient)"


# ------------------------------------------------------ G-raker-carts-to-tip
def test_a_raker_carts_the_refuse_to_the_tip():
    w = Waste(hazard_threshold=5.0)
    w.add_place("PoorRow", occupants=6, waste_rate=0.5)
    w.live_a_day(3)
    assert w.is_hazard("PoorRow")
    total_before = w.total_waste()
    w.appoint_raker("Ned"); w.collect()
    assert w.place_refuse("PoorRow") == 0.0 and not w.is_hazard("PoorRow"), \
        "the raker clears the place -- the hazard is gone"
    assert w.tip_refuse() == 9.0, "the refuse is concentrated at the tip -- moved, not destroyed"
    assert w.total_waste() == total_before, "conservation: total waste is unchanged (it just moved)"


# ------------------------------------------------------ G-no-raker-no-collection
def test_without_a_raker_the_refuse_is_not_collected():
    w = Waste(hazard_threshold=5.0)
    w.add_place("PoorRow", occupants=6, waste_rate=0.5)
    w.live_a_day(3)
    w.collect()                                             # no raker appointed
    assert w.place_refuse("PoorRow") == 9.0 and w.is_hazard("PoorRow"), \
        "with no raker in office, nobody carts it away -- it stays and stays hazardous"


# ------------------------------------------------------ G-dumping-is-pollution
def test_dumping_in_the_river_relocates_the_problem():
    w = Waste()
    w.add_place("Hovel", occupants=4, waste_rate=1.0)
    w.live_a_day(3)                                          # 12
    total_before = w.total_waste()
    w.dump("Hovel")
    assert w.place_refuse("Hovel") == 0.0 and w.river_pollution() == 12.0, \
        "dumping moves the refuse to the river as pollution -- the problem is relocated, not removed"
    assert w.total_waste() == total_before, "conservation: it still exists, downstream"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_waste():
    src = open(os.path.join(_ROOT, "worlds", "bigville_waste_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_waste.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"wa_produce", "wa_hazard", "wa_collect", "wa_dump"} <= names, names
    coll = [r for r in seed["rules"] if r["name"] == "wa_collect"][0]
    assert ["town", "has_raker", "raker"] in coll["match"], "collection requires a raker (an office)"
