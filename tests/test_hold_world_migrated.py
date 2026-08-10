"""bigville block 295000 -- newspaper-writer Rung C: the publisher HOLDS what he is
told or witnessed as a general belief, testimony-bound.

Gates mirror BIGVILLE_HOLD_PREREG.md. The hard gates are anti-confabulation (a
fact he was not given and did not see is NOT known) and held == told U witnessed.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_hold_world import BigvilleHoldWorld           # noqa: E402

PUB, FAR = (27, 9), (0, 2)


def _delivered_world():
    w = BigvilleHoldWorld()
    w.add_publisher("iris", PUB)
    w.add_reporter("alice", FAR, salience=3.0, desc="a foreclosure on Elm Street")
    w.add_witnessed_fact("a fire at the mill", salience=2.0)
    w.add_rumor("aliens landed", salience=5.0)
    w.run(T=80)
    return w


# --------------------------------------------------------- G-holds-told
def test_holds_what_he_was_told():
    w = _delivered_world()
    assert w.knows("a foreclosure on Elm Street"), "a delivered fact must be held"
    assert ("a foreclosure on Elm Street", "testimony") in w.known_facts()
    w.close()


# --------------------------------------------------------- G-holds-witnessed
def test_holds_what_he_witnessed():
    w = _delivered_world()
    assert w.knows("a fire at the mill"), "a witnessed fact must be held"
    assert ("a fire at the mill", "witness") in w.known_facts()
    w.close()


# --------------------------------------------------------- G-anti-confabulation
def test_does_not_hold_what_he_was_not_given():
    """HARD: a fact neither delivered nor witnessed (a rumour that merely EXISTS)
    is NOT held. The publisher does not confabulate."""
    w = _delivered_world()
    assert not w.knows("aliens landed"), "confabulation: held a fact never given"
    descs = {d for d, _ in w.known_facts()}
    assert "aliens landed" not in descs
    w.close()


# --------------------------------------------------------- G-held-equals-source
def test_held_set_equals_told_union_witnessed():
    """HARD: the held `knows` set is EXACTLY (received) U (witnessed) -- faithful
    to its sources, nothing extra, nothing missing."""
    w = _delivered_world()
    assert w.held_equals_told_union_witnessed(), (
        "held beliefs diverge from (told U witnessed): %s" % (w.known_facts(),))
    # and it is non-trivial: he DOES hold the two real ones.
    assert len(w.known_facts()) == 2, w.known_facts()
    w.close()


# --------------------------------------------------------- G-no-python-decision
def test_no_python_decides_belief():
    src = open(os.path.join(_ROOT, "worlds", "bigville_hold_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    import json
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_hold.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"hold_told", "hold_witnessed"} <= names, names
    # belief is minted only from received / witnessed_fact (structural bound).
    blob = json.dumps(seed)
    assert "received" in blob and "witnessed_fact" in blob and "knows" in blob
