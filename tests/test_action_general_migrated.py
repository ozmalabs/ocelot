"""bigville R75 (block 393000): the generic action -- perform an action on N THINGS with Y TOOLS
(or none). One engine (an_meet / an_use_tool / an_done) runs any action; forge, burn, and assemble
are all instances. Gates mirror the generic engine.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_action_world import BigvilleActionWorld as Act   # noqa: E402


def _world():
    w = Act()
    w.add_actor("Smith", role="smith"); w.add_actor("Colly", role="collier")
    w.add_tool("hammer", wear=0.05); w.add_tool("crucible", wear=0.1)
    for k, q in (("wood", 20), ("iron", 5), ("charcoal", 10), ("copper", 6), ("tin", 2),
                 ("nails", 0), ("bronze", 0), ("pick_head", 1), ("pick_handle", 1), ("pick", 0)):
        w.set_stock(k, q)
    return w


# ------------------------------------------------------ G-one-input-no-tools (headline)
def test_an_action_on_one_thing_with_no_tools():
    w = _world()
    w.install_action({"name": "burn", "requires": "collier", "inputs": [["wood", 4]], "tools": [],
                      "out": ["charcoal", 1], "difficulty": 2.0})
    w.do("Colly", "burn")
    assert w.qty("wood") == 16.0 and w.qty("charcoal") == 11.0, "N=1, Y=0: one input consumed, output made, no tool"


# ------------------------------------------------------ G-two-inputs-one-tool (headline)
def test_an_action_on_two_things_with_a_tool_that_wears():
    w = _world()
    w.install_action({"name": "forge_nails", "requires": "smith", "inputs": [["iron", 1], ["charcoal", 1]],
                      "tools": ["hammer"], "out": ["nails", 5], "difficulty": 1.5})
    w.do("Smith", "forge_nails")
    assert w.qty("iron") == 4.0 and w.qty("charcoal") == 9.0 and w.qty("nails") == 5.0, "N=2 inputs both consumed"
    assert w.tool_condition("hammer") == 0.95, "Y=1: the hammer was used and WORE (0.05)"


# ------------------------------------------------------ G-three-inputs (headline; any N)
def test_an_action_on_three_things():
    w = _world()
    w.install_action({"name": "cast_bronze", "requires": "smith", "inputs": [["copper", 3], ["tin", 1], ["charcoal", 2]],
                      "tools": ["crucible"], "out": ["bronze", 1], "difficulty": 3.0})
    w.do("Smith", "cast_bronze")
    assert w.qty("copper") == 3.0 and w.qty("tin") == 1.0 and w.qty("charcoal") == 8.0 and w.qty("bronze") == 1.0, \
        "N=3 inputs all consumed by the same generic engine -- any number of things"


# ------------------------------------------------------ G-assemble-is-just-an-action (headline)
def test_assembly_is_just_an_action_using_a_hammer_on_two_things():
    w = _world()
    w.install_action({"name": "assemble_pick", "requires": "smith", "inputs": [["pick_head", 1], ["pick_handle", 1]],
                      "tools": ["hammer"], "out": ["pick", 1], "difficulty": 0.5})
    w.do("Smith", "assemble_pick")
    assert w.qty("pick_head") == 0.0 and w.qty("pick_handle") == 0.0 and w.qty("pick") == 1.0, \
        "assemble = an action on two things with a hammer -- no special rule"
    assert w.tool_condition("hammer") == 0.95, "the hammer wore, like any tool used in any action"


# ------------------------------------------------------ G-adding-an-action-is-data + generic (source audit)
def test_the_engine_is_generic_and_names_no_action():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_action_general.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"an_meet", "an_use_tool", "an_done_bulk"} <= names, "generic rules: meet N inputs, use Y tools, complete"
    body = json.dumps([r for r in seed["rules"] if r["name"].startswith("an_")])
    for action in ("burn", "forge", "nails", "bronze", "assemble", "pick", "hammer", "crucible"):
        assert action not in body, f"the engine must name no action/item ({action}) -- it reads the data"
    src = open(os.path.join(_ROOT, "worlds", "bigville_action_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
