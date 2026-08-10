#!/usr/bin/env python3
"""Generate the integer energy ledger — the STOCK the option margin needs.

The agent already holds the accounting identity (`energy_balance`: "Intake =
expenditure + storage"; `energy_conservation`: "KE + PE + heat dissipated =
constant. Energy not lost, only converted.").  What it lacked was a ledger that
OPERATES it: consumption was measured on every receipt (`energy_cost_units`,
223 live writes; `peak_load_units`, 341) but nothing ever carried a LEVEL, so
the books could not close and monotonicity could not even be stated.

Deliberately built in the INTEGER frame.  The `*_joules` / `*_watts` vocabulary
declared on `EmbodiedEnergeticState` is template-only in a live graph — zero
instances after thirteen hours — and floats are cross-frame renderings anyway;
in-frame quantities are integers.

The two ceilings are kept apart, after the F16 fuel ledger:

    stock_units      AMOUNT ceiling — a finite stock; only expenditure removes it
    rate_ceiling     RATE ceiling  — how fast stock can be converted per action
    reachable_units  = min(stock, rate x horizon)   -- what is actually
                       reachable inside the loop's own declared horizon

Expenditure is SUMMED over linked receipts rather than accumulated, so posting
is idempotent by construction and the ledger cannot drift under a re-run
fixpoint.

Every quantity carries a `_measured` companion, after the F16 pattern
(`state_remaining_fuel_kg_measured`, `channel_reserve_measured`): a declared
default is usable but is never confusable with a measurement.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# A declared opening budget, used when no world publishes a measured one.
# Provenance travels with it: anything consuming the ledger can see that this
# number was declared rather than observed.
DEFAULT_OPENING_UNITS = 1000
DEFAULT_RATE_CEILING_UNITS = 50
DEFAULT_HORIZON_ACTIONS = 8


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(name, key): return {"type": "Attr", "node": V(name), "key": key}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Not(arg): return {"type": "Not", "arg": arg}
def N(name, edge): return {"type": "Neighbours", "node": V(name), "edge_type": edge}
def Exists(source, var, predicate): return {
    "type": "Exists", "source": source, "var_name": var, "predicate": predicate}
def Sum(source, var, value): return {
    "type": "Sum", "source": source, "var_name": var, "value": value}
def Min(*items): return {"type": "Min", "items": list(items)}
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(*items): return {"type": "Times", "items": list(items)}


def absent(source, var="prior"):
    return Not(Exists(source, var, L(True)))


def default0(name, key):
    """The tree's null-coalescing read. Used ONLY where 0 is the honest identity
    for an accounting column (an empty ledger really has spent nothing)."""
    return Plus(A(name, key), L(0))


def open_ledger_rule():
    return {
        "name": "enl_open_energy_ledger",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "One durable ledger per embodied episode. The opening balance is a "
            "DECLARED default, not a measurement, and says so: `stock_measured` "
            "is 0 until a world publishes an observed level. A declared budget "
            "is usable; it is never confusable with an observation."
        ),
        "match": [["agent", "has_embodied_development_episode", "episode"]],
        "where": absent(N("episode", "has_energy_ledger")),
        "effects": [
            ["add_node", "ledger", "EnergyLedger", {
                "opening_units": DEFAULT_OPENING_UNITS,
                "intake_units": 0,
                "expenditure_units": 0,
                "stock_units": DEFAULT_OPENING_UNITS,
                "stock_measured": 0,
                "rate_ceiling_units": DEFAULT_RATE_CEILING_UNITS,
                "rate_ceiling_measured": 0,
                "horizon_actions": DEFAULT_HORIZON_ACTIONS,
                "reachable_units": 0,
                "posted_receipt_count": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "episode", "has_energy_ledger", "ledger"],
        ],
    }


def post_receipt_rule():
    return {
        "name": "enl_post_closed_receipt_to_ledger",
        "area": "general_cognition",
        "latency_class": "soft_realtime",
        "comment": (
            "A causally closed receipt is an accounting document. Posting is an "
            "EDGE only — the amount is never accumulated into a running total, "
            "because a fixpoint that re-fires would double-count it. The balance "
            "is summed from the posted set instead, so posting is idempotent by "
            "construction and the ledger cannot drift."
        ),
        "match": [
            ["episode", "has_energy_ledger", "ledger"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(default0("receipt", "development_receipt_closed"), L(1)),
            Not(Exists(N("ledger", "has_posted_receipt"), "posted",
                       {"type": "Eq", "a": V("posted"), "b": V("receipt")})),
        ),
        "effects": [["add_edge", "ledger", "has_posted_receipt", "receipt"]],
    }


def settle_rule():
    """storage = intake - expenditure, over the opening balance.

    The agent's own held identity (`energy_balance`: intake = expenditure +
    storage), rearranged for the column the ledger carries.
    """
    expenditure = Sum(N("ledger", "has_posted_receipt"), "posted",
                      default0("posted", "energy_cost_units"))
    return {
        "name": "enl_settle_energy_balance",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "Intake = expenditure + storage, the identity the agent already "
            "holds, evaluated over the posted set. Recomputed from the documents "
            "every pass rather than carried forward, so it is always exactly the "
            "sum of what was posted. With no intake source the stock is monotone "
            "non-increasing — which is the claim an aircraft's throttle "
            "falsifies and which only closes once the convertible stock is "
            "carried as its own column."
        ),
        # UNCONDITIONAL by necessity and by design.  `Sum` over `Neighbours`
        # evaluates to 0 inside a `where` while the identical expression yields
        # the true total in an effect — measured, not assumed — so the balance
        # cannot be guarded on its own value.  It does not need to be: the rule
        # is a pure function of the posted set, so re-firing rewrites the same
        # numbers.  `test_posting_is_idempotent_under_a_re_run_fixpoint` is the
        # standing proof that this neither drifts nor fails to terminate.
        "match": [["episode", "has_energy_ledger", "ledger"]],
        "where": L(True),
        "effects": [
            ["set_attr", "ledger", "expenditure_units", {"__term__": expenditure}],
            ["set_attr", "ledger", "stock_units", {"__term__": Minus(
                Plus(default0("ledger", "opening_units"),
                     default0("ledger", "intake_units")),
                expenditure)}],
            ["set_attr", "ledger", "posted_receipt_count", {"__term__": {
                "type": "Count", "source": N("ledger", "has_posted_receipt")}}],
        ],
    }


def reachable_rule():
    """The two ceilings, kept apart and combined only here."""
    reachable = Min(
        default0("ledger", "stock_units"),
        Times(default0("ledger", "rate_ceiling_units"),
              default0("ledger", "horizon_actions")),
    )
    return {
        "name": "enl_project_reachable_within_horizon",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "reachable = min(stock, rate x horizon). The AMOUNT ceiling and the "
            "RATE ceiling are different quantities and neither alone answers "
            "affordability: a full tank cannot be spent faster than the actuator "
            "converts it, and an unlimited conversion rate cannot spend a tank "
            "that is empty. This is the humanoid form of the F16 fuel ledger's "
            "min(remaining fuel, max power x H)."
        ),
        # Unconditional for the same reason as the settle rule: a pure function
        # of two columns, so re-firing rewrites the same number.
        "match": [["episode", "has_energy_ledger", "ledger"]],
        "where": L(True),
        "effects": [["set_attr", "ledger", "reachable_units", {"__term__": reachable}]],
    }


def observe_rate_ceiling_rule():
    """Raise the declared rate ceiling to the observed peak, and say it is measured.

    A declared ceiling below what the body has demonstrably produced is not a
    ceiling; the observation supersedes the default and the provenance flips.
    """
    observed = {"type": "Max", "items": [
        default0("ledger", "rate_ceiling_units"),
        default0("receipt", "peak_load_units"),
    ]}
    return {
        "name": "enl_raise_rate_ceiling_to_observed_peak",
        "area": "general_cognition",
        "latency_class": "soft_realtime",
        "comment": (
            "A ceiling the body has already exceeded was never the ceiling. The "
            "observed peak supersedes the declared default and `rate_ceiling_"
            "measured` flips to 1, so a consumer can tell an observed limit from "
            "an assumed one."
        ),
        "match": [
            ["ledger", "has_posted_receipt", "receipt"],
        ],
        "where": Gt(default0("receipt", "peak_load_units"),
                    default0("ledger", "rate_ceiling_units")),
        "effects": [
            ["set_attr", "ledger", "rate_ceiling_units", {"__term__": observed}],
            ["set_attr", "ledger", "rate_ceiling_measured", 1],
        ],
    }


def manifest() -> dict:
    return {
        "id": "energy_ledger",
        "version": "1.0.0",
        "depends_on": ["embodied_learning_session"],
        "description": (
            "THE STOCK. Consumption was already measured on every receipt; no "
            "level was ever carried, so the books could not close and the "
            "option margin had no affordability term. This carries opening, "
            "intake, expenditure and stock as integer columns, keeps the AMOUNT "
            "and RATE ceilings apart, and projects reachable = min(stock, rate x "
            "horizon). Expenditure is summed from posted receipts rather than "
            "accumulated, so it is idempotent under the fixpoint. Every quantity "
            "carries a `_measured` companion so a declared default is never "
            "confusable with an observation."
        ),
        "microtheory": "energy_ledger",
        "nodes": [],
        "edges": [],
        "productions": [
            {"provenance": "seed:energy_ledger:has_energy_ledger-0",
             "src": {"type": "EmbodiedDevelopmentEpisode", "var": "s"},
             "edge_type": "has_energy_ledger",
             "tgt": {"type": "EnergyLedger", "var": "t"}},
            {"provenance": "seed:energy_ledger:has_posted_receipt-1",
             "src": {"type": "EnergyLedger", "var": "s"},
             "edge_type": "has_posted_receipt",
             "tgt": {"type": "EmbodiedLearningTrialReceipt", "var": "t"}},
        ],
        "rules": [
            open_ledger_rule(),
            post_receipt_rule(),
            settle_rule(),
            reachable_rule(),
            observe_rate_ceiling_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "energy_ledger.json"
    output.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
