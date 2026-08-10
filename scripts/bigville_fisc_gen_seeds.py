#!/usr/bin/env python3
"""bigville R9 (block 257000) SEED BUILDER -- emits the FISCAL + CHURCH rule seeds.

This is a TOOL (a seed BUILDER that emits graph data, explicitly allowed by
experiments/gamma-substrate/CLAUDE.md -- the same class as
`bigville_fin_gen_seeds.py`). It writes two self-contained, `self_load_only` seed
manifests the Rust runtime loads ONLY for the R9 adapter. NO agent decision lives
here -- every institutional DECISION (set-tax / collect / pay-salary / graft /
levy / tithe / donate / stipend / charity / defund-parsonage / counsel) is a RULE
in the emitted JSON; this file only assembles Term-trees.

ZERO new Rust. The town's institutional TRIAD adds its two FUNDING institutions on
top of R7's bank:

  * STATE / FISCAL -- taxes on landowners+workers at a rate SET BY THE COUNCIL (a
    decision_value, the fiscal lever -- TWIN of R7's bank rate) -> a `Treasury`
    purse -> the MAYOR's salary + the CONSTABLE's wage; money RE-ENTERS circulation
    when spent. Same principal/agent structure as the bank (a corrupt John grafts
    from the purse). `seeds/bigville_fisc_state.json`.

  * CHURCH -- funded by voluntary DONATION: the devout TITHE a committed fraction,
    others donate discretionary surplus when flush (a per-villager devotion axis).
    Church income funds Mary's STIPEND + parsonage (TIED housing) + CHARITY. NO
    lever (she can only ASK) -- procyclical + precarious. Plus co-regulation
    COUNSELLING (reuse the 239000 safety channel). `seeds/bigville_fisc_church.json`.

The frame/continuum invariant (CLAUDE.md) is respected exactly as in R7: a tax rate
and a tithe fraction are INTENSIONAL (basis points, the cross-frame map); every
collected/paid amount is OBSERVED STEPPED as INTEGER coin via the pre-existing
`IDiv` Term (round-half-up = `IDiv(x + denom/2, denom)`), never a fractional float
in a frame. No `Round`/`Floor`/`Div`-into-a-coin-attr anywhere.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEEDS = os.path.join(ROOT, "seeds")

BP = 10000
HALF_BP = 5000          # round-half-up: add denom/2 before the integer divide


# ---- Term-tree helpers (compose EXISTING DSL Terms; no new Rust) -------------
def var(n):
    return {"type": "Var", "name": n}


def lit(v):
    return {"type": "Lit", "value": float(v)}


def ilit(v):
    return {"type": "Lit", "value": int(v)}


def attr(node, key):
    """Read attr as a number with default 0 (the `Plus[Attr, 0]` idiom the R4/R7
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
    return {"type": "IDiv", "a": a, "b": b}


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


def term(t):
    return {"__term__": t}


# ---- the CROSS-FRAME rate/fraction step (the invariant, shared with R7) -------
# levy_due = round(base * rate_bp / BP) = IDiv(base*rate_bp + BP/2, BP), integer coin.
def scaled_due(base_node, base_key, rate_node, rate_key):
    base = attr(base_node, base_key)
    rate = attr(rate_node, rate_key)
    return idiv(plus(times(base, rate), ilit(HALF_BP)), ilit(BP))


# ================================================= THE STATE (FISCAL) ENTITY
def build_state():
    rules = []

    # --- fs_set_tax: the RATE IS THE COUNCIL'S DECISION (decision_value) -------
    # treasury.tax_rate_bp <- base_rate_bp + capture_premium_bp -- the TWIN of the
    # bank's bf_set_rate (fair + greed premium). A FAIR council sets premium=0; a
    # CAPTURED (John's) council sets a self-serving premium>0 (extracts more from
    # workers to fund the inflated mayoralty). The rate is POLICY, not a constant.
    chosen = plus(attr("council", "base_rate_bp"),
                  attr("council", "capture_premium_bp"))
    rules.append({
        "name": "fs_set_tax",
        "match": [["council", "sets_tax", "treasury"]],
        "where": eq(attr("council", "tax_armed"), lit(1.0)),
        "effects": [
            ["set_attr", "treasury", "tax_rate_bp", term(chosen)],
            ["set_attr", "council", "tax_rate_bp", term(chosen)],
            ["set_attr", "council", "tax_armed", 0.0],
        ],
    })

    # --- fs_collect: TAX collection -> the public purse ------------------------
    # per-payer arm (collect_armed on the payer, like R7's per-mortgage accrue_armed).
    # tax_due = round(payer.taxable * tax_rate_bp / BP), INTEGER coin (cross-frame
    # rate applied INTENSIONALLY). Paid iff the payer can afford it.
    tax_due = scaled_due("payer", "taxable", "treasury", "tax_rate_bp")
    rules.append({
        "name": "fs_collect",
        "match": [["treasury", "taxes", "payer"]],
        "where": a_and(
            eq(attr("payer", "collect_armed"), lit(1.0)),
            gte(attr("payer", "coin"), tax_due),
        ),
        "effects": [
            ["set_attr", "payer", "coin", term(minus(attr("payer", "coin"), tax_due))],
            ["set_attr", "treasury", "funds",
             term(plus(attr("treasury", "funds"), tax_due))],
            ["set_attr", "treasury", "revenue",
             term(plus(attr("treasury", "revenue"), tax_due))],
            ["set_attr", "payer", "collect_armed", 0.0],
        ],
    })

    # --- fs_pay_salary: the MAYOR/CONSTABLE are paid FROM the treasury ----------
    # per-servant arm. Paid iff the purse can afford it (the funding is LOAD-BEARING:
    # an empty treasury -> the salary is NOT paid, public services fail). Money
    # RE-ENTERS circulation when the servant later spends. salary>0 is the ablation.
    rules.append({
        "name": "fs_pay_salary",
        "match": [["treasury", "pays", "servant"]],
        "where": a_and(
            eq(attr("servant", "salary_armed"), lit(1.0)),
            gt(attr("servant", "salary"), lit(0.0)),
            gte(attr("treasury", "funds"), attr("servant", "salary")),
        ),
        "effects": [
            ["set_attr", "treasury", "funds",
             term(minus(attr("treasury", "funds"), attr("servant", "salary")))],
            ["set_attr", "servant", "coin",
             term(plus(attr("servant", "coin"), attr("servant", "salary")))],
            ["set_attr", "servant", "paid_count",
             term(plus(attr("servant", "paid_count"), lit(1.0)))],
            ["set_attr", "servant", "salary_armed", 0.0],
        ],
    })

    # --- fs_salary_unfunded: DISJOINT -- the purse can't pay -> public service FAILS
    rules.append({
        "name": "fs_salary_unfunded",
        "match": [["treasury", "pays", "servant"]],
        "where": a_and(
            eq(attr("servant", "salary_armed"), lit(1.0)),
            gt(attr("servant", "salary"), lit(0.0)),
            lt(attr("treasury", "funds"), attr("servant", "salary")),
        ),
        "effects": [
            ["set_attr", "servant", "unpaid", 1.0],
            ["set_attr", "servant", "salary_armed", 0.0],
        ],
    })

    # --- fs_treasury_empty: SYSTEMIC -- the purse, once FUNDED, is drained to empty
    # (public works fail). The revenue>0 guard is load-bearing: a treasury that is
    # trivially empty at BOOT (before any tax) is NOT "depleted" -- depletion is
    # having COLLECTED revenue and then had it drained (e.g. by graft).
    rules.append({
        "name": "fs_treasury_empty",
        "match": [["council", "sets_tax", "treasury"]],
        "where": a_and(
            gt(attr("treasury", "revenue"), lit(0.0)),
            lte(attr("treasury", "funds"), lit(0.0)),
            eq(attr("treasury", "depleted"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "treasury", "depleted", 1.0],
        ],
    })

    # --- fs_graft: MAYORAL CORRUPTION (the failing control) --------------------
    # a CORRUPT mayor funnels public funds to himself (inflates his take). Gated on
    # corrupt=1: a FAIR mayor (corrupt=0) never matches -> the purse sustains. Same
    # principal/agent structure as the greedy banker: his PERSONAL coin rises while
    # the purse he administers drains.
    rules.append({
        "name": "fs_graft",
        "match": [["treasury", "pays", "mayor"]],
        "where": a_and(
            eq(attr("mayor", "graft_armed"), lit(1.0)),
            eq(attr("mayor", "corrupt"), lit(1.0)),
            gt(attr("mayor", "graft_amount"), lit(0.0)),
            gte(attr("treasury", "funds"), attr("mayor", "graft_amount")),
        ),
        "effects": [
            ["set_attr", "treasury", "funds",
             term(minus(attr("treasury", "funds"), attr("mayor", "graft_amount")))],
            ["set_attr", "mayor", "coin",
             term(plus(attr("mayor", "coin"), attr("mayor", "graft_amount")))],
            ["set_attr", "mayor", "grafted",
             term(plus(attr("mayor", "grafted"), attr("mayor", "graft_amount")))],
            ["set_attr", "mayor", "graft_armed", 0.0],
        ],
    })

    # --- fs_levy: the POOLING force (the R7 interest attractor's essence) -------
    # coin flows FROM the worker payer TO the wealthy rentier (Scrooge's personal
    # purse) each period -- the "coin POOLS at the bank/wealthy" side of the money
    # model (spec sec 2). This is a lightweight, HONESTLY-labelled stand-in for R7's
    # full mortgage-interest drain (R7 imported read-only): the same direction of
    # flow (workers -> the wealthy). The redistribution loop (fs_collect + fs_pay_
    # salary) is what BREAKS this pooling fixpoint -- measured as money velocity.
    rules.append({
        "name": "fs_levy",
        "match": [["rich", "levies", "payer"]],
        "where": a_and(
            eq(attr("payer", "levy_armed"), lit(1.0)),
            gt(attr("rich", "levy_amount"), lit(0.0)),
            gte(attr("payer", "coin"), attr("rich", "levy_amount")),
        ),
        "effects": [
            ["set_attr", "payer", "coin",
             term(minus(attr("payer", "coin"), attr("rich", "levy_amount")))],
            ["set_attr", "rich", "coin",
             term(plus(attr("rich", "coin"), attr("rich", "levy_amount")))],
            ["set_attr", "payer", "levy_armed", 0.0],
        ],
    })

    return {
        "id": "bigville_fisc_state",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R9 (block 257000) -- the STATE / FISCAL institution: taxes on "
            "landowners+workers at a rate SET BY THE COUNCIL (fs_set_tax: a "
            "decision_value = base_rate_bp + capture_premium_bp, the TWIN of R7's bank "
            "rate -- a FAIR council premium=0, a CAPTURED John's council premium>0) -> a "
            "`Treasury` purse (fs_collect: tax_due = IDiv(taxable*rate+5000, 10000), "
            "INTEGER coin, the cross-frame rate applied INTENSIONALLY) -> the MAYOR's "
            "salary + the CONSTABLE's wage (fs_pay_salary, funded iff the purse can "
            "afford it; fs_salary_unfunded marks the public service FAILED when it "
            "can't). fs_treasury_empty flags a depleted purse (public works fail). "
            "fs_graft is MAYORAL CORRUPTION gated on corrupt=1 (the failing control: a "
            "fair mayor never matches -> the purse sustains; a corrupt one drains it to "
            "his PERSONAL coin -- the principal/agent divergence, the state twin of the "
            "greedy banker). fs_levy is the POOLING force (coin flows workers->the "
            "wealthy -- the R7 interest-attractor essence, honestly stand-in) that the "
            "tax+salary REDISTRIBUTION loop BREAKS. Composes existing Terms; zero new "
            "Rust; self_load_only so it cannot affect any other suite."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


# =============================================== THE CHURCH (DONATION) ENTITY
def build_church():
    rules = []

    # --- fc_tithe: a TITHER donates a COMMITTED FRACTION of income -------------
    # per-giver arm. tithe_due = round(income * tithe_bp / BP), INTEGER coin -- the
    # cross-frame fraction applied INTENSIONALLY (the same invariant as interest/tax).
    # A tither has tithe_bp>0.
    tithe_due = scaled_due("giver", "income", "giver", "tithe_bp")
    rules.append({
        "name": "fc_tithe",
        "match": [["church", "gathers", "giver"]],
        "where": a_and(
            eq(attr("giver", "donate_armed"), lit(1.0)),
            gt(attr("giver", "tithe_bp"), lit(0.0)),
            gte(attr("giver", "coin"), tithe_due),
        ),
        "effects": [
            ["set_attr", "giver", "coin", term(minus(attr("giver", "coin"), tithe_due))],
            ["set_attr", "church", "funds",
             term(plus(attr("church", "funds"), tithe_due))],
            ["set_attr", "church", "income_total",
             term(plus(attr("church", "income_total"), tithe_due))],
            ["set_attr", "giver", "donate_armed", 0.0],
        ],
    })

    # --- fc_donate_occasional: an OCCASIONAL giver donates surplus WHEN FLUSH ---
    # DISJOINT from the tither (tithe_bp=0). Gives a fixed discretionary amount iff
    # flush (coin > flush_threshold). devotion=none (tithe_bp=0 AND occasional=0)
    # matches NEITHER rule -> income 0 (ablate devotion -> church income -> 0).
    rules.append({
        "name": "fc_donate_occasional",
        "match": [["church", "gathers", "giver"]],
        "where": a_and(
            eq(attr("giver", "donate_armed"), lit(1.0)),
            eq(attr("giver", "tithe_bp"), lit(0.0)),
            eq(attr("giver", "occasional"), lit(1.0)),
            gt(attr("giver", "donate_amount"), lit(0.0)),
            gt(attr("giver", "coin"), attr("giver", "flush_threshold")),
        ),
        "effects": [
            ["set_attr", "giver", "coin",
             term(minus(attr("giver", "coin"), attr("giver", "donate_amount")))],
            ["set_attr", "church", "funds",
             term(plus(attr("church", "funds"), attr("giver", "donate_amount")))],
            ["set_attr", "church", "income_total",
             term(plus(attr("church", "income_total"), attr("giver", "donate_amount")))],
            ["set_attr", "giver", "donate_armed", 0.0],
        ],
    })

    # --- fc_stipend: the church pays Mary's STIPEND from its funds --------------
    # NO lever: paid iff donations sufficed (funds >= stipend). This is Mary's
    # precarity -- her pay depends on voluntary goodwill, not a compulsory tax.
    rules.append({
        "name": "fc_stipend",
        "match": [["church", "run_by", "mary"]],
        "where": a_and(
            eq(attr("church", "stipend_armed"), lit(1.0)),
            gt(attr("church", "stipend"), lit(0.0)),
            gte(attr("church", "funds"), attr("church", "stipend")),
        ),
        "effects": [
            ["set_attr", "church", "funds",
             term(minus(attr("church", "funds"), attr("church", "stipend")))],
            ["set_attr", "mary", "coin",
             term(plus(attr("mary", "coin"), attr("church", "stipend")))],
            ["set_attr", "mary", "paid_count",
             term(plus(attr("mary", "paid_count"), lit(1.0)))],
            ["set_attr", "church", "stipend_armed", 0.0],
        ],
    })

    # --- fc_stipend_unfunded: DISJOINT -- donations fell short -> Mary UNPAID ----
    rules.append({
        "name": "fc_stipend_unfunded",
        "match": [["church", "run_by", "mary"]],
        "where": a_and(
            eq(attr("church", "stipend_armed"), lit(1.0)),
            gt(attr("church", "stipend"), lit(0.0)),
            lt(attr("church", "funds"), attr("church", "stipend")),
        ),
        "effects": [
            ["set_attr", "mary", "unpaid", 1.0],
            ["set_attr", "church", "stipend_armed", 0.0],
        ],
    })

    # --- fc_charity: VOLUNTARY redistribution to the poor (Old Tussock) ---------
    # procyclical: paid iff funds >= charity_amount. In a downturn funds -> 0 ->
    # charity FAILS exactly when it is most needed (the voluntary sector breaks first).
    rules.append({
        "name": "fc_charity",
        "match": [["church", "gives_charity", "poor"]],
        "where": a_and(
            eq(attr("church", "charity_armed"), lit(1.0)),
            gt(attr("church", "charity_amount"), lit(0.0)),
            gte(attr("church", "funds"), attr("church", "charity_amount")),
        ),
        "effects": [
            ["set_attr", "church", "funds",
             term(minus(attr("church", "funds"), attr("church", "charity_amount")))],
            ["set_attr", "poor", "coin",
             term(plus(attr("poor", "coin"), attr("church", "charity_amount")))],
            ["set_attr", "church", "charity_given",
             term(plus(attr("church", "charity_given"), attr("church", "charity_amount")))],
            ["set_attr", "church", "charity_armed", 0.0],
        ],
    })

    # --- fc_charity_unfunded: DISJOINT -- the plate is empty -> charity FAILS ----
    rules.append({
        "name": "fc_charity_unfunded",
        "match": [["church", "gives_charity", "poor"]],
        "where": a_and(
            eq(attr("church", "charity_armed"), lit(1.0)),
            gt(attr("church", "charity_amount"), lit(0.0)),
            lt(attr("church", "funds"), attr("church", "charity_amount")),
        ),
        "effects": [
            ["set_attr", "church", "charity_failed", 1.0],
            ["set_attr", "church", "charity_armed", 0.0],
        ],
    })

    # --- fc_church_defunct: the church runs out of money -----------------------
    rules.append({
        "name": "fc_church_defunct",
        "match": [["church", "run_by", "mary"]],
        "where": a_and(
            lte(attr("church", "funds"), lit(0.0)),
            eq(attr("church", "defunct"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "church", "defunct", 1.0],
        ],
    })

    # --- fc_parsonage_precarious: TIED housing lost with the stipend -----------
    # the parsonage is TIED (not owned): if the church goes defunct, Mary loses BOTH
    # the stipend AND the roof -- a real stake on the materially-weakest institution.
    rules.append({
        "name": "fc_parsonage_precarious",
        "match": [["church", "houses", "mary"]],
        "where": a_and(
            eq(attr("church", "parsonage_armed"), lit(1.0)),
            eq(attr("church", "defunct"), lit(1.0)),
        ),
        "effects": [
            ["set_attr", "mary", "homeless", 1.0],
            ["del_edge", "church", "houses", "mary"],
            ["set_attr", "church", "parsonage_armed", 0.0],
        ],
    })

    # --- fc_counsel: private CO-REGULATION (reuse the 239000 safety channel) ----
    # a distressed (dysregulated) resident who APPROACHES a SAFE Mary (regulated,
    # non-judging: safe=1) returns TOWARD their window -- arousal falls, valence
    # rises. Gated on the COUNSELLOR's safety: a judging / dysregulated counsellor
    # (safe=0) never matches -> no return (co-reg FAILS, the 239 dysregulated-
    # caregiver control). Mechanism-identical to the caregiver safety signal.
    rules.append({
        "name": "fc_counsel",
        "match": [["resident", "seeks_counsel", "mary"],
                  ["resident", "has_affective_state", "aff"]],
        "where": a_and(
            eq(attr("resident", "counsel_armed"), lit(1.0)),
            eq(attr("mary", "safe"), lit(1.0)),
        ),
        "effects": [
            ["set_attr", "aff", "arousal",
             term(minus(attr("aff", "arousal"), attr("mary", "regulate_down")))],
            ["set_attr", "aff", "valence",
             term(plus(attr("aff", "valence"), attr("mary", "regulate_up")))],
            ["set_attr", "resident", "co_regulated", 1.0],
            ["set_attr", "resident", "counsel_armed", 0.0],
        ],
    })

    return {
        "id": "bigville_fisc_church",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R9 (block 257000) -- the CHURCH, the THIRD (voluntary, NO-lever) "
            "institution funded by DONATION. fc_tithe: a TITHER gives a COMMITTED "
            "FRACTION of income (tithe_due = IDiv(income*tithe_bp+5000, 10000), INTEGER "
            "coin -- the cross-frame fraction INTENSIONAL, the invariant shared with "
            "interest/tax). fc_donate_occasional: DISJOINT (tithe_bp=0) discretionary "
            "giving WHEN FLUSH; devotion=none matches NEITHER -> income 0 (ablate "
            "devotion -> 0). fc_stipend pays Mary FROM funds iff donations sufficed "
            "(fc_stipend_unfunded marks her UNPAID otherwise -- precarity, NO lever). "
            "fc_charity redistributes to the poor (fc_charity_unfunded: the plate is "
            "empty in a downturn -> charity FAILS when most needed -- procyclical). "
            "fc_church_defunct + fc_parsonage_precarious: a defunct church costs Mary "
            "the stipend AND the TIED parsonage. fc_counsel is CO-REGULATION (reuse the "
            "239000 safety channel): a distressed resident approaching a SAFE Mary "
            "returns toward the window (arousal down / valence up); a dysregulated "
            "counsellor (safe=0) -> no return (the 239 control). Composes existing "
            "Terms; zero new Rust; self_load_only."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


def main():
    os.makedirs(SEEDS, exist_ok=True)
    for seed in (build_state(), build_church()):
        path = os.path.join(SEEDS, seed["id"] + ".json")
        with open(path, "w") as f:
            json.dump(seed, f, indent=1)
        print("wrote", path, "--", len(seed["rules"]), "rules")


if __name__ == "__main__":
    main()
