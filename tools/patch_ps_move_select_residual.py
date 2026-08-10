#!/usr/bin/env python3
"""patch_ps_move_select_residual — HOOK the held-residual weight into the
EXISTING weighted collapse (`ps_move_select`, seeds/program_synthesis.json).

WHY THIS RULE AND NOT A NEW ONE.  `ps_move_select` is this project's canonical
weighted collapse — its own comment says so: *"WEIGHTED COLLAPSE: Argmax over
every candidate MoveCandidate ... by weight = ps_move_w_gap*gap +
ps_move_w_arity*arity_gap - ps_move_w_mdl*mdl_bits -- coefficients read from
the GOAL's own attrs (graph data ... tunable without code or rule changes)."*
It already separates POOL MEMBERSHIP (refutation and the gap>0 earns-its-keep
gate, both `where`/`Filter` predicates) from WEIGHT (the Argmax value).  A held
residual belongs on the WEIGHT side of that line, and this patch puts it there
and nowhere else — the pool filters are untouched, so a residual can never
remove a candidate from consideration.  That is the difference between a weight
and a veto, and here it is structural rather than a promise.

WHAT CHANGES, exactly:
  * `ps_move_mark`   +1 effect  — stamps `ps_move_w_residual` (1.0) onto the
                                  goal alongside the three existing
                                  coefficients, so the residual term is tunable
                                  as graph data like every other term.
  * `ps_move_select`  weight    — `... - ps_move_w_residual * PENALTY(mc)`,
                                  substituted in EVERY Argmax in the rule's
                                  effects (five of them) so no two selected
                                  facts can come from different rankings.
  The audit read-out (`ps_move_sel_residual_penalty`) is NOT added here: it is
  `gr_move_sel_audit` in seeds/goal_residuals.json, so the residual bookkeeping
  lives with the residuals and the synthesis seed carries only the weight.

INERT BY CONSTRUCTION.  `PENALTY` is `IfThenElse(Exists matching residual, max
weight, 0.0)`, and a candidate with no `sig_seam` matches nothing, so for every
MoveCandidate `domains/prog_moves.py` mints today the subtracted term is
exactly `0.0`.  (`Times(w, null)` evaluates to `w` in this engine — measured —
which is why the zero is an explicit `IfThenElse` branch and not a null.)

  PYTHONPATH=runners/dsl/python:. python tools/patch_ps_move_select_residual.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tools.build_goal_residual_seed import A, L, ITE, PENALTY, V  # noqa: E402

SEED = os.path.join(ROOT, "seeds", "program_synthesis.json")
NEW_VERSION = "1.12.0"

OLD_WEIGHT = {
    "type": "Minus",
    "a": {"type": "Plus", "items": [
        {"type": "Times", "items": [A("g", "ps_move_w_gap"), A("mc", "gap")]},
        {"type": "Times", "items": [A("g", "ps_move_w_arity"),
                                    A("mc", "arity_gap")]},
    ]},
    "b": {"type": "Times", "items": [A("g", "ps_move_w_mdl"),
                                     A("mc", "mdl_bits")]},
}

# `ps_move_w_residual` defaults to 1.0 when a goal predates this patch, so an
# older graph is weighted identically rather than multiplied by null.
W_RES = ITE(
    {"type": "Eq", "a": A("g", "ps_move_w_residual"), "b": L(None)},
    L(1.0), A("g", "ps_move_w_residual"))

NEW_WEIGHT = {
    "type": "Minus",
    "a": OLD_WEIGHT,
    "b": {"type": "Times", "items": [W_RES, PENALTY("mc")]},
}


def _sub(node, old, new, counter):
    """Structural substitution of `old` by `new` anywhere inside `node`."""
    if node == old:
        counter[0] += 1
        return json.loads(json.dumps(new))
    if isinstance(node, dict):
        return {k: _sub(v, old, new, counter) for k, v in node.items()}
    if isinstance(node, list):
        return [_sub(v, old, new, counter) for v in node]
    return node


def main() -> int:
    with open(SEED) as fh:
        seed = json.load(fh)

    n_sub = [0]
    for rule in seed["rules"]:
        if rule["name"] == "ps_move_mark":
            keys = [e[2] for e in rule["effects"]]
            if "ps_move_w_residual" not in keys:
                rule["effects"].append(
                    ["set_attr", "g", "ps_move_w_residual", 1.0])
                rule["comment"] += (
                    "  v1.12.0 (goal residuals): also stamps ps_move_w_residual "
                    "-- the coefficient on the HELD-REFUTATION term "
                    "ps_move_select subtracts.  Same shape as the other three: "
                    "graph data on the goal, tunable without touching a rule or "
                    "a line of Python.")
        if rule["name"] == "ps_move_select":
            rule["effects"] = _sub(rule["effects"], OLD_WEIGHT, NEW_WEIGHT, n_sub)
            rule["comment"] += (
                    "  v1.12.0 (GOAL RESIDUALS -- measured ceilings, graph-"
                    "resident): the weight gains one more term, "
                    "`- ps_move_w_residual * PENALTY(mc)`, where PENALTY is the "
                    "weight of the STRONGEST non-stale GoalResidual whose goal "
                    "signature matches this candidate's (0.0 when none does, so "
                    "the term is identically absent for every unsignatured "
                    "candidate -- which is every candidate prog_moves.py mints "
                    "today).  A refutation the agent already holds is a WEIGHT, "
                    "not a veto: it is subtracted INSIDE the Argmax and appears "
                    "NOWHERE in the pool filters, so a candidate with a large "
                    "enough gap still wins over a held residual.  Pursuing an "
                    "unreachable goal is legitimate -- that is how residuals get "
                    "made; being confidently wrong where the residual is already "
                    "held is not.  The penalty is computed INLINE rather than "
                    "read from an attr, so the selection can never depend on "
                    "whether gr_move_penalty's audit stamp has been written yet "
                    "in the fixpoint; gr_move_sel_audit "
                    "(seeds/goal_residuals.json) copies the winner's charge onto "
                    "the goal afterwards.")

    if n_sub[0] == 0:
        print("no substitution made -- already patched?")
        return 1
    seed["version"] = NEW_VERSION
    with open(SEED, "w") as fh:
        json.dump(seed, fh, indent=2)
        fh.write("\n")
    print("patched %s: %d weight substitutions, version -> %s"
          % (SEED, n_sub[0], NEW_VERSION))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
