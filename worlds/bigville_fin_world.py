"""BigvilleFinWorld -- bigville R7 (block 255000): graph-native FINANCE on top of
the proven R4 economy / R5 loop / R6 skill world. The DEEPER economy: housing held
under three TENURES, a BANK run by the banker AGENT Scrooge McBankFace (funds
SEPARATE from his personal coin), interest as the cross-frame MULTIPLICATIVE base,
and rent/mortgage payments whose default cascades to foreclosure/eviction ->
HOMELESSNESS.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 2 FINANCE + sec 3 R7)
------------------------------------------------------------------------------
  * TENURE          -- own outright (tenure=0, holds equity), MORTGAGE (tenure=1,
                       owes the bank principal+interest, builds equity slowly), or
                       RENT (tenure=2, pays a landlord, builds NO equity).
  * THE BANK        -- a `Bank` node with its OWN reserves, RUN BY Scrooge (a full
                       Mover), `run_by` edge. It issues mortgages (`issued` edge),
                       sets its rate (Scrooge's decision_value: fair_rate_bp +
                       greed_premium_bp), and pays Scrooge a SALARY (bank->Scrooge,
                       funds separate: his personal coin tracks the salary).
  * INTEREST        -- `bf_accrue`: balance' = round(balance*(1+r)) at integer
                       periods, r = rate_bp/10000 applied INTENSIONALLY via IDiv --
                       the balance stays INTEGER coin (frame/continuum invariant).
  * DEFAULT CASCADE -- `bf_mortgage_pay`/`_miss` (disjoint on coin>=payment),
                       `bf_foreclose` (missed>=term -> the LAND transfers to the
                       bank + homeless), the rent twins, `bf_homeless_affect` (the
                       204000/239000 distress channel).
  * EQUITY / RENTIER-- `bf_owner_equity`/`bf_mortgagor_equity` (a renter matches
                       NEITHER -> flat), `bf_appreciate`, `bf_rent_raise` (the
                       slumlord lever moving a tenant's affect + backing).

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R6 (BigvilleSkillWorld) by IMPORT, edits no tracked
file, and holds NO agent decision. It ONLY does mechanical I/O: register
Bank/House/Mortgage/Rental graph data (ingest); ARM a one-shot flag for the phase
being advanced (accrue / set-rate / charge / salary / appreciate / equity / raise);
run the Rust `run_rules` fixpoint; read state back. EVERY finance decision -- accrue,
set rate, pay-vs-miss, foreclose, evict, draw salary, go insolvent, raise rent -- is
a seed RULE (bigville_fin_bank / bigville_fin_tenure), never Python. The interest
math is a per-period arithmetic rule composing the pre-existing IDiv/Times/Plus
Terms: NO new Rust.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                       # noqa: E402
from worlds.bigville_skill_world import BigvilleSkillWorld           # noqa: E402

# tenure codes
OWN, MORTGAGE, RENT = 0.0, 1.0, 2.0

# finance attrs set on every character so a rule never reads a missing key. The
# population variation (tenure, decision values) is set by the caller -- these are
# ingest, not a decision (the R4 ECON_DEFAULTS / R6 SKILL_DEFAULTS pattern).
FIN_DEFAULTS = dict(
    tenure=0.0, homeless=0.0, homeless_affect_done=0.0, equity=0.0,
    social_concern=0.0, backing_landlord=0.0,
    pay_armed=0.0, rent_armed=0.0, equity_armed=0.0,
    fair_rate_bp=0.0, greed_premium_bp=0.0,
)


class BigvilleFinWorld(BigvilleSkillWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_fin_bank", "bigville_fin_tenure"):
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._houses = {}       # name -> House nid
        self._mortgages = {}    # char name -> Mortgage nid
        self._rentals = {}      # tenant name -> Rental nid
        self._bank = None       # Bank nid
        self._scrooge = None    # banker char name

    # ---------------------------------------------------------------- ingest
    def make_char(self, name, start, **kw):
        """A townsperson who can hold housing/finance. R4 make_trader (coin) +
        the finance attrs. Mechanical graph data."""
        m = self.make_trader(name, start)
        for k, v in FIN_DEFAULTS.items():
            self.eng.set_attr(m, k, float(v))
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))
        return m

    def set_char(self, name, **kw):
        m = self._movers[name]
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))

    def add_bank(self, scrooge, start, *, reserves, salary,
                 fair_rate_bp, greed_premium_bp=0.0):
        """The BANK (a `Bank` node with its OWN reserves) RUN BY the banker AGENT
        Scrooge McBankFace (a full Mover with his OWN personal coin). The rate is
        Scrooge's decision (fair_rate_bp + greed_premium_bp); the salary is a
        bank->Scrooge transfer. Funds SEPARATE. Mechanical graph data."""
        self._scrooge = scrooge
        self.make_char(scrooge, start, coin=0.0,
                       fair_rate_bp=fair_rate_bp, greed_premium_bp=greed_premium_bp)
        b = self.eng.add_node("Bank", {
            "reserves": float(reserves), "salary": float(salary),
            "rate_bp": float(fair_rate_bp) + float(greed_premium_bp),
            "insolvent": 0.0, "salary_armed": 0.0, "rate_armed": 0.0})
        self.eng.add_edge_unchecked(b, "run_by", self._movers[scrooge])
        self._bank = b
        return b

    def set_scrooge(self, **kw):
        """Set Scrooge's decision values (fair_rate_bp / greed_premium_bp) and the
        bank's salary. WHICH values he picks is HIS -- opaque attrs the adapter sets
        via **kw; the RATE decision itself is bf_set_rate."""
        for k, v in kw.items():
            if k == "salary":
                self.eng.set_attr(self._bank, "salary", float(v))
            else:
                self.eng.set_attr(self._movers[self._scrooge], k, float(v))

    def add_house(self, name, value, apprec=0.0):
        h = self.eng.add_node("House", {"value": float(value), "apprec": float(apprec),
                                        "appreciate_armed": 0.0})
        self._houses[name] = h
        return h

    def own(self, char, house):
        """OWN outright: tenure=0 + owns_house edge. Holds equity = house.value."""
        self.eng.set_attr(self._movers[char], "tenure", OWN)
        self.eng.add_edge_unchecked(self._movers[char], "owns_house", self._houses[house])

    def mortgage(self, char, house, *, principal, payment, term, deduct_reserves=True):
        """Issue a MORTGAGE: tenure=1, the debtor owns the house (secured on the
        LAND+building), the bank funds the loan (reserves -= principal). Balance
        accrues interest each period; missing `term` payments -> foreclosure."""
        self.eng.set_attr(self._movers[char], "tenure", MORTGAGE)
        self.eng.add_edge_unchecked(self._movers[char], "owns_house", self._houses[house])
        rate = float(self.eng.node(self._bank)["attrs"].get("rate_bp", 0.0))
        mort = self.eng.add_node("Mortgage", {
            "balance": float(principal), "rate_bp": rate,
            "payment": float(payment), "term": float(term),
            "missed": 0.0, "foreclosed": 0.0, "period": 0.0, "accrue_armed": 0.0})
        self.eng.add_edge_unchecked(self._movers[char], "has_mortgage", mort)
        self.eng.add_edge_unchecked(mort, "secured_on", self._houses[house])
        self.eng.add_edge_unchecked(self._bank, "issued", mort)
        if deduct_reserves:
            r = float(self.eng.node(self._bank)["attrs"].get("reserves", 0.0))
            self.eng.set_attr(self._bank, "reserves", r - float(principal))
        self._mortgages[char] = mort
        return mort

    def rent(self, tenant, landlord, house, *, rent, term, raise_amount=0.0):
        """A TENANCY: the LANDLORD owns the house (tenure=0, accrues equity), the
        TENANT rents it (tenure=2, builds NO equity). Missing `term` rents -> eviction."""
        self.own(landlord, house)                       # landlord holds the asset
        self.eng.set_attr(self._movers[tenant], "tenure", RENT)
        rental = self.eng.add_node("Rental", {
            "rent": float(rent), "term": float(term), "raise_amount": float(raise_amount),
            "missed": 0.0, "evicted": 0.0, "threatened": 0.0, "raise_armed": 0.0})
        self.eng.add_edge_unchecked(self._movers[tenant], "rents", rental)
        self.eng.add_edge_unchecked(rental, "landlord", self._movers[landlord])
        self.eng.add_edge_unchecked(rental, "rented_house", self._houses[house])
        self._rentals[tenant] = rental
        return rental

    # ------------------------------------------------- rule-driven one-shots
    def _all_mortgages(self):
        return list(self.eng.nodes("Mortgage"))

    def accrue(self):
        """Arm one interest period on every mortgage; bf_accrue applies the
        multiplicative step. The invariant headline."""
        for mort in self._all_mortgages():
            self.eng.set_attr(mort, "accrue_armed", 1.0)
        return self._run()

    def set_rate(self):
        """Scrooge SETS the rate (bf_set_rate reads his decision values and
        propagates to the bank + every issued mortgage)."""
        self.eng.set_attr(self._bank, "rate_armed", 1.0)
        return self._run()

    def charge_mortgages(self):
        """Arm one payment on every mortgagor; bf_mortgage_pay / _miss decides, and
        (in the same fixpoint) bf_foreclose + bf_homeless_affect cascade if a term
        has been breached."""
        for name, mort in self._mortgages.items():
            self.eng.set_attr(self._movers[name], "pay_armed", 1.0)
        return self._run()

    def charge_rents(self):
        """Arm one rent on every tenant; bf_rent_pay / _miss / bf_evict cascade."""
        for name in self._rentals:
            self.eng.set_attr(self._movers[name], "rent_armed", 1.0)
        return self._run()

    def appreciate(self):
        """Arm appreciation on every house (bf_appreciate raises its value)."""
        for h in self._houses.values():
            self.eng.set_attr(h, "appreciate_armed", 1.0)
        return self._run()

    def recompute_equity(self):
        """Arm equity recompute on every character; bf_owner_equity / _mortgagor_equity
        recompute it (a renter matches NEITHER -> stays flat)."""
        for m in self._movers.values():
            self.eng.set_attr(m, "equity_armed", 1.0)
        return self._run()

    def pay_salary(self):
        """Arm one bank->Scrooge salary transfer (bf_salary; funds separate)."""
        self.eng.set_attr(self._bank, "salary_armed", 1.0)
        return self._run()

    def raise_rent(self, tenant):
        """The rentier lever: arm a rent raise + eviction threat on a tenancy
        (bf_rent_raise moves the tenant's affect + backing)."""
        self.eng.set_attr(self._rentals[tenant], "raise_armed", 1.0)
        return self._run()

    def period(self, *, salary=True):
        """One financial period (mechanical composition of the one-shots): charge
        mortgages + rents (interest is serviced/capitalised INSIDE bf_mortgage_pay/
        _miss, so no separate accrue here -- the standalone `accrue()` is only the
        pure-invariant demo) -> pay salary -> appreciate -> recompute equity. The
        clock analog (reuse R3's discrete step)."""
        self.charge_mortgages()
        self.charge_rents()
        if salary:
            self.pay_salary()
        self.appreciate()
        self.recompute_equity()

    # ------------------------------------------------- glass-box read-offs
    def equity_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("equity", 0.0))

    def reserves(self):
        return float(self.eng.node(self._bank)["attrs"].get("reserves", 0.0))

    def scrooge_coin(self):
        return self.coin_of(self._scrooge)

    def bank_rate_bp(self):
        return float(self.eng.node(self._bank)["attrs"].get("rate_bp", 0.0))

    def insolvent(self):
        return int(self.eng.node(self._bank)["attrs"].get("insolvent", 0.0))

    def homeless_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("homeless", 0.0))

    def social_concern_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("social_concern", 0.0))

    def backing_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("backing_landlord", 0.0))

    def balance_of(self, char):
        mort = self._mortgages.get(char)
        return float(self.eng.node(mort)["attrs"].get("balance", 0.0)) if mort else 0.0

    def missed_of(self, char):
        mort = self._mortgages.get(char)
        return int(self.eng.node(mort)["attrs"].get("missed", 0.0)) if mort else 0

    def period_of(self, char):
        mort = self._mortgages.get(char)
        return int(self.eng.node(mort)["attrs"].get("period", 0.0)) if mort else 0

    def foreclosed_of(self, char):
        mort = self._mortgages.get(char)
        return int(self.eng.node(mort)["attrs"].get("foreclosed", 0.0)) if mort else 0

    def rate_bp_of(self, char):
        mort = self._mortgages.get(char)
        return float(self.eng.node(mort)["attrs"].get("rate_bp", 0.0)) if mort else 0.0

    def rent_missed_of(self, tenant):
        r = self._rentals.get(tenant)
        return int(self.eng.node(r)["attrs"].get("missed", 0.0)) if r else 0

    def evicted_of(self, tenant):
        r = self._rentals.get(tenant)
        return int(self.eng.node(r)["attrs"].get("evicted", 0.0)) if r else 0

    def rent_of(self, tenant):
        r = self._rentals.get(tenant)
        return float(self.eng.node(r)["attrs"].get("rent", 0.0)) if r else 0.0

    def house_value_of(self, name):
        return float(self.eng.node(self._houses[name])["attrs"].get("value", 0.0))

    def owns_house(self, char, house):
        """Is `char` currently the owner of `house`? (Foreclosure transfers it.)"""
        h = self._houses[house]
        return h in list(self.eng.neighbours(self._movers[char], "owns_house"))

    def bank_owns(self, house):
        h = self._houses[house]
        return h in list(self.eng.neighbours(self._bank, "owns_house"))
