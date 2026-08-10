"""bigville R54 (block 367000): pious bequests -- a testator DECIDES whether to leave some money
to the church, a COLLAPSE valued by their OWN piety (from their graph), not a threshold. The
pious give (even the poor); the worldly keep. Composes the will (executor still decides to
honour) + cemetery (funeral first). Gates mirror the seed description.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_will_world import BigvilleWillWorld as Will   # noqa: E402


def _willed(name, *, piety, greed, estate, heir_bequest=20.0, funeral_fee=5.0):
    w = Will(funeral_fee=funeral_fee); w.appoint_doctor_undertaker("Doc")
    w.add_resident(name, estate=estate, piety=piety, greed=greed)
    w.add_resident("Heir", coin=0.0); w.add_resident("Vicar", coin=0.0)   # Vicar defaults honest
    w.write_note(name, "my will")
    if heir_bequest:
        w.bequeath(name, "Heir", heir_bequest)
    w.attest_as_will("Vicar", name, executor="Vicar")
    w.die(name)
    return w


# ------------------------------------------------------ G-pious-decides-to-give (headline)
def test_a_pious_testator_decides_to_leave_money_to_the_church():
    w = _willed("Squire", piety=0.9, greed=0.1, estate=100.0)
    assert w.pious_choice("Squire") == "bequeath", "the pious agent DECIDES to give (a collapse on its own piety)"
    assert w.church_coin() == 14.0, "the church gets the funeral fee (5) + the pious legacy (piety*10 = 9)"


# ------------------------------------------------------ G-worldly-decides-to-keep (headline; divergence)
def test_a_worldly_testator_decides_to_keep_it_all():
    w = _willed("Miser", piety=0.1, greed=0.9, estate=100.0)
    assert w.pious_choice("Miser") == "keep", "the worldly agent DECIDES not to give -- agents diverge on their piety"
    assert w.church_coin() == 5.0, "the church gets only the funeral fee -- no pious legacy"


# ------------------------------------------------------ G-even-the-poor-give (headline)
def test_even_a_poor_pious_person_leaves_some_to_the_church():
    # a poor pious widow whose will is a church legacy only (no family bequest)
    w = _willed("Widow", piety=0.9, greed=0.1, estate=7.0, heir_bequest=0.0)
    assert w.pious_choice("Widow") == "bequeath", "she decides to give despite being poor -- piety, not wealth"
    # funeral fee 5 leaves 2; the pious legacy (9) abates to her remaining 2 -> the church gets it
    assert w.church_coin() == 7.0 and w.estate("Widow") == 0.0, \
        "even the poor leave what little they can to the church (funeral 5 + her last 2)"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_the_pious_bequest_is_a_collapse_not_a_threshold():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_will.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"pl_pious_decide", "pl_pious_grant"} <= names, names
    dec = json.dumps([r for r in seed["rules"] if r["name"] == "pl_pious_decide"][0])
    assert "PietyStance" in dec and "Argmax" in dec, "the pious bequest is an Argmax collapse over the agent's stances"
    assert "piety" in dec, "valued by the agent's OWN piety (read from its graph), not a threshold constant"
