"""bigville R71 (block 388000): containers -- a class of the same kind as pile. A Container (barrel)
is a physical, located world-fact with a capacity that holds contents; filling/emptying moves
matter (conserved), bounded by capacity, by access. Gates mirror ct_fill / ct_empty.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_container_world import BigvilleContainerWorld as Cont   # noqa: E402


def _yard(loose=15.0, cap=10.0, start=0.0):
    w = Cont(); w.add_agent("Tom"); w.add_pile("charcoal", loose)
    w.add_container("barrel1", kind="barrel", holds="charcoal", capacity=cap, qty=start)
    return w


# ------------------------------------------------------ G-container-is-a-peer-of-pile (headline)
def test_a_container_is_a_located_world_fact_like_a_pile():
    w = _yard()
    assert w.is_container("barrel1") and w.located("barrel1"), "a barrel is a Container, a located world-fact (like a pile)"
    assert w.capacity("barrel1") == 10.0, "but it has a capacity and holds contents -- the pile's sibling class"


# ------------------------------------------------------ G-fill-bounded-by-capacity (headline)
def test_a_container_cannot_be_overfilled():
    w = _yard(loose=15.0, cap=10.0)
    w.fill("Tom", "barrel1", 100.0)                    # ask for more than fits
    assert w.contents("barrel1") == 10.0, "only its capacity goes in -- never overfilled"
    assert w.loose_qty("charcoal") == 5.0, "the rest stays loose (15 - 10)"


# ------------------------------------------------------ G-fill-and-empty-conserve (headline)
def test_filling_and_emptying_conserve_matter():
    w = _yard(loose=15.0, cap=10.0)
    t0 = w.total("charcoal")
    w.fill("Tom", "barrel1", 8.0)
    assert w.contents("barrel1") == 8.0 and w.loose_qty("charcoal") == 7.0 and w.total("charcoal") == t0, \
        "filling MOVES matter into the barrel -- nothing created"
    w.empty("Tom", "barrel1", 3.0)
    assert w.contents("barrel1") == 5.0 and w.loose_qty("charcoal") == 10.0 and w.total("charcoal") == t0, \
        "emptying moves it back out -- still conserved"


# ------------------------------------------------------ G-empty-bounded-by-contents
def test_you_cannot_empty_more_than_is_inside():
    w = _yard(loose=0.0, cap=10.0, start=3.0)          # 3 inside, nothing loose
    w.empty("Tom", "barrel1", 99.0)
    assert w.contents("barrel1") == 0.0 and w.loose_qty("charcoal") == 3.0, "at most what is inside comes out"


# ------------------------------------------------------ G-a-locked-safe-needs-the-key (headline)
def test_a_locked_safe_blocks_access_without_the_key():
    w = Cont(); w.add_agent("Tom"); w.add_agent("Clerk"); w.add_pile("coin", 20.0)
    w.add_container("safe", kind="safe", holds="coin", capacity=100.0, lock_id=7.0, locked=True)
    w.give_key("Clerk", opens=7.0)
    w.fill("Tom", "safe", 20.0)
    assert w.contents("safe") == 0.0 and w.loose_qty("coin") == 20.0, "no key -> the locked safe stays shut"
    w.fill("Clerk", "safe", 20.0)
    assert w.contents("safe") == 20.0, "the keyholder can open it and fill it"


# ------------------------------------------------------ G-a-wrong-key-does-not-work
def test_a_wrong_key_does_not_open_the_safe():
    w = Cont(); w.add_agent("Tom"); w.add_pile("coin", 20.0)
    w.add_container("safe", kind="safe", holds="coin", capacity=100.0, qty=10.0, lock_id=7.0, locked=True)
    w.give_key("Tom", opens=99.0)                       # a key for a different lock
    w.empty("Tom", "safe", 5.0)
    assert w.contents("safe") == 10.0, "a key that opens another lock does not open this safe"


# ------------------------------------------------------ G-the-keyholder-locks-and-unlocks
def test_the_keyholder_can_lock_and_unlock():
    w = Cont(); w.add_agent("Clerk"); w.add_pile("coin", 20.0)
    w.add_container("safe", kind="safe", holds="coin", capacity=100.0, qty=10.0, lock_id=7.0, locked=True)
    w.give_key("Clerk", opens=7.0)
    w.unlock("Clerk", "safe")
    assert not w.is_locked("safe"), "the keyholder unlocks it"
    w.empty("Clerk", "safe", 4.0)
    assert w.contents("safe") == 6.0, "and can then take from it"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_container():
    src = open(os.path.join(_ROOT, "worlds", "bigville_container_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_container.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"ct_fill", "ct_empty"} <= names, names
    fill = json.dumps([r for r in seed["rules"] if r["name"] == "ct_fill"][0])
    assert "capacity" in fill and "contains" in fill and '"at"' in fill, \
        "fill is bounded by capacity, targets the contained pile, and binds by access (co-location)"
