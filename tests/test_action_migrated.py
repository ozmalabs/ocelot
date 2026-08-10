"""bigville cognitive C6 (block 330000): the cost & impact of action -- the thermodynamics
of agency. Work costs energy and produces (conserved) output; recovering a drive consumes a
real resource; metabolism forces the loop. Gates mirror BIGVILLE_ACTION_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_action_world import BigvilleActionWorld   # noqa: E402


# ------------------------------------------------------ G-work-costs-energy (headline)
def test_work_costs_energy_and_no_energy_cannot_work():
    w = BigvilleActionWorld(deposit_stock=10.0)
    w.add_agent("F", energy=10.0, work_cost=2.0, work_yield=3.0)
    w.work("F")
    assert w.energy("F") == 8.0, "working spends work_cost energy"
    weak = BigvilleActionWorld(deposit_stock=10.0)
    weak.add_agent("W", energy=1.0, work_cost=2.0)
    weak.work("W")
    assert weak.energy("W") == 1.0 and weak.store_stock() == 0.0, "energy < cost -> cannot work, no output"


# ------------------------------------------------------ G-work-has-impact (headline)
def test_work_produces_output_and_no_input_no_output():
    w = BigvilleActionWorld(deposit_stock=10.0)
    w.add_agent("F", work_yield=3.0)
    w.work("F")
    assert w.store_stock() == 3.0 and w.last_output("F") == 3.0, "work produces output into the store"
    empty = BigvilleActionWorld(deposit_stock=0.0)
    empty.add_agent("F", work_yield=3.0)
    empty.work("F")
    assert empty.store_stock() == 0.0, "no resource in the deposit -> no output"


# ------------------------------------------------------ G-recovering-costs (headline)
def test_recovering_hunger_consumes_a_real_food_unit():
    w = BigvilleActionWorld(deposit_stock=10.0)
    w.add_agent("F", hunger=2.0, satiation=1.0)
    w.work("F")                       # produce food
    before = w.store_stock()
    w.eat("F")
    assert w.store_stock() == before - 1.0, "eating consumes one food unit (conserved)"
    assert w.hunger("F") == 1.0, "and reduces hunger by the satiation"
    # no food -> cannot recover for free
    starving = BigvilleActionWorld(deposit_stock=0.0)
    starving.add_agent("S", hunger=5.0)
    starving.eat("S")
    assert starving.hunger("S") == 5.0, "no food -> hunger cannot be reduced"


# ------------------------------------------------------ G-conservation
def test_conservation_across_work_and_eat():
    w = BigvilleActionWorld(deposit_stock=10.0)
    w.add_agent("F", work_yield=3.0, hunger=2.0)
    d0, s0 = w.deposit_stock(), w.store_stock()
    w.work("F")
    assert (d0 - w.deposit_stock()) == (w.store_stock() - s0) == w.last_output("F"), \
        "extracted == deposit decrease == store increase (no creation from nothing)"
    # partial take: cannot over-extract a nearly-empty deposit
    small = BigvilleActionWorld(deposit_stock=2.0)
    small.add_agent("F", work_yield=3.0)
    small.work("F")
    assert small.deposit_stock() == 0.0 and small.store_stock() == 2.0, "output floored at the stock (min take)"


# ------------------------------------------------------ G-the-loop-is-not-free (falsifier)
def test_metabolism_forces_the_loop():
    # metabolism ON: an idle agent runs down (energy -> 0, hunger climbs)
    w = BigvilleActionWorld()
    w.add_agent("Idle", energy=5.0, hunger=0.0, metabolic_cost=1.0, metabolic_hunger=0.5)
    w.metabolize(6)
    assert w.energy("Idle") == 0.0 and w.hunger("Idle") > 0.0, "the cost of living runs an idle agent down"
    # metabolism OFF: it coasts (nothing is spent)
    coast = BigvilleActionWorld()
    coast.add_agent("Coast", energy=5.0, hunger=0.0, metabolic_cost=0.0, metabolic_hunger=0.0)
    coast.metabolize(6)
    assert coast.energy("Coast") == 5.0 and coast.hunger("Coast") == 0.0, "no cost -> no forced loop"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_action():
    src = open(os.path.join(_ROOT, "worlds", "bigville_action_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_action.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"ac_work", "ac_eat", "ac_rest", "ac_metabolize"} <= names, names
