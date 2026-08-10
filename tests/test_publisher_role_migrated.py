"""bigville block 293000 -- newspaper-writer Rung A: the PORTABLE publisher role.

The "gather information and write" role is a GENERAL, held, portable thing: a
resident who `affords` a makes_known Affordance is the town's writer, decided by
a RULE (the Paper employs whoever affords it) -- not a Python role-pick. Move the
affordance and the role moves. Gates mirror BIGVILLE_PUBLISHER_ROLE_PREREG.md.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_publisher_world import BigvillePublisherWorld   # noqa: E402


def _town(*names):
    w = BigvillePublisherWorld()
    for nm in names:
        w.add_resident(nm)
    return w


# --------------------------------------------------------- G-role-derives
def test_role_derives_from_the_held_affordance():
    """Give a resident the makes_known affordance -> the Paper employs it (by rule)
    and it acquires the general gather goal Goal{kind:know}. No Python picked it."""
    w = _town("alice", "bob", "carol")
    w.set_publisher("alice")
    w.run()
    assert w.publisher() == ["alice"], w.publisher()
    assert w.holds_gather_goal("alice"), "the publisher must hold the gather goal"
    assert not w.holds_gather_goal("bob"), "a non-publisher holds no gather goal"
    w.close()


# --------------------------------------------------------- G-portable (HEADLINE)
def test_the_role_follows_the_affordance():
    """Move the makes_known affordance from alice to bob -> the Paper now employs
    BOB and NOT alice, and bob acquires the gather goal. Swapping the holder swaps
    the writer with ZERO code change -- the proof the role is general, not bespoke."""
    w = _town("alice", "bob", "carol")
    w.set_publisher("alice"); w.run()
    assert w.publisher() == ["alice"]

    w.set_publisher("bob"); w.run()
    assert w.publisher() == ["bob"], (
        "the publish role did NOT follow the affordance: %s" % w.publisher())
    assert w.holds_gather_goal("bob"), "the new publisher must hold the gather goal"
    w.close()


# --------------------------------------------------------- ablate
def test_ablating_the_affordance_empties_the_role():
    """Remove the makes_known affordance from the town entirely -> the Paper employs
    no one (the employs edge FOLLOWS the affordance, it does not accrete)."""
    w = _town("alice", "bob")
    w.set_publisher("alice"); w.run()
    assert w.publisher() == ["alice"]
    w.set_publisher(None); w.run()
    assert w.publisher() == [], w.publisher()
    w.close()


# --------------------------------------------------------- G-two-afforders
def test_role_is_not_singular_by_construction():
    """Two residents affording makes_known -> the Paper employs BOTH; nothing
    hardcodes a single reporter. Remove one -> the other remains (which resident
    is the LEAD among several is a later rung's concern)."""
    w = _town("alice", "bob", "carol")
    w.set_publisher("alice"); w.add_publisher("carol"); w.run()
    assert w.publisher() == ["alice", "carol"], w.publisher()
    # take carol's affordance away (hand it solely to alice) -> only alice remains
    w.set_publisher("alice"); w.run()
    assert w.publisher() == ["alice"], w.publisher()
    w.close()


# --------------------------------------------------------- G-no-python-pick
def test_no_python_selects_the_publisher():
    """Source audit: the world adapter holds NO role-string / name test that
    decides who the writer is (the defect this rung removes was
    `if self.roles2.get(nm) == 'fishmonger'`). The `employs` edge is produced only
    by the seed rule reading the affordance."""
    src = open(os.path.join(_ROOT, "worlds", "bigville_publisher_world.py")).read()
    # no role/name equality test selecting a publisher, no rule-engine calls.
    assert 'roles' not in src, "adapter must not read a role table to pick the writer"
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    # the decision lives in the seed rule, not Python.
    import json
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_publisher_role.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"pub_employ_afforder", "pub_unemploy_non_afforder", "pub_role_gathers"} <= names, names
    # the employ rule keys on the affordance, not a role name.
    employ = next(r for r in seed["rules"] if r["name"] == "pub_employ_afforder")
    assert "makes_known" in json.dumps(employ), "the writer must be derived from the affordance"
