"""bigville block 294000 -- newspaper-writer Rung B: townspeople GO TO the
publisher to report what they hold.

A resident holding a salient Fact forms -- by RULE -- the intent to report it to
whoever affords makes_known, WALKS there on the real nav flood, and delivers on
arrival. Gates mirror BIGVILLE_REPORT_PREREG.md.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_report_world import BigvilleReportWorld       # noqa: E402

PUB, FAR, FAR2 = (27, 9), (0, 2), (5, 0)


# ------------------------------------------------------ G-report-delivered
def test_reporter_walks_to_the_publisher_and_delivers():
    """A reporter far from the publisher forms the report goal, WALKS to the
    publisher's cell, and delivers -- the publisher received the fact."""
    w = BigvilleReportWorld()
    w.add_publisher("iris", PUB)
    w.add_reporter("alice", FAR, salience=3.0, desc="a foreclosure on Elm Street")
    assert w.pos["alice"] == FAR and not w.delivered("alice")
    w.run(T=80)
    assert w.pos["alice"] == PUB, ("the reporter did not reach the publisher: at %s"
                                   % (w.pos["alice"],))
    assert w.delivered("alice"), "arrived but did not deliver"
    assert ("a foreclosure on Elm Street", 3.0) in w.received_facts()
    w.close()


# ------------------------------------------------------ G-no-afforder
def test_no_afforder_no_report():
    """Ablate the makes_known affordance -> no target -> the reporter forms no
    goal, does not move, and nothing is delivered."""
    w = BigvilleReportWorld()
    w.add_publisher("iris", PUB)
    w.set_publisher_affordance(False)
    w.add_reporter("alice", FAR, salience=3.0, desc="x")
    w.run(T=80)
    assert not w.report_intent("alice"), "no afforder, yet an intent formed"
    assert w.pos["alice"] == FAR, "no afforder, yet the reporter travelled"
    assert not w.delivered("alice")
    w.close()


# ------------------------------------------------------ G-travel-bound
def test_delivery_is_travel_bound():
    """With movement ablated the reporter still forms the intent (it WANTS the
    thing known) but never reaches the publisher -> no delivery."""
    w = BigvilleReportWorld()
    w.add_publisher("iris", PUB)
    w.add_reporter("alice", FAR, salience=3.0, desc="x")
    w.run(T=80, move=False)
    assert w.report_intent("alice"), "the reporter should still WANT to report"
    assert w.pos["alice"] == FAR and not w.delivered("alice"), (
        "delivery must depend on travelling there")
    w.close()


# ------------------------------------------------------ G-two-reporters
def test_two_reporters_both_deliver():
    """Two residents, each holding a salient fact, both walk to the same publisher
    and both deliver -- nothing is special-cased to one reporter."""
    w = BigvilleReportWorld()
    w.add_publisher("iris", PUB)
    w.add_reporter("alice", FAR, salience=2.0, desc="an eviction")
    w.add_reporter("bob", FAR2, salience=2.0, desc="a missing shipment")
    w.run(T=120)
    assert w.delivered("alice") and w.delivered("bob"), (
        "both reporters must deliver: alice=%s bob=%s"
        % (w.delivered("alice"), w.delivered("bob")))
    descs = {d for d, _ in w.received_facts()}
    assert {"an eviction", "a missing shipment"} <= descs, descs
    w.close()


# ------------------------------------------------------ G-no-python-decision
def test_no_python_decides_reporting():
    """Source audit: the adapter runs no rule engine and holds no if/else over
    graph state deciding who reports or when to deliver -- the report goal and the
    delivery come only from the seed rules."""
    src = open(os.path.join(_ROOT, "worlds", "bigville_report_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    import json
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_report.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"rep_form_report_goal", "rep_deliver_on_arrival"} <= names, names
    # the target is chosen by the affordance, not a reporter identity.
    form = next(r for r in seed["rules"] if r["name"] == "rep_form_report_goal")
    assert "makes_known" in json.dumps(form)
