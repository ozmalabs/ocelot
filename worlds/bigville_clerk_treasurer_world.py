"""BigvilleClerkTreasurerWorld -- bigville R46 (block 345000): the CLERK-TREASURER.

A paid council office whose job is to KEEP RECORDS and COLLECT TAXES. Money is not magic:
the treasury only gains coin because someone collects it, every move is written into a
ledger (someone has to do the books), and the record must RECONCILE against the actual coin
-- so an unrecorded transaction or embezzlement surfaces as a discrepancy.

A WORLD ADAPTER. No collect/pay/reconcile DECISION in Python -- ct_* are seed rules. The
adapter mints the treasury/ledger/clerk/residents, arms collection/pay/reconcile, and reads.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402


class BigvilleClerkTreasurerWorld:
    def __init__(self, *, treasury_coin=0.0):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_clerk_treasurer"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._treasury = self.eng.add_node("Treasury", {"coin": float(treasury_coin), "discrepancy": 0.0,
                                                        "reconciled": 0.0, "reconcile_armed": 0.0,
                                                        "pay_armed": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_treasury", self._treasury)
        self._ledger = self.eng.add_node("Ledger", {"recorded": 0.0})
        self.eng.add_edge_unchecked(self._treasury, "has_ledger", self._ledger)
        self._clerk = None
        self._residents = {}

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def appoint_clerk(self, name, *, salary=3.0, honesty=1.0, coin=0.0):
        """Appoint the paid Clerk-Treasurer. honesty<1 => the clerk skims (embezzles)."""
        c = self.eng.add_node("Agent", {"name": name, "role": "clerk_treasurer",
                                        "salary": float(salary), "honesty": float(honesty),
                                        "coin": float(coin)})
        self.eng.add_edge_unchecked(self._town, "has_clerk", c)
        self._clerk = c
        return c

    def add_resident(self, name, *, tax_due=0.0, coin=20.0):
        r = self.eng.add_node("Agent", {"name": name, "tax_due": float(tax_due), "coin": float(coin),
                                        "tax_collected": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", r)
        self._residents[name] = r
        return r

    def collect_taxes(self):
        """The clerk collects the assessed taxes (if there is a clerk in office)."""
        self._run()

    def pay_clerk(self):
        self.eng.set_attr(self._treasury, "pay_armed", 1.0)
        self._run()

    def unrecorded_income(self, amount):
        """Coin enters the treasury WITHOUT the clerk recording it (a forgotten/hidden
        transaction) -- the reconciliation should catch the gap."""
        self.eng.set_attr(self._treasury, "coin",
                          float(self.eng.node(self._treasury)["attrs"]["coin"]) + float(amount))

    def reconcile(self):
        self.eng.set_attr(self._treasury, "reconcile_armed", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def _t(self, k): return round(float(self.eng.node(self._treasury)["attrs"].get(k, 0.0)), 4)
    def treasury_coin(self): return self._t("coin")
    def recorded_balance(self): return round(float(self.eng.node(self._ledger)["attrs"]["recorded"]), 4)
    def discrepancy(self): return self._t("discrepancy")
    def is_reconciled(self): return self._t("reconciled") == 1.0
    def clerk_coin(self):
        return round(float(self.eng.node(self._clerk)["attrs"].get("coin", 0.0)), 4)
    def ledger_entries(self):
        return [self.eng.node(e)["attrs"] for e in self.eng.neighbours(self._ledger, "has_entry")]
    def entry_count(self): return len(self.eng.neighbours(self._ledger, "has_entry"))
