"""bigville R70 (block 387000): a pile is just a pile -- a world-fact (located matter, conserved),
with NO intrinsic owner. Ownership is a human frame people ADD and others RECOGNIZE. Physical acts
work by ACCESS, not ownership. Gates mirror cp_burn / cp_consume / cp_owner.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_commodity_physical_world import BigvilleCommodityPhysicalWorld as Phys   # noqa: E402


def _yard(wood=20.0):
    w = Phys()
    for who in ("Colly", "Tom", "Nan"):
        w.add_agent(who)
    w.add_pile("wood", wood); w.add_pile("charcoal", 0.0); w.add_pile("smoke", 0.0)
    return w


# ------------------------------------------------------ G-a-pile-is-just-a-pile (headline)
def test_a_pile_is_just_a_pile_not_owned():
    w = _yard()
    assert w.owner_of("wood") is None, "a fresh pile has no owner -- it is just a pile"
    assert not w.has_owner_attr("wood"), "the pile stores no owner -- ownership is not a property of the pile"


# ------------------------------------------------------ G-people-add-ownership (headline)
def test_people_add_ownership_and_it_must_be_recognized():
    w = _yard()
    w.claim("Colly", "wood")
    assert w.owner_of("wood") is None, "a claim nobody recognizes is not ownership"
    w.recognize("Tom", "Colly", "wood")
    assert w.owner_of("wood") == "Colly" and w.claim_recognized("Colly", "wood"), \
        "ownership is a RECOGNIZED claim -- added by people, not intrinsic to the pile"


# ------------------------------------------------------ G-substrate-does-not-forbid-rival-claims (headline)
def test_rival_claims_coexist_and_recognition_decides():
    w = _yard()
    w.claim("Colly", "wood"); w.recognize("Tom", "Colly", "wood"); w.recognize("Nan", "Colly", "wood")
    w.claim("Nan", "wood"); w.recognize("Colly", "Nan", "wood")     # a rival claim -- allowed
    assert w.owner_of("wood") == "Colly", "recognition decides the owner (Colly 2 vs Nan 1); the substrate forbade neither claim"


# ------------------------------------------------------ G-acts-by-access-not-ownership (headline)
def test_a_physical_act_works_by_access_not_ownership():
    w = _yard(20.0)
    m0 = w.total_mass()
    w.claim("Colly", "wood"); w.recognize("Tom", "Colly", "wood")   # Colly owns the wood
    w.burn("Nan", 8.0)                                              # Nan, not the owner, is AT the wood
    assert w.qty("charcoal") == 2.0 and w.qty("smoke") == 6.0, "she can burn it -- the act needs reach, not a deed"
    assert w.total_mass() == m0, "and mass is still conserved (8 wood -> 2 charcoal + 6 smoke)"


# ------------------------------------------------------ G-mass-conserved / cannot-conjure
def test_conservation_still_holds():
    w = _yard(0.0)
    m0 = w.total_mass()
    w.burn("Colly", 8.0)
    assert w.qty("charcoal") == 0.0 and w.total_mass() == m0, "no wood -> no charcoal; nothing conjured"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_and_ownership_is_recognized():
    src = open(os.path.join(_ROOT, "worlds", "bigville_commodity_physical_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_commodity_physical.json")))
    burn = json.dumps([r for r in seed["rules"] if r["name"] == "cp_burn"][0])
    assert '"owns"' not in burn and '"at"' in burn, "the act binds by co-location (access), not ownership"
    owner = json.dumps([r for r in seed["rules"] if r["name"] == "cp_owner"][0])
    assert "recognizes" in owner and "recognized" in owner, "ownership is conferred by recognition, not stored on the pile"
