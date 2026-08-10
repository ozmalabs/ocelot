#!/usr/bin/env python3
"""bigville R7 (block 255000) SEED BUILDER -- emits the FINANCE rule seeds.

This is a TOOL (a seed BUILDER that emits graph data, explicitly allowed by
experiments/gamma-substrate/CLAUDE.md -- the same class as
`bigville_skill_gen_seeds.py`). It writes two self-contained seed manifests the
Rust runtime loads. NO agent decision lives here -- every finance DECISION
(accrue / set-rate / pay-vs-miss / foreclose / evict / salary / insolvency /
rent-raise) is a RULE in the emitted JSON; this file only assembles Term-trees.

ZERO new Rust. Interest -- the cross-frame MULTIPLICATIVE base (CLAUDE.md's
frame/continuum invariant: in-frame is INTEGER; non-integer math is CROSS-FRAME)
-- is a per-period integer arithmetic rule composing EXISTING DSL Terms. The
multiplicative step is round-half-up on integers via the pre-existing `IDiv`
(integer truncating division) Term -- NO `Round` primitive needed:

    balance' = IDiv( balance*(10000 + rate_bp) + 5000 , 10000 ) - payment

`rate_bp` is INTENSIONAL (basis points; the rule parameter / the cross-frame
map); the balance is OBSERVED STEPPED as INTEGER coin each period. No float ever
lives in a frame.

  seeds/bigville_fin_bank.json    -- the BANK ENTITY run by Scrooge McBankFace:
        bf_accrue (interest), bf_set_rate (Scrooge's decision_value), bf_salary
        (bank->Scrooge, funds separate), bf_insolvent (systemic).

  seeds/bigville_fin_tenure.json  -- housing tenure + payments + foreclosure /
        eviction + equity divergence + the rentier lever:
        bf_mortgage_pay / bf_mortgage_miss / bf_foreclose / bf_rent_pay /
        bf_rent_miss / bf_evict / bf_homeless_affect / bf_owner_equity /
        bf_mortgagor_equity / bf_appreciate / bf_rent_raise.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEEDS = os.path.join(ROOT, "seeds")

# interest denominator: basis points. rate_bp is an INTEGER (e.g. 1000 = 10%).
BP = 10000
HALF_BP = 5000          # round-half-up: add denom/2 before the integer divide


# ---- Term-tree helpers (compose EXISTING DSL Terms; no new Rust) -------------
def var(n):
    return {"type": "Var", "name": n}


def lit(v):
    return {"type": "Lit", "value": float(v)}


def ilit(v):
    """An INTEGER literal (decodes to Value::Int) -- used for the interest
    constants so the whole IDiv numerator/denominator stays integer."""
    return {"type": "Lit", "value": int(v)}


def attr(node, key):
    """Read attr as a number with default 0 (the `Plus[Attr, 0]` idiom the R4/R6
    seeds use so a missing key never aborts a match)."""
    return {"type": "Plus", "items": [
        {"type": "Attr", "node": var(node), "key": key}, lit(0)]}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def times(*items):
    return {"type": "Times", "items": list(items)}


def idiv(a, b):
    """Integer truncating division (the pre-existing IDiv Term). Round-half-up on
    positive integers is `IDiv(x + denom/2, denom)`."""
    return {"type": "IDiv", "a": a, "b": b}


def mx(*items):
    return {"type": "Max", "items": list(items)}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def lte(a, b):
    return {"type": "Lte", "a": a, "b": b}


def a_and(*items):
    return {"type": "And", "items": list(items)}


def a_not(arg):
    return {"type": "Not", "arg": arg}


def term(t):
    return {"__term__": t}


# ---- the INTEREST step (the invariant headline) -----------------------------
# balance' = IDiv( balance*(BP + rate_bp) + BP/2 , BP )
# multiplicative (1+r) with r = rate_bp/BP applied INTENSIONALLY; the result is an
# INTEGER coin balance (round-half-up), never a fractional in-frame float.
def accrue_step(mort):
    bal = attr(mort, "balance")
    rate = attr(mort, "rate_bp")
    grown = plus(times(bal, plus(ilit(BP), rate)), ilit(HALF_BP))
    return idiv(grown, ilit(BP))


# interest_due this period = round(balance * rate_bp / 10000), integer coin.
def interest_due(mort):
    return idiv(plus(times(attr(mort, "balance"), attr(mort, "rate_bp")),
                     ilit(HALF_BP)), ilit(BP))


# the REQUIRED periodic payment = interest_due (RATE-SCALED) + the fixed principal
# portion ('payment' attr). A higher rate raises interest_due -> raises the required
# payment -> a marginal-income debtor can no longer afford it -> misses. This is how
# the RATE (Scrooge's decision) drives foreclosures (G-interest-is-policy).
def required_payment(mort):
    return plus(interest_due(mort), attr(mort, "payment"))


# ============================================================ THE BANK ENTITY
def build_bank():
    rules = []

    # --- bf_accrue: the multiplicative interest step (the invariant) ----------
    rules.append({
        "name": "bf_accrue",
        "match": [["debtor", "has_mortgage", "mort"]],
        "where": a_and(
            eq(attr("mort", "accrue_armed"), lit(1.0)),
            eq(attr("mort", "foreclosed"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "mort", "balance", term(accrue_step("mort"))],
            ["set_attr", "mort", "period",
             term(plus(attr("mort", "period"), lit(1.0)))],
            ["set_attr", "mort", "accrue_armed", 0.0],
        ],
    })

    # --- bf_set_rate: the RATE IS SCROOGE'S DECISION (decision_value) ----------
    # bank.rate_bp and every issued mortgage's rate_bp <- fair + greed premium.
    chosen = plus(attr("scrooge", "fair_rate_bp"),
                  attr("scrooge", "greed_premium_bp"))
    rules.append({
        "name": "bf_set_rate",
        "match": [["bank", "run_by", "scrooge"], ["bank", "issued", "mort"]],
        "where": eq(attr("bank", "rate_armed"), lit(1.0)),
        "effects": [
            ["set_attr", "bank", "rate_bp", term(chosen)],
            ["set_attr", "mort", "rate_bp", term(chosen)],
            ["set_attr", "bank", "rate_armed", 0.0],
        ],
    })

    # --- bf_salary: bank->Scrooge SALARY (funds SEPARATE from reserves) --------
    # personal wealth accrues from the salary, NOT the reserves. Only pays if the
    # bank can afford it (reserves >= salary) and a salary is set (> 0: the
    # no-salary ablation control).
    rules.append({
        "name": "bf_salary",
        "match": [["bank", "run_by", "scrooge"]],
        "where": a_and(
            eq(attr("bank", "salary_armed"), lit(1.0)),
            gt(attr("bank", "salary"), lit(0.0)),
            gte(attr("bank", "reserves"), attr("bank", "salary")),
        ),
        "effects": [
            ["set_attr", "bank", "reserves",
             term(minus(attr("bank", "reserves"), attr("bank", "salary")))],
            ["set_attr", "scrooge", "coin",
             term(plus(attr("scrooge", "coin"), attr("bank", "salary")))],
            ["set_attr", "bank", "salary_armed", 0.0],
        ],
    })

    # --- bf_insolvent: SYSTEMIC credit event, distinct from Scrooge's wealth ---
    rules.append({
        "name": "bf_insolvent",
        "match": [["bank", "run_by", "scrooge"]],
        "where": a_and(
            lte(attr("bank", "reserves"), lit(0.0)),
            eq(attr("bank", "insolvent"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "bank", "insolvent", 1.0],
        ],
    })

    return {
        "id": "bigville_fin_bank",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R7 (block 255000) -- the BANK ENTITY run by the banker AGENT "
            "Scrooge McBankFace (NOT a magic third party): funds SEPARATE from his "
            "personal coin. bf_accrue is INTEREST -- the cross-frame MULTIPLICATIVE "
            "base (CLAUDE.md invariant): balance' = IDiv(balance*(10000+rate_bp)+5000, "
            "10000), round-half-up on integers via the pre-existing IDiv Term (NO new "
            "Rust, NO Round primitive), so rate_bp is INTENSIONAL (basis points, the "
            "cross-frame map) and the balance is OBSERVED STEPPED as INTEGER coin -- no "
            "float lives in a frame. bf_set_rate makes the rate Scrooge's decision_value "
            "(fair_rate_bp + greed_premium_bp) propagated to every issued mortgage. "
            "bf_salary transfers bank->Scrooge each cycle iff reserves>=salary>0 (his "
            "personal wealth tracks the salary, not the reserves; salary=0 is the "
            "ablation). bf_insolvent flags reserves<=0 -- a systemic event DISTINCT from "
            "Scrooge's personal wealth. Composes existing Terms; zero new Rust."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


# ================================================== TENURE / PAYMENTS / EQUITY
def build_tenure():
    rules = []

    # match reused by pay / miss / foreclose: debtor -has_mortgage-> mort
    #   -secured_on-> house, bank -issued-> mort.
    mort_match = [
        ["debtor", "has_mortgage", "mort"],
        ["mort", "secured_on", "house"],
        ["bank", "issued", "mort"],
    ]

    # --- bf_mortgage_pay: coin >= interest_due + principal -> service the loan -
    # transfer (interest_due + principal) to the bank; the balance drops by the
    # PRINCIPAL portion (interest is the bank's revenue, not capitalised). This is
    # the prereg's `balance' = round(balance*(1+r)) - payment` in the paid case.
    rules.append({
        "name": "bf_mortgage_pay",
        "match": mort_match,
        "where": a_and(
            eq(attr("debtor", "pay_armed"), lit(1.0)),
            eq(attr("mort", "foreclosed"), lit(0.0)),
            gte(attr("debtor", "coin"), required_payment("mort")),
        ),
        "effects": [
            ["set_attr", "debtor", "coin",
             term(minus(attr("debtor", "coin"), required_payment("mort")))],
            ["set_attr", "bank", "reserves",
             term(plus(attr("bank", "reserves"), required_payment("mort")))],
            ["set_attr", "mort", "balance",
             term(minus(attr("mort", "balance"), attr("mort", "payment")))],
            ["set_attr", "mort", "period",
             term(plus(attr("mort", "period"), lit(1.0)))],
            ["set_attr", "mort", "missed", 0.0],
            ["set_attr", "debtor", "pay_armed", 0.0],
        ],
    })

    # --- bf_mortgage_miss: coin < required -> a MISSED payment (DISJOINT) ------
    # the unpaid interest CAPITALISES: balance' = round(balance*(1+r)) (the debt
    # spiral). A higher rate makes the required payment unaffordable sooner.
    rules.append({
        "name": "bf_mortgage_miss",
        "match": mort_match,
        "where": a_and(
            eq(attr("debtor", "pay_armed"), lit(1.0)),
            eq(attr("mort", "foreclosed"), lit(0.0)),
            lt(attr("debtor", "coin"), required_payment("mort")),
        ),
        "effects": [
            ["set_attr", "mort", "balance", term(accrue_step("mort"))],
            ["set_attr", "mort", "period",
             term(plus(attr("mort", "period"), lit(1.0)))],
            ["set_attr", "mort", "missed",
             term(plus(attr("mort", "missed"), lit(1.0)))],
            ["set_attr", "debtor", "pay_armed", 0.0],
        ],
    })

    # --- bf_foreclose: missed >= term -> the bank SEIZES the LAND+building -----
    rules.append({
        "name": "bf_foreclose",
        "match": mort_match + [["debtor", "owns_house", "house"]],
        "where": a_and(
            eq(attr("mort", "foreclosed"), lit(0.0)),
            gte(attr("mort", "missed"), attr("mort", "term")),
        ),
        "effects": [
            ["set_attr", "mort", "foreclosed", 1.0],
            ["del_edge", "debtor", "owns_house", "house"],
            ["add_edge", "bank", "owns_house", "house"],
            ["set_attr", "debtor", "homeless", 1.0],
            ["set_attr", "debtor", "equity", 0.0],
        ],
    })

    # rental match: tenant -rents-> rental -landlord-> ll
    rent_match = [
        ["tenant", "rents", "rental"],
        ["rental", "landlord", "ll"],
    ]

    # --- bf_rent_pay: coin >= rent -> transfer to landlord (no equity built) ---
    rules.append({
        "name": "bf_rent_pay",
        "match": rent_match,
        "where": a_and(
            eq(attr("tenant", "rent_armed"), lit(1.0)),
            eq(attr("rental", "evicted"), lit(0.0)),
            gte(attr("tenant", "coin"), attr("rental", "rent")),
        ),
        "effects": [
            ["set_attr", "tenant", "coin",
             term(minus(attr("tenant", "coin"), attr("rental", "rent")))],
            ["set_attr", "ll", "coin",
             term(plus(attr("ll", "coin"), attr("rental", "rent")))],
            ["set_attr", "rental", "missed", 0.0],
            ["set_attr", "tenant", "rent_armed", 0.0],
        ],
    })

    # --- bf_rent_miss: coin < rent -> a MISSED rent (DISJOINT) -----------------
    rules.append({
        "name": "bf_rent_miss",
        "match": rent_match,
        "where": a_and(
            eq(attr("tenant", "rent_armed"), lit(1.0)),
            eq(attr("rental", "evicted"), lit(0.0)),
            lt(attr("tenant", "coin"), attr("rental", "rent")),
        ),
        "effects": [
            ["set_attr", "rental", "missed",
             term(plus(attr("rental", "missed"), lit(1.0)))],
            ["set_attr", "tenant", "rent_armed", 0.0],
        ],
    })

    # --- bf_evict: missed >= term -> homelessness (landlord keeps the house) ---
    rules.append({
        "name": "bf_evict",
        "match": rent_match,
        "where": a_and(
            eq(attr("rental", "evicted"), lit(0.0)),
            gte(attr("rental", "missed"), attr("rental", "term")),
        ),
        "effects": [
            ["set_attr", "rental", "evicted", 1.0],
            ["set_attr", "tenant", "homeless", 1.0],
        ],
    })

    # --- bf_homeless_affect: distress (the 204000/239000 channel) --------------
    # exactly like R4 be_default_affect: a homeless Mover with an AffectiveState
    # gets arousal up / valence down, once (homeless_affect_done guard).
    rules.append({
        "name": "bf_homeless_affect",
        "match": [["m", "has_affective_state", "aff"]],
        "where": a_and(
            eq(attr("m", "homeless"), lit(1.0)),
            eq(attr("m", "homeless_affect_done"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "aff", "arousal",
             term(plus(attr("aff", "arousal"), attr("aff", "concern_mag")))],
            ["set_attr", "aff", "valence",
             term(minus(attr("aff", "valence"), attr("aff", "concern_drop")))],
            ["set_attr", "m", "social_concern", 1.0],
            ["set_attr", "m", "homeless_affect_done", 1.0],
        ],
    })

    # --- bf_owner_equity: OWN outright (tenure=0) -> equity = house.value ------
    rules.append({
        "name": "bf_owner_equity",
        "match": [["owner", "owns_house", "house"]],
        "where": a_and(
            eq(attr("owner", "equity_armed"), lit(1.0)),
            eq(attr("owner", "tenure"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "owner", "equity", term(attr("house", "value"))],
            ["set_attr", "owner", "equity_armed", 0.0],
        ],
    })

    # --- bf_mortgagor_equity: tenure=1 -> equity = max(0, value - balance) -----
    rules.append({
        "name": "bf_mortgagor_equity",
        "match": [["debtor", "has_mortgage", "mort"], ["mort", "secured_on", "house"]],
        "where": a_and(
            eq(attr("debtor", "equity_armed"), lit(1.0)),
            eq(attr("debtor", "tenure"), lit(1.0)),
            eq(attr("mort", "foreclosed"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "debtor", "equity",
             term(mx(lit(0.0), minus(attr("house", "value"),
                                     attr("mort", "balance"))))],
            ["set_attr", "debtor", "equity_armed", 0.0],
        ],
    })

    # --- bf_appreciate: a house's value rises (owner/landlord equity rises) ----
    rules.append({
        "name": "bf_appreciate",
        "match": [["owner", "owns_house", "house"]],
        "where": eq(attr("house", "appreciate_armed"), lit(1.0)),
        "effects": [
            ["set_attr", "house", "value",
             term(plus(attr("house", "value"), attr("house", "apprec")))],
            ["set_attr", "house", "appreciate_armed", 0.0],
        ],
    })

    # --- bf_rent_raise: the RENTIER lever (John-as-slumlord, ties 239/247) -----
    # raising rent / threatening eviction moves the tenant's affect + backing:
    # economic coercive control.
    rules.append({
        "name": "bf_rent_raise",
        "match": rent_match + [["tenant", "has_affective_state", "aff"]],
        "where": eq(attr("rental", "raise_armed"), lit(1.0)),
        "effects": [
            ["set_attr", "rental", "rent",
             term(plus(attr("rental", "rent"), attr("rental", "raise_amount")))],
            ["set_attr", "rental", "threatened", 1.0],
            ["set_attr", "aff", "arousal",
             term(plus(attr("aff", "arousal"), attr("ll", "coerce_mag")))],
            ["set_attr", "aff", "valence",
             term(minus(attr("aff", "valence"), attr("ll", "coerce_drop")))],
            ["set_attr", "tenant", "backing_landlord",
             term(plus(attr("tenant", "backing_landlord"), lit(1.0)))],
            ["set_attr", "rental", "raise_armed", 0.0],
        ],
    })

    return {
        "id": "bigville_fin_tenure",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R7 (block 255000) -- housing TENURE (own/mortgage/rent), periodic "
            "payments, foreclosure/eviction -> HOMELESSNESS, tenure-driven EQUITY "
            "divergence, and the RENTIER lever. bf_mortgage_pay/miss are DISJOINT on the "
            "coin>=payment guard (an income collapse -> misses); bf_foreclose (missed>= "
            "term) transfers the LAND+building (owns_house edge) to the bank -- the "
            "ultimate collateral -- and sets homeless=1. bf_rent_pay/miss/evict mirror it "
            "for tenancy (the landlord keeps the house). bf_homeless_affect books the "
            "204000/239000 distress (arousal up / valence down + social_concern), exactly "
            "like R4 be_default_affect. Equity DIVERGES by tenure: bf_owner_equity "
            "(=house.value), bf_mortgagor_equity (=max(0,value-balance), rises as balance "
            "falls) -- a RENTER matches NO equity rule so his equity stays FLAT at 0. "
            "bf_appreciate raises a house's value (owner/landlord equity rises; a renter "
            "owns none). bf_rent_raise is John-as-slumlord: raising rent moves the "
            "tenant's affect + backing (economic coercive control, 239/247). Every "
            "decision a RULE; composes existing Terms; zero new Rust."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


def main():
    os.makedirs(SEEDS, exist_ok=True)
    for seed in (build_bank(), build_tenure()):
        path = os.path.join(SEEDS, seed["id"] + ".json")
        with open(path, "w") as f:
            json.dump(seed, f, indent=1)
        print("wrote", path, "--", len(seed["rules"]), "rules")


if __name__ == "__main__":
    main()
