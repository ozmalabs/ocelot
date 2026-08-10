"""bigville R43 (block 336000): TOOLS + INVENTORY + OWNERSHIP -- adventure-game mechanics
(USE X ON Z / USE X WITH Y). A tool is an effectiveness multiplier; ownership is a
RECOGNIZED frame, not a world fact. Gates mirror BIGVILLE_TOOLS_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_tools_world import BigvilleToolsWorld   # noqa: E402


# ------------------------------------------------------ G-hands-bear-almost-nothing (headline)
def test_mining_with_hands_bears_almost_nothing_a_pick_works():
    w = BigvilleToolsWorld(); w.add_agent("Miner", energy=50.0)
    w.add_deposit("vein", resource="ore", richness=4.0, stock=100.0, gather_verb="mine")
    w.use("Miner", "mine", "vein")                       # bare hands
    hands_yield, hands_cost = w.last_yield("Miner"), w.last_effort("Miner")
    w.give_tool("Miner", "pick", mine=(1.0, 1.0))
    w.use("Miner", "mine", "vein", tool="pick")
    pick_yield, pick_cost = w.last_yield("Miner"), w.last_effort("Miner")
    assert hands_yield < 0.5 and hands_cost > pick_cost, "bare hands bear almost nothing at large cost"
    assert pick_yield > 10 * hands_yield, "a pick actually works"
    assert w.inventory("Miner", "ore") > 0, "the haul lands in the inventory"
    assert w.deposit_stock("vein") < 100.0, "the deposit is depleted (conservation)"


# ------------------------------------------------------ G-fishing-same
def test_fishing_with_hands_barely_a_rod_works():
    w = BigvilleToolsWorld(); w.add_agent("Anna", energy=50.0)
    w.add_deposit("pond", resource="fish", richness=3.0, stock=50.0, gather_verb="fish")
    w.use("Anna", "fish", "pond"); bare = w.last_yield("Anna")
    w.give_tool("Anna", "rod", fish=(1.0, 1.0)); w.use("Anna", "fish", "pond", tool="rod")
    assert w.last_yield("Anna") > 10 * bare, "a rod actually catches fish; hands barely"


# ------------------------------------------------------ G-wrong-tool-does-nothing
def test_you_can_only_use_a_tool_you_hold_and_it_must_fit():
    w = BigvilleToolsWorld(); w.add_agent("Bob", energy=50.0)
    w.add_deposit("vein", resource="ore", richness=4.0, stock=100.0, gather_verb="mine")
    w.give_tool("Bob", "rod", fish=(1.0, 1.0))
    w.use("Bob", "mine", "vein", tool="rod")             # a rod has no 'mine' fitness
    assert w.last_yield("Bob") == 0.0, "the wrong tool bears nothing (no matching fitness)"


# ------------------------------------------------------ G-knife-is-dual-use (headline)
def test_the_same_knife_helps_prep_and_wounds_a_person():
    w = BigvilleToolsWorld(); w.add_agent("Cook", cook_skill=0.6, energy=50.0)
    w.give_tool("Cook", "knife", prep=(1.5, 1.0), strike=(2.0, 1.0))   # one node, two fitnesses
    # USE X WITH Y: knife with food is a skill multiplier
    w.add_food("stew", taste=0.2, prep_bonus=0.4); w.use("Cook", "prep", "stew"); hands_q = w.food_quality("stew")
    w.add_food("stew2", taste=0.2, prep_bonus=0.4); w.use("Cook", "prep", "stew2", tool="knife")
    assert w.food_quality("stew2") > hands_q, "a knife multiplies prep skill (use knife WITH food)"
    # USE X ON Z: the SAME knife on a person is violence
    w.add_agent("Victim", health=10.0)
    w.use("Cook", "strike", "Victim"); fist = w.health("Victim")       # a punch
    w.use("Cook", "strike", "Victim", tool="knife")                    # the knife as a weapon
    assert w.health("Victim") < fist, "the same knife wounds far worse than a fist (use knife ON a person)"


# ------------------------------------------------------ G-owner-is-not-a-world-fact (headline)
def test_ownership_is_recognition_not_a_fact():
    w = BigvilleToolsWorld(); w.add_institution("TheInn")
    for n in ("Cook", "P1", "P2"): w.add_agent(n, energy=50.0)
    w.give_tool("Cook", "inn_knife", prep=(1.5, 1.0))     # the cook HOLDS it
    claim = w.claim_ownership("TheInn", "Cook", "inn_knife")
    assert w.owner_of("Cook", "inn_knife") is None, "a bare claim nobody recognizes owns nothing"
    for r in ("Cook", "P1", "P2"): w.recognize_ownership(r, claim)
    assert w.owner_of("Cook", "inn_knife") == "TheInn", "the inn owns it because the town RECOGNIZES the claim"
    assert w.recognition_of(claim) == 3, "ownership weight = Count(recognizers)"


# ------------------------------------------------------ G-holding-is-not-owning
def test_the_cook_uses_the_inns_knife_without_owning_it():
    w = BigvilleToolsWorld(); w.add_institution("TheInn")
    w.add_agent("Cook", cook_skill=0.6, energy=50.0)
    w.give_tool("Cook", "inn_knife", prep=(1.5, 1.0))
    claim = w.claim_ownership("TheInn", "Cook", "inn_knife")
    w.recognize_ownership("Cook", claim)
    w.add_food("stew", taste=0.2, prep_bonus=0.4)
    w.use("Cook", "prep", "stew", tool="inn_knife")       # holding is enough to USE
    assert w.food_quality("stew") > 0.0, "the cook can USE the inn's knife -- holding suffices"
    assert w.owner_of("Cook", "inn_knife") == "TheInn", "yet the inn, not the cook, is the recognized owner"


# ------------------------------------------------------ G-possession-does-not-transfer-ownership
def test_a_thief_holds_the_knife_but_does_not_become_owner():
    w = BigvilleToolsWorld(); w.add_institution("TheInn")
    for n in ("Cook", "P1", "P2", "Thief"): w.add_agent(n, energy=50.0)
    w.give_tool("Cook", "knife", strike=(2.0, 1.0))
    inn = w.claim_ownership("TheInn", "Cook", "knife")
    for r in ("Cook", "P1", "P2"): w.recognize_ownership(r, inn)
    # the thief takes it -- physically holds it -- and even claims it, but nobody recognizes him
    w.give_tool("Thief", "knife", strike=(2.0, 1.0))
    thief_claim = w.claim_ownership("Thief", "Thief", "knife")
    assert w.owner_of("Thief", "knife") is None, "possession + an unrecognized claim owns nothing -> theft"
    assert w.owner_of("Cook", "knife") == "TheInn", "the inn is still the recognized owner"


# ------------------------------------------------------ G-disputed-ownership
def test_split_recognition_is_disputed_and_the_substrate_does_not_adjudicate():
    w = BigvilleToolsWorld()
    for n in ("Alice", "Bob", "R1", "R2"): w.add_agent(n, energy=50.0)
    w.give_tool("Alice", "cart", pull=(1.0, 1.0))
    ca = w.claim_ownership("Alice", "Alice", "cart"); cb = w.claim_ownership("Bob", "Alice", "cart")
    w.recognize_ownership("Alice", ca); w.recognize_ownership("R1", ca)
    w.recognize_ownership("Bob", cb); w.recognize_ownership("R2", cb)
    assert w.recognition_of(ca) == w.recognition_of(cb) == 2
    assert w.owner_of("Alice", "cart") == "disputed", "split recognition = disputed; the substrate does not decide"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_tools_or_ownership():
    src = open(os.path.join(_ROOT, "worlds", "bigville_tools_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_tools.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"tl_gather", "tl_strike", "tl_prep", "oc_recognition"} <= names, names
    # tool use is gated on HOLDING, never owning; there is no owns-as-fact edge anywhere.
    blob = json.dumps(seed)
    assert '"owns"' not in blob, "owner must NOT be a world fact -- no owns edge"
    # ownership weight is a COUNT of recognizers (mirrors authority)
    oc = [r for r in seed["rules"] if r["name"] == "oc_recognition"][0]
    assert "Count" in json.dumps(oc) and "recognizes" in json.dumps(oc), \
        "ownership must be Count(recognizers), not a fact"
    gather = [r for r in seed["rules"] if r["name"] == "tl_gather"][0]
    assert ["agent", "holds", "slot"] in gather["match"], "use is gated on holding, not owning"
