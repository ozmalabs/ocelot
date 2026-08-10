"""bigville R23 (block 310000): the legislature + the council's routine acts.
Gates mirror BIGVILLE_LEGISLATURE_PREREG.md. Every outcome (vote/pass/apply/
censure/tax) is a seed rule; the adapter only mints, arms, ticks, and reads.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_legislature_world import BigvilleLegislatureWorld   # noqa: E402


def _council(w):
    # three poor-bloc, two rich-bloc councillors.
    for n in ("Ada", "Bram", "Cato"):
        w.add_councillor(n, bloc="poor")
    for n in ("Dane", "Esme"):
        w.add_councillor(n, bloc="rich")


def _residents(w, n=4, coin=20.0):
    for i in range(n):
        w.add_resident(f"R{i}", coin=coin)


# ------------------------------------------------------ G-vote-by-bloc (headline)
def test_bill_collects_only_its_bloc_and_passes_at_threshold():
    w = BigvilleLegislatureWorld()
    _council(w)
    w.add_law("land_tax", 2.0)
    # relief aids the poor bloc; threshold 3 -> the three poor councillors carry it.
    bill = w.propose_bill("amend", target="land_tax", new_value=1.0,
                          aids_bloc="poor", threshold=3)
    w.run()
    assert w.bill_status(bill) == "enacted", "poor-bloc bill (3 votes >= 3) should pass+apply"
    assert int(w.eng.node(bill)["attrs"]["votes_for"]) == 3, "only the 3 poor councillors vote"

    # a bill needing 4 with only 3 poor votes stays pending.
    w2 = BigvilleLegislatureWorld()
    _council(w2)
    w2.add_law("land_tax", 2.0)
    b2 = w2.propose_bill("amend", target="land_tax", new_value=1.0,
                         aids_bloc="poor", threshold=4)
    w2.run()
    assert w2.bill_status(b2) == "pending", "below-threshold bill must not pass"


# ------------------------------------------------------ G-amend-changes-the-take (headline)
def test_amend_changes_the_treasury_take():
    w = BigvilleLegislatureWorld()
    _council(w)
    _residents(w, n=4)
    w.add_law("land_tax", 2.0)
    assert abs(w.collect_tax() - 8.0) < 1e-9, "4 residents * 2.0 = 8.0 before amend"
    # rich bloc carries a tax RISE to 5.0 (threshold 2 -> the two rich councillors).
    bill = w.propose_bill("amend", target="land_tax", new_value=5.0,
                          aids_bloc="rich", threshold=2)
    w.run()
    assert w.bill_status(bill) == "enacted"
    assert abs(w.law_value("land_tax") - 5.0) < 1e-9
    assert abs(w.collect_tax() - 20.0) < 1e-9, "4 residents * 5.0 = 20.0 after amend"


# ------------------------------------------------------ G-repeal-stops-the-effect
def test_repeal_stops_the_tax():
    w = BigvilleLegislatureWorld()
    _council(w)
    _residents(w, n=4)
    w.add_law("land_tax", 2.0)
    assert abs(w.collect_tax() - 8.0) < 1e-9
    bill = w.propose_bill("repeal", target="land_tax", aids_bloc="poor", threshold=3)
    w.run()
    assert w.bill_status(bill) == "enacted"
    assert w.law_status("land_tax")[0] == "repealed"
    assert abs(w.collect_tax() - 0.0) < 1e-9, "repealed land_tax takes nothing"


# ------------------------------------------------------ G-enact-adds-a-law
def test_enact_mints_a_new_law_once():
    w = BigvilleLegislatureWorld()
    _council(w)
    bill = w.propose_bill("enact", target="curfew", new_value=22.0,
                          aids_bloc="poor", threshold=3)
    w.run()
    assert w.bill_status(bill) == "enacted"
    st = w.law_status("curfew")
    assert st is not None and st[0] == "active" and abs(st[1] - 22.0) < 1e-9
    # a second enact of the same name mints no duplicate.
    b2 = w.propose_bill("enact", target="curfew", new_value=23.0,
                        aids_bloc="poor", threshold=3)
    w.run()
    curfews = [l for l in w.eng.neighbours(w._book, "has_law")
               if w.eng.node(l)["attrs"].get("name") == "curfew"]
    assert len(curfews) == 1, "enact must not duplicate an existing law name"


# ------------------------------------------------------ G-censure-bites
def test_censure_lowers_standing_decision_does_not():
    w = BigvilleLegislatureWorld()
    _council(w)
    w.add_resident("Mordecai", standing=5.0)
    before = w.standing_of("Mordecai")
    w.issue_act("censure", "for repeated public drunkenness", target="Mordecai")
    w.run()
    assert abs(w.standing_of("Mordecai") - (before - 1.0)) < 1e-9, "censure lowers standing once"
    # re-running does not double-apply (applied guard).
    w.run()
    assert abs(w.standing_of("Mordecai") - (before - 1.0)) < 1e-9, "censure applies exactly once"
    # a plain decision changes no standing.
    w.add_resident("Nell", standing=4.0)
    w.issue_act("decision", "the market shall open at dawn")
    w.run()
    assert abs(w.standing_of("Nell") - 4.0) < 1e-9
    kinds = {k for k, _ in w.posted_acts()}
    assert {"censure", "decision"} <= kinds, "acts are posted to the noticeboard"


# ------------------------------------------------------ G-below-threshold-no-change (falsifier)
def test_below_threshold_leaves_the_book_unchanged():
    w = BigvilleLegislatureWorld()
    _council(w)
    w.add_law("land_tax", 2.0)
    before = w.law_book()
    # rich bill needing 3 but only 2 rich councillors -> fails.
    w.propose_bill("amend", target="land_tax", new_value=9.0,
                   aids_bloc="rich", threshold=3)
    w.run()
    assert w.law_book() == before, "a bill that misses its threshold changes no law"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_legislation():
    src = open(os.path.join(_ROOT, "worlds", "bigville_legislature_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_legislature.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"leg_vote", "leg_tally", "leg_pass", "leg_amend", "leg_repeal",
            "leg_enact", "law_tax_charge", "ca_censure_effect"} <= names, names
