"""bigville R60 (block 373000): the FORGE and the WOODSHOP are on the generated map -- fixed-point
places, sheltered and (the forge) self-lit, staffed with skilled makers wired via has_smith /
has_woodworker so the bigville_craft rules bind to the town's geography. The town's own smith can
forge a tool head. Gates mirror the map generator additions.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402
from worlds.bigville_map_generator import BigvilleMapGenerator as Map   # noqa: E402


def _town():
    return Map().generate()


# ------------------------------------------------------ G-forge-and-woodshop-on-the-map (headline)
def test_the_forge_and_woodshop_are_places_on_the_map():
    g = _town()
    assert g.role_place("forge") is not None, "the forge is a fixed-point place on the map"
    assert g.role_place("woodshop") is not None, "the woodshop is a fixed-point place on the map"
    forge = g.role_place("forge")
    assert float(g.eng.node(forge)["attrs"].get("sheltered", 0.0)) == 1.0, "the forge is sheltered (indoors)"


# ------------------------------------------------------ G-staffed-makers-wired (headline)
def test_the_trades_are_staffed_and_wired_as_makers():
    g = _town()
    smiths = g.eng.neighbours(g._town, "has_smith")
    woods = g.eng.neighbours(g._town, "has_woodworker")
    assert len(smiths) == 1 and len(woods) == 1, "the town has one blacksmith and one woodworker"
    assert g.eng.node(smiths[0])["attrs"]["name"] == "Wayland", "the smith is the forge's staff, wired as the maker"
    assert float(g.eng.node(smiths[0])["attrs"]["skill"]) > 0.0, "the maker carries a craft skill (=> tool quality)"


# ------------------------------------------------------ G-craft-works-in-the-town (headline, composition)
def test_the_towns_own_smith_can_forge_a_tool_head():
    eng = substrate_rs.Substrate()._inner
    eng.load_seed_manifest(manifest_for("bigville_craft"), None)   # the craft rules on the same engine
    g = Map(eng=eng).generate()
    store = eng.add_node("Store", {"iron": 10.0, "timber": 10.0, "charcoal": 10.0})
    eng.add_edge_unchecked(g._town, "has_store", store)
    smith = eng.neighbours(g._town, "has_smith")[0]
    for k, v in (("making_kind", "pick"), ("making_verb", "mine"), ("base_mult", 2.0),
                 ("base_effort", 1.0), ("mat_cost", 1.0), ("fuel_cost", 1.0), ("make_armed", 1.0)):
        eng.set_attr(smith, k, v if isinstance(v, str) else float(v))
    for _ in range(3):
        eng.force_all_dirty(); eng.run_rules(1000000)
    heads = list(eng.neighbours(g._town, "has_part"))
    assert len(heads) == 1, "the town's own smith forged a tool head (craft binds to the map's geography)"
    assert float(eng.node(store)["attrs"]["iron"]) == 9.0, "the forging consumed a unit of iron from the store"
