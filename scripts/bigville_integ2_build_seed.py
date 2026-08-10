"""bigville_integ2_build_seed -- EMIT the conserving-transfer seed
`seeds/bigville_integ2_conserve.json` (block 273000, R10b DEFECT 1).

A seed AUTHORING script (emits graph data, no agent logic) in the same class as
the other one-off `tools/` seed builders. It writes the double-entry conservation
rules that close the R4/R17 coin-conservation leak diagnosed in R10:

  af_outcome_work credits a worker +5 coin as a SOURCE with NO sink -> the assembled
  town's total coin inflated ~35x. These rules give every affect-outcome coin move a
  MATCHING counter-move against a WagePool employer/output account, so Sigma(coin) is
  INVARIANT across the whole run (the frame/continuum conservation invariant).

Each rule fires on an INDEPENDENT `wsink_armed` flag (armed by the integ2 world in
parallel with `outcome_armed`), so it NEVER races the landed `af_outcome_*` rules
(which consume `outcome_armed`): one credit, one debit, race-free. The rules are
prefixed `bi2_` and edit no landed seed.
"""
from __future__ import annotations

import json
import os


def var(n):
    return {"type": "Var", "name": n}


def attr(node, key):
    # missing-tolerant read: (node.key + 0.0), the convention the landed seeds use.
    return {"type": "Plus", "items": [
        {"type": "Attr", "node": var(node), "key": key},
        {"type": "Lit", "value": 0.0}]}


def lit(v):
    return {"type": "Lit", "value": float(v)}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def andt(*items):
    return {"type": "And", "items": list(items)}


# match: the WagePool `pays` this worker (pool -pays-> m, one incoming per m), and
# the worker is at a cell. Binds pool + m + cur.
MATCH = [["pool", "pays", "m"], ["m", "is_at", "cur"]]


def outcome_rule(name, action_code, pool_delta):
    """A conserving counter-move to one af_outcome_* rule. When the worker's chosen
    action == `action_code` and the sink is armed, move `pool_delta` onto the pool
    (negative = pool pays the wage; positive = the worker's loss returns to the pool),
    exactly mirroring the af_outcome coin move of the OPPOSITE sign. Then disarm."""
    where = andt(eq(attr("m", "wsink_armed"), lit(1.0)),
                 eq(attr("m", "chosen_action"), lit(float(action_code))))
    new_pool = plus(attr("pool", "coin"), lit(float(pool_delta)))
    return {
        "name": name, "batch": False, "match": MATCH, "where": where,
        "effects": [
            ["set_attr", "pool", "coin", {"__term__": new_pool}],
            ["set_attr", "m", "wsink_armed", 0.0],
        ],
    }


def idle_rule():
    """Catch-all disarm: if the sink is armed but the chosen action is none of the
    four coin-moving outcomes, just clear the flag (no coin moves -- nothing to
    conserve). Keeps the flag from ever sticking."""
    where = andt(eq(attr("m", "wsink_armed"), lit(1.0)),
                 {"type": "Not", "arg": {"type": "Or", "items": [
                     eq(attr("m", "chosen_action"), lit(1.0)),
                     eq(attr("m", "chosen_action"), lit(2.0)),
                     eq(attr("m", "chosen_action"), lit(3.0)),
                     eq(attr("m", "chosen_action"), lit(4.0))]}})
    return {"name": "bi2_outcome_idle", "batch": False, "match": MATCH,
            "where": where,
            "effects": [["set_attr", "m", "wsink_armed", 0.0]]}


def main():
    seed = {
        "id": "bigville_integ2_conserve",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R10b (block 273000) DEFECT 1 -- close the R4/R17 coin-"
            "conservation leak. af_outcome_work credits +5 with no sink; these "
            "bi2_ rules give every affect-outcome coin move a matching counter-move "
            "against a WagePool employer/output account (pool -pays-> worker), so "
            "Sigma(coin) is INVARIANT across the whole run. Fires on an independent "
            "wsink_armed flag -> never races the landed af_outcome_* rules. "
            "INTEGRATION-LAYER fix: edits no landed rung seed; ZERO new Rust."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": [
            # work: af_outcome_work credits worker +5  -> pool pays 5 (pool -= 5)
            outcome_rule("bi2_work_sink", 1, -5.0),
            # withdraw: af_outcome_withdraw debits worker -2 -> returns to pool (+2)
            outcome_rule("bi2_withdraw_source", 2, +2.0),
            # drink: af_outcome_drink debits worker -3 -> returns to pool (+3)
            outcome_rule("bi2_drink_source", 3, +3.0),
            # snap: af_outcome_snap debits worker -1 -> returns to pool (+1)
            outcome_rule("bi2_snap_source", 4, +1.0),
            idle_rule(),
        ],
    }
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "seeds", "bigville_integ2_conserve.json")
    with open(out, "w") as f:
        json.dump(seed, f, indent=1)
    print("wrote", out, "rules:", [r["name"] for r in seed["rules"]])


if __name__ == "__main__":
    main()
