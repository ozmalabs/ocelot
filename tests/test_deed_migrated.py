"""bigville R55 (block 366000): land ownership by deed, register, and bank. Ownership is what
the Clerk's register records; the register is authoritative only if the clerk's office is
recognized; transfers follow the register; the bank forecloses on a defaulted mortgage. The
formal version of the recognition thesis. Gates mirror the seed description.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_deed_world import BigvilleDeedWorld as Deed   # noqa: E402


def _with_recognized_clerk():
    w = Deed(); w.add_clerk("ClerkJones")
    for r in ("A", "B", "C"):
        w.recognize_clerk(r)
    return w


# ------------------------------------------------------ G-land-by-registered-deed (headline)
def test_land_ownership_is_what_the_register_records():
    w = _with_recognized_clerk()
    w.issue_deed("Northfield", owner="Giles")
    assert w.is_registered("Northfield"), "the clerk records the deed in the register"
    assert w.owner_of("Northfield") == "Giles", "ownership is the register's recorded owner"


# ------------------------------------------------------ G-register-authority-rests-on-recognition (headline)
def test_an_unrecognized_clerks_register_has_no_authority():
    w = Deed(); w.add_clerk("Pretender")                    # nobody recognizes him
    w.issue_deed("Southfield", owner="Squatter")
    assert w.clerk_authority() == 0
    assert not w.is_registered("Southfield") and w.owner_of("Southfield") is None, \
        "an unrecognized clerk's register is not authoritative -- the deed is not recorded"


# ------------------------------------------------------ G-transfer-follows-the-register (headline)
def test_a_transfer_updates_the_register():
    w = _with_recognized_clerk()
    w.issue_deed("Northfield", owner="Giles")
    w.transfer("Northfield", to="WidowBrown")
    assert w.owner_of("Northfield") == "WidowBrown", "selling/bequeathing land -> the clerk records the new owner"


# ------------------------------------------------------ G-no-deed-no-ownership
def test_without_a_registered_deed_there_is_no_ownership():
    w = _with_recognized_clerk()
    # a plot nobody has a registered deed for
    w.issue_deed("Waste", owner="Nobody")
    w.eng.set_attr(w._deeds["Waste"], "registered", 0.0)     # pretend it was never recorded
    assert w.owner_of("Waste") is None, "a claim without a registered deed owns nothing -- the register decides"


# ------------------------------------------------------ G-bank-forecloses
def test_the_bank_forecloses_on_a_defaulted_mortgage():
    w = _with_recognized_clerk()
    w.add_bank("BigvilleBank")
    w.issue_deed("Millplot", owner="Miller")
    w.pledge_to_bank("Millplot", "BigvilleBank")             # mortgaged, deed in the bank's safe
    assert w.owner_of("Millplot") == "Miller"
    w.default("Millplot")
    assert w.owner_of("Millplot") == "BigvilleBank", "on default the bank forecloses -- the clerk records the bank"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_land():
    src = open(os.path.join(_ROOT, "worlds", "bigville_deed_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_deed.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"ld_clerk_authority", "ld_record", "ld_transfer", "ld_foreclose"} <= names, names
    rec = json.dumps([r for r in seed["rules"] if r["name"] == "ld_record"][0])
    assert "has_deed" in rec and "authority" in rec, "recording a deed requires a recognized clerk"
