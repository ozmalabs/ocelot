"""bigville R54 (block 365000): a will is a NOTE, and PEOPLE make it a will. A note with bequests
is inert writing until a person attests it as the deceased's will and names an executor; even
then the estate is not auto-distributed -- the executor DECIDES whether to honour it. Composes
the cemetery (funeral first). Gates mirror the seed description.
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


# ------------------------------------------------------ G-just-writing-until-people-make-it-a-will (headline)
def test_a_note_is_just_writing_until_people_make_it_a_will():
    w = Will(funeral_fee=5.0); w.appoint_doctor_undertaker("Doc")
    w.add_resident("Squire", estate=100.0)
    for n in ("Son", "Cook", "Nephew"):
        w.add_resident(n, coin=0.0)
    w.set_next_of_kin("Squire", "Nephew")
    w.write_note("Squire", "I leave 30 to my son and 10 to the cook")
    w.bequeath("Squire", "Son", 30.0); w.bequeath("Squire", "Cook", 10.0)
    w.die("Squire")                                            # NOBODY attested the note as a will
    assert w.coin("Son") == 0.0 and w.coin("Cook") == 0.0, \
        "the bequests are ignored -- a note is just writing until people make it a will"
    assert w.coin("Nephew") == 95.0, "so the estate passes INTESTATE to the next of kin (after the funeral fee)"


# ------------------------------------------------------ G-people-make-it-a-will (headline)
def test_a_person_attests_the_note_as_the_will_and_it_is_enacted():
    w = Will(funeral_fee=5.0); w.appoint_doctor_undertaker("Doc")
    w.add_resident("Squire", estate=100.0)
    for n in ("Son", "Cook", "Vicar"):
        w.add_resident(n, coin=0.0)                            # Vicar defaults honest
    w.write_note("Squire", "I leave 30 to my son and 10 to the cook")
    w.bequeath("Squire", "Son", 30.0); w.bequeath("Squire", "Cook", 10.0)
    w.attest_as_will("Vicar", "Squire", executor="Vicar")     # a PERSON makes it a will
    w.die("Squire")
    assert w.executor_choice("Vicar") == "honour", "an honest executor decides to honour the wishes"
    assert w.coin("Son") == 30.0 and w.coin("Cook") == 10.0, "the bequests are paid from the estate"
    assert w.estate("Squire") == 55.0, "funeral fee first, then legacies (100 - 5 - 30 - 10)"


# ------------------------------------------------------ G-executor-decides-withhold (headline)
def test_even_attested_the_executor_decides_and_may_withhold():
    w = Will(funeral_fee=5.0); w.appoint_doctor_undertaker("Doc")
    w.add_resident("Squire", estate=100.0)
    w.add_resident("Son", coin=0.0)
    w.add_resident("Rogue", coin=0.0, honesty=0.2, greed=0.9)  # a grasping executor
    w.write_note("Squire", "all to my son"); w.bequeath("Squire", "Son", 50.0)
    w.attest_as_will("Rogue", "Squire", executor="Rogue")
    w.die("Squire")
    assert w.executor_choice("Rogue") == "withhold", "the executor DECIDES -- the estate is not auto-distributed"
    assert w.coin("Son") == 0.0 and w.coin("Rogue") == 95.0, \
        "a grasping executor keeps the estate for himself -- a betrayal (contestable via the court)"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_will():
    src = open(os.path.join(_ROOT, "worlds", "bigville_will_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_will.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"wl_decide", "wl_honour", "wl_withhold", "wl_intestate"} <= names, names
    dec = json.dumps([r for r in seed["rules"] if r["name"] == "wl_decide"][0])
    assert "HonorStance" in dec and "Argmax" in dec, "honouring the will is the executor's decision (a collapse)"
    # a will is a Note made testamentary by people (willed_by / executor edges), not a special type
    assert '["note", "willed_by", "dead"]' in dec.replace(" ", "") or ["note", "willed_by", "dead"] in \
        [r for r in seed["rules"] if r["name"] == "wl_decide"][0]["match"], "the rules operate on a Note"
