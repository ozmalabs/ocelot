"""bigville R69 (block 385000): world actions are a DATA STRUCTURE, not code. One generic rule
(ax_do) executes any ActionSpec recipe row (inputs, output, difficulty, time, wear); adding an
action is adding data. Gates mirror the generic engine.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_actions_world import BigvilleActionsWorld as Act   # noqa: E402


def _world():
    w = Act()
    w.add_actor("Wayland", role="smith"); w.add_actor("Colly", role="collier")
    for k, q in (("timber", 20), ("ore", 10), ("charcoal", 5), ("iron", 0), ("nails", 0)):
        w.set_stock(k, q)
    return w


# ------------------------------------------------------ G-actions-are-data (headline)
def test_different_actions_run_through_one_generic_rule():
    w = _world()
    w.do("Colly", "burn_charcoal")
    assert w.stock("timber") == 16.0 and w.stock("charcoal") == 6.0, "burn_charcoal: timber -4 -> charcoal +1 (from data)"
    w.do("Wayland", "smelt_iron")
    assert w.stock("ore") == 8.0 and w.stock("iron") == 1.0, "smelt_iron: ore -2 + charcoal -1 -> iron +1 (same rule)"


# ------------------------------------------------------ G-the-combination-is-data (headline)
def test_a_recipe_combines_its_inputs_from_data():
    w = _world()
    w.set_stock("iron", 2)
    w.do("Wayland", "forge_nails")
    assert w.stock("iron") == 1.0 and w.stock("charcoal") == 4.0 and w.stock("nails") == 5.0, \
        "forge_nails combines iron + charcoal -> 5 nails -- the combination is data, not code"


# ------------------------------------------------------ G-adding-an-action-is-just-data (headline)
def test_a_new_action_added_as_data_runs_with_no_code_change():
    w = _world()
    assert "saw_planks" not in w.actions()
    w.add_action("saw_planks", requires="sawyer", in1_kind="log", in1_qty=1,
                 out_kind="timber", out_qty=2, difficulty=0.8)      # a DATA row, no new rule/method
    w.add_actor("Sawyer", role="sawyer"); w.set_stock("log", 5)
    before = w.stock("timber")
    w.do("Sawyer", "saw_planks")
    assert w.stock("log") == 4.0 and w.stock("timber") == before + 2.0, "the new recipe runs on the same generic rule"


# ------------------------------------------------------ G-difficulty-is-data
def test_difficulty_is_data_and_tires_the_actor():
    w = _world()
    w.do("Wayland", "smelt_iron")          # difficulty 3.0
    assert w.fatigue("Wayland") == 3.0, "the actor is tired by the recipe's difficulty (a data field)"


# ------------------------------------------------------ G-no-python-decision + generic (source audit)
def test_the_executor_is_generic_and_names_no_action():
    src = open(os.path.join(_ROOT, "worlds", "bigville_actions_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_actions.json")))
    assert len(seed["rules"]) == 1 and seed["rules"][0]["name"] == "ax_do", "ONE generic rule executes all actions"
    rule = json.dumps(seed["rules"][0])
    for action in ("burn_charcoal", "smelt_iron", "forge_nails"):
        assert action not in rule, f"the rule must not name a specific action ({action}) -- it reads the data"
    specs = [n for n in seed["nodes"] if n["type"] == "ActionSpec"]
    assert len(specs) >= 3, "the actions are data rows (ActionSpec nodes)"
    for f in ("in1_kind", "out_kind", "difficulty", "time_minutes", "wear_rate"):
        assert f in specs[0]["attrs"], f"each recipe carries {f} as data"
