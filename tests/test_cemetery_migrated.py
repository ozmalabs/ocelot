"""bigville R53 (block 364000): the churchyard cemetery, funerals, the pauper's grave. The
cemetery is at the church; the church holds funerals the estate pays for; an estate that
cannot pay gets a pauper's grave; no undertaker -> the body lies unburied. In a small town the
undertaker is also the doctor (a plural office). Gates mirror the seed description.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_cemetery_world import BigvilleCemeteryWorld as Cem   # noqa: E402


# ------------------------------------------------------ G-churchyard-funeral (headline)
def test_the_church_holds_a_funeral_the_estate_pays_for():
    w = Cem(funeral_fee=5.0)
    w.appoint_doctor_undertaker("DrPayne")
    w.add_resident("Squire", estate=50.0)
    w.die("Squire")
    assert w.is_buried("Squire") and not w.in_paupers_grave("Squire"), "a solvent estate gets a proper grave"
    assert w.estate("Squire") == 45.0, "the estate pays the funeral fee"
    assert w.church_coin() == 5.0, "the funeral fee is the church's revenue"
    assert w.grave_count() == 1


# ------------------------------------------------------ G-doctor-is-undertaker (headline; plural office)
def test_in_a_small_town_the_doctor_is_also_the_undertaker():
    w = Cem()
    w.appoint_doctor_undertaker("DrPayne")
    assert w.has_role("DrPayne", "doctor", "undertaker"), \
        "one person holds BOTH roles -- a plural office (one-office-per-person is a big-town assumption)"


# ------------------------------------------------------ G-paupers-grave (headline)
def test_an_estate_that_cannot_pay_gets_a_paupers_grave():
    w = Cem(funeral_fee=5.0)
    w.appoint_doctor_undertaker("DrPayne")
    w.add_resident("Tom", estate=1.0)                       # cannot afford the fee
    w.die("Tom")
    assert w.is_buried("Tom") and w.in_paupers_grave("Tom"), \
        "an insolvent estate gets a pauper's grave -- the poverty gradient reaches the grave"
    assert w.church_coin() == 0.0, "no fee is paid for a pauper burial"
    assert w.estate("Tom") == 1.0, "the estate keeps its meagre coin -- the parish bears the pauper burial"


# ------------------------------------------------------ G-cemetery-at-the-church
def test_the_cemetery_is_the_churchyard():
    w = Cem()
    assert w.eng.has_edge(w._church, "has_cemetery", w._cem), "the cemetery is AT the church (the churchyard)"


# ------------------------------------------------------ G-no-undertaker-unburied
def test_with_no_undertaker_the_dead_lie_unburied():
    w = Cem(funeral_fee=5.0)
    w.appoint_doctor_only("DrAlone")                        # a doctor, but nobody to bury
    w.add_resident("Widow", estate=50.0)
    w.die("Widow")
    assert not w.is_buried("Widow") and w.is_unburied("Widow"), \
        "with no undertaker in office, the body lies unburied -- a hazard, like unmanaged rubbish"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_burial():
    src = open(os.path.join(_ROOT, "worlds", "bigville_cemetery_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_cemetery.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"cy_funeral", "cy_pauper", "cy_unburied_hazard"} <= names, names
    blob = json.dumps(seed)
    assert "has_cemetery" in blob and "funeral_fee" in blob and "pauper" in blob, \
        "churchyard + funeral fee + pauper's grave are the mechanism"
