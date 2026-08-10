"""bigville: EATING and RESTING are DECISIONS, not world calls -- the world provides information + affordances.

Given a TURN to act (live), a villager reads its body state (hunger, fatigue) and the world's affordances
(food in the bag) and COLLAPSES over its options (eat vs rest) to the strongest pull above threshold, then
acts -- by its OWN decision. The adapter never calls eat()/rest(); it flags the turn and runs the decision.

  * hungry + holds food -> decides to EAT (hunger drops); hungry + NO food -> cannot (no affordance).
  * depleted -> decides to REST (reserve recovers); rested -> does nothing.
  * hungry AND tired -> the collapse addresses both, by urgency.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import BigvilleEconWorld, BREAD          # noqa: E402
from worlds.bigville_time_world import DAY                              # noqa: E402
from worlds.bigville_need_world import BigvilleNeedWorld               # noqa: E402

SQUARE = (14, 8)


def _hungry_holder(hunger=8, loaves=2):
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("c", SQUARE, coin=10, hunger_level=hunger, satiety=5)
    w.give_good("c", BREAD, qty=loaves)
    return w


# ------------------------------------------------------ G-eat-is-a-decision (headline)
def test_a_hungry_villager_holding_food_decides_to_eat():
    w = _hungry_holder(hunger=8, loaves=2)
    assert w.hunger_of("c") == 8 and w.inventory_of("c", BREAD) == 2, "hungry, with bread in the bag"
    w.live("c")                                                # give it a turn -- it decides
    assert w.hunger_of("c") < 8, "it CHOSE to eat -- hunger fell (no world call to eat)"
    assert w.inventory_of("c", BREAD) < 2, "and the bread it ate was consumed"


def test_a_hungry_villager_with_no_food_cannot_eat():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("c", SQUARE, coin=10, hunger_level=8, satiety=5)   # holds no food
    w.live("c")
    assert w.hunger_of("c") == 8, "no food in the bag -> it cannot decide to eat (the world gave no affordance)"


# ------------------------------------------------------ G-rest-is-a-decision (headline)
def test_a_depleted_villager_decides_to_rest():
    n = BigvilleNeedWorld(); n.add_mover("t", SQUARE); n.set_physique("t", sta_base=1.5)
    for _ in range(2):
        n.perform_task("t", stamina=True, stamina_cost=0.5)   # tire it out
    low = n.stamina_reserve("t")
    assert low < n.stamina("t"), "the reserve is depleted"
    n.live("t")                                               # give it a turn -- it decides to rest
    assert n.stamina_reserve("t") > low, "it CHOSE to rest -- the reserve recovered (no world call to rest)"


def test_a_sated_and_rested_villager_does_nothing():
    n = BigvilleNeedWorld(); n.add_mover("s", SQUARE); n.set_physique("s", sta_base=1.0)
    r0 = n.stamina_reserve("s")
    out = n.live("s")
    assert out["hunger"] == 0.0 and n.stamina_reserve("s") == r0, "no pressing need -> the agent does nothing"


# ------------------------------------------------------ G-collapse-arbitrates (headline)
def test_hungry_and_tired_the_collapse_addresses_both():
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("b", SQUARE, coin=10, hunger_level=8, satiety=5); w.set_physique("b", sta_base=2.0)
    w.give_good("b", BREAD, qty=2)                             # the world affords food to eat
    for _ in range(3):
        w.perform_task("b", stamina=True, stamina_cost=0.5)   # hard labour -> tired AND hungrier
    h0, r0 = w.hunger_of("b"), w.keeper_stamina_reserve("b")
    assert h0 > 8 and r0 < 2.0, "the work left it both hungry and depleted"
    w.live("b")                                               # one turn to act on its body
    assert w.hunger_of("b") < h0, "it ate (hunger fell)"
    assert w.keeper_stamina_reserve("b") > r0, "and it rested (reserve recovered) -- the collapse handled both"


# ------------------------------------------------------ G-the-decision-is-a-rule (source audit)
def test_the_action_is_a_collapse_decided_on_ticks_not_turns():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_body_choice.json")))
    choose = next(r for r in seed["rules"] if r["name"] == "bc_choose")
    assert json.dumps(choose["effects"]).count('"Argmax"') >= 1, "the choice is a COLLAPSE (Argmax over options)"
    # the decision rules fire while the agent is ALIVE (a persistent property) -- not on a transient turn flag
    assert '"alive"' in json.dumps(choose["where"]), "bc_choose fires while the agent is alive, every tick"
    eat = next(r for r in seed["rules"] if r["name"] == "bc_score_eat")
    assert "has_good" in json.dumps(eat), "the eat option's pull is GATED by the affordance (holding food)"
    src = open(os.path.join(_ROOT, "worlds", "bigville_need_world.py")).read()
    ticks = src.split("def run_ticks", 1)[1].split("\n    def ", 1)[0]
    assert "run_rules" in ticks and "deliberating" not in src, "the driver is run_ticks (the fixpoint); there are no turns"
    for act in ("self.eat(", "self.rest(", "self.perform_task(", "eat_meal("):
        assert act not in ticks, f"run_ticks must not call {act} -- the AGENT decides on each tick"
