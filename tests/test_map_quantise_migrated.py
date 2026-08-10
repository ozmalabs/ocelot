"""bigville R45 (blocks 341000/342000): MULTIPLE QUANTISATIONS of the generated map, with
HIERARCHICAL LANDMARK routing (not a town-wide flood -- people route to landmarks in steps,
and the cost is invariant to town size), plus a lazy foveated room tile-grain that enables
bumping / squeezing past. Gates mirror BIGVILLE_MAP_PREREG.md.
"""
from __future__ import annotations

import copy
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_map_quantise import QuantisedMap            # noqa: E402
from worlds.bigville_map_generator import DEFAULT_SPEC           # noqa: E402


# ------------------------------------------------------ G-landmark-route (headline)
def test_routing_is_landmark_based_in_steps():
    q = QuantisedMap(seed=7)
    r = q.landmark_route("house1", "bedroom", "Church", "counsel")
    # the coarse plan is a short landmark chain: your building -> the square -> the church
    assert r["landmarks"] == ["house1", "Square", "Church"], "route to landmarks in steps"
    # refined locally at each end: out to your entrance, across, in to the counsel room
    assert r["steps"][0] == "house1:bedroom" and r["steps"][-1] == "Church:counsel"
    assert "Square" in r["steps"], "the square is the landmark you pass through"
    # a same-building trip never leaves the building (no square)
    inside = q.landmark_route("Inn", "kitchen", "Inn", "guestroom")
    assert inside["landmarks"] == ["Inn"] and "Square" not in inside["steps"]


# ------------------------------------------------------ G-cost-invariant-to-town-size (headline)
def test_landmark_routing_cost_is_independent_of_town_size():
    small = QuantisedMap(seed=7)
    big_spec = copy.deepcopy(DEFAULT_SPEC); big_spec["houses"]["count"] = 40
    big = QuantisedMap(seed=7, spec=big_spec)
    rs = small.landmark_route("house1", "bedroom", "Church", "counsel")
    rb = big.landmark_route("house1", "bedroom", "Church", "counsel")
    assert rs["touched"] == rb["touched"], \
        "a landmark route touches only the endpoint buildings -- cost is invariant to town size"
    assert big.flood_cost_would_be() > small.flood_cost_would_be(), \
        "a town-wide flood, by contrast, touches ~every room -- it grows with the town"
    assert rs["touched"] < small.flood_cost_would_be(), "landmark routing is much cheaper than the flood"


# ------------------------------------------------------ G-multi-grain
def test_the_grains_fall_out_of_the_hierarchy():
    q = QuantisedMap(seed=7)
    r = q.landmark_route("house1", "bedroom", "Church", "counsel")
    # coarse grain = the landmark chain; building grain = the interior steps within a landmark
    assert len(r["landmarks"]) == 3
    interior_at_church = [s for s in r["steps"] if s.startswith("Church:")]
    assert interior_at_church == ["Church:nave", "Church:counsel"], "building grain refines within the landmark"


# ------------------------------------------------------ G-lazy-fine-foveated (headline)
def test_the_fine_tile_grain_is_lazy_and_foveated():
    q = QuantisedMap(seed=7)
    assert q.tiles_in("Inn", "kitchen") == 0, "no room is tiled until it is focused"
    assert q.focus("Inn", "kitchen", w=2, h=2) == 4, "focusing a room materialises its tile grid on demand"
    assert q.tiles_in("Inn", "taproom") == 0, "an UNfocused room stays tile-less (foveation)"


# ------------------------------------------------------ G-bump / G-squeeze-past
def test_the_fine_grain_makes_bumping_and_squeeze_past_visible():
    q = QuantisedMap(seed=7); q.focus("Inn", "kitchen", w=2, h=2)
    q.occupy("Cook", "Inn", "kitchen", 1, 1)
    q.occupy("Server", "Inn", "kitchen", 1, 1)      # same tile
    q.occupy("Potboy", "Inn", "kitchen", 0, 0)      # different tile
    assert q.is_bump("Cook", "Server") and not q.is_bump("Cook", "Potboy")
    assert q.must_squeeze_past("Potboy", "Inn", "kitchen", 1, 1), "stepping onto an occupied tile squeezes past"
    assert not q.must_squeeze_past("Potboy", "Inn", "kitchen", 0, 1), "an empty tile does not"


# ------------------------------------------------------ G-no-flood-no-decision (source audit)
def test_routing_is_hierarchical_and_makes_no_decision():
    src = open(os.path.join(_ROOT, "worlds", "bigville_map_quantise.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"the quantiser must not run a rule engine: {forbidden}"
    # the town-wide flood is gone: routing is landmark/hierarchical over the semantic map
    assert "run_rules" not in src and "bigville_move_nav" not in src, \
        "routing must not flood -- it routes to landmarks in steps"
    assert "landmark_route" in src and "flood_cost_would_be" in src
