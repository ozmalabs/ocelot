"""bigville R46 (block 345000): the CLERK-TREASURER -- a paid council office that keeps
records and collects taxes; money is not magic (someone must collect it), records are
written (someone must do the books), and the record must RECONCILE against the actual coin
(so an unrecorded transaction or embezzlement surfaces). Gates mirror the seed description.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_clerk_treasurer_world import BigvilleClerkTreasurerWorld as Clerk   # noqa: E402


# ------------------------------------------------------ G-money-not-magic (headline)
def test_the_treasury_does_not_magically_get_money():
    w = Clerk()
    w.add_resident("A", tax_due=5.0); w.add_resident("B", tax_due=5.0)
    w.collect_taxes()                            # no clerk in office
    assert w.treasury_coin() == 0.0 and w.entry_count() == 0, \
        "with no clerk to collect, the treasury stays flat -- money is not magic"


# ------------------------------------------------------ G-clerk-collects-and-records
def test_the_clerk_collects_taxes_and_writes_the_record():
    w = Clerk(); w.appoint_clerk("Honest", honesty=1.0)
    for who in ("A", "B", "D"):
        w.add_resident(who, tax_due=5.0)
    w.collect_taxes()
    assert w.treasury_coin() == 15.0, "the clerk collects the assessed taxes into the treasury"
    assert w.entry_count() == 3, "someone has to do the books -- one ledger entry per collection"
    assert w.recorded_balance() == 15.0, "the written record matches what was collected"


# ------------------------------------------------------ G-books-reconcile
def test_an_honest_clerks_books_reconcile():
    w = Clerk(); w.appoint_clerk("Honest", honesty=1.0)
    w.add_resident("A", tax_due=5.0); w.collect_taxes()
    w.reconcile()
    assert w.discrepancy() == 0.0 and w.is_reconciled(), \
        "every move is recorded, so an honest clerk reconciles the record to the actual coin"


# ------------------------------------------------------ G-clerk-is-paid
def test_the_clerk_is_a_paid_position_and_the_salary_is_recorded():
    w = Clerk(); w.appoint_clerk("Honest", salary=3.0, honesty=1.0)
    w.add_resident("A", tax_due=5.0); w.collect_taxes()
    w.pay_clerk()
    assert w.clerk_coin() == 3.0 and w.treasury_coin() == 2.0, "the salary is drawn from the treasury"
    w.reconcile()
    assert w.discrepancy() == 0.0 and w.is_reconciled(), "a recorded expense keeps the books balanced"


# ------------------------------------------------------ G-embezzlement-surfaces (headline)
def test_reconciliation_catches_embezzlement():
    w = Clerk(); w.appoint_clerk("Crook", honesty=0.7)      # records the full tax, banks 70%
    for who in ("A", "B", "D"):
        w.add_resident(who, tax_due=5.0)
    w.collect_taxes(); w.reconcile()
    assert w.recorded_balance() == 15.0 and w.treasury_coin() == 10.5, \
        "the clerk records the full 15 but only 10.5 reaches the treasury"
    assert w.clerk_coin() == 4.5, "the clerk pocketed the difference"
    assert w.discrepancy() == -4.5 and not w.is_reconciled(), \
        "the books do not balance themselves -- reconciliation surfaces the missing coin"


# ------------------------------------------------------ G-unrecorded-income-surfaces
def test_reconciliation_catches_an_unrecorded_transaction():
    w = Clerk(); w.appoint_clerk("Honest", honesty=1.0)
    w.add_resident("A", tax_due=5.0); w.collect_taxes()
    w.unrecorded_income(4.0)                      # coin enters without a record
    w.reconcile()
    assert w.discrepancy() == 4.0 and not w.is_reconciled(), \
        "coin the records do not account for surfaces as a positive discrepancy"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_does_the_books():
    src = open(os.path.join(_ROOT, "worlds", "bigville_clerk_treasurer_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_clerk_treasurer.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"ct_collect", "ct_pay_clerk", "ct_reconcile"} <= names, names
    recon = json.dumps([r for r in seed["rules"] if r["name"] == "ct_reconcile"][0])
    assert "discrepancy" in recon and "recorded" in recon, \
        "reconciliation compares the written record against the actual coin"
