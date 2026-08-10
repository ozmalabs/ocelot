#!/usr/bin/env python3
"""AUTHORING TOOL (block 265000, R17) — emits the five bigville_affect_* seed
manifests. NOT agent runtime: this script only ASSEMBLES Term-tree JSON (graph
data) and writes it to seeds/. Every DECISION lives in the emitted rules; this
file computes NO agent state. Re-run to regenerate the committed seeds
byte-for-byte.

  python scripts/bigville_affect_gen_seeds.py

Composes ONLY existing DSL Terms (Argmax / NodesOfType / Attr / Plus / Minus /
Times / Min / Max / Eq / Gt / Gte / Lt / And / Or / Not / IfThenElse / Lit /
Var). ZERO new Rust.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED_DIR = os.path.join(ROOT, "seeds")

# ---- Term builders (pure JSON assembly) ------------------------------------
def lit(v):            return {"type": "Lit", "value": float(v)}
def var(n):            return {"type": "Var", "name": n}
def attr(node, key):   return {"type": "Attr", "node": node, "key": key}
def av(name, key):     return attr(var(name), key)
def rd(name, key):     # read-with-default-0 idiom (as bigville_need_choice uses)
    return {"type": "Plus", "items": [av(name, key), lit(0.0)]}
def plus(*xs):         return {"type": "Plus", "items": list(xs)}
def minus(a, b):       return {"type": "Minus", "a": a, "b": b}
def times(*xs):        return {"type": "Times", "items": list(xs)}
def tmin(*xs):         return {"type": "Min", "items": list(xs)}
def tmax(*xs):         return {"type": "Max", "items": list(xs)}
def eq(a, b):          return {"type": "Eq", "a": a, "b": b}
def gt(a, b):          return {"type": "Gt", "a": a, "b": b}
def lt(a, b):          return {"type": "Lt", "a": a, "b": b}
def band(*xs):         return {"type": "And", "items": list(xs)}
def bnot(x):           return {"type": "Not", "arg": x}
def nodesof(t):        return {"type": "NodesOfType", "node_type": t}
def argmax(source, vn, value):
    return {"type": "Argmax", "source": source, "var_name": vn, "value": value}
def clamp01(x):        return tmax(lit(0.0), tmin(lit(1.0), x))
def term(t):           return {"__term__": t}


def rule(name, match, where, effects, batch=False):
    return {"name": name, "batch": batch, "match": match,
            "where": where, "effects": effects}


def seed(sid, desc, rules):
    return {"id": sid, "version": "1.0.0", "depends_on": [],
            "self_load_only": True, "description": desc,
            "nodes": [], "edges": [], "productions": [], "concepts": [],
            "rules": rules}


# =========================================================== the decision_value
# decision_value(act) = base_value(act)
#                       + affect_gain(m) * eff_distress(m) * grief_affinity(act)
# eff_distress = grief_distress * clamp01(1 - regulation)   -- co-regulation damps
def decision_value():
    eff = times(rd("m", "grief_distress"),
                clamp01(minus(lit(1.0), rd("m", "regulation"))))
    return plus(rd("act", "base_value"),
                times(rd("m", "affect_gain"), eff, rd("act", "grief_affinity")))


# ------------------------------------------------------ bigville_affect_grief
GRIEF = seed(
    "bigville_affect_grief",
    "BIGVILLE R17 (block 265000) -- af_grief_from_loss: a Loss{magnitude,kind,"
    "grieved} suffered by a person raises grief_distress by the loss magnitude "
    "(once, grieved guard). Grief is source-AGNOSTIC -- bereavement (R14 death), "
    "a failed dream (R8), a foreclosure (R7) are the SAME Loss with a different "
    "kind provenance tag; grief is grief. The initial loss is an exogenous shock; "
    "the spiral is endogenous. NO reward/punishment token. Composes existing "
    "Terms only; ZERO new Rust.",
    [rule(
        "af_grief_from_loss",
        [["p", "suffered", "loss"]],
        eq(rd("loss", "grieved"), lit(0.0)),
        [["set_attr", "p", "grief_distress",
          term(plus(rd("p", "grief_distress"), rd("loss", "magnitude")))],
         ["set_attr", "loss", "grieved", 1.0]],
    )],
)

# ----------------------------------------------------- bigville_affect_decide
DECIDE = seed(
    "bigville_affect_decide",
    "BIGVILLE R17 (block 265000) -- af_choose_action (THE HEADLINE): the chosen "
    "action is the decision_value Argmax over the Action menu (same Argmax family "
    "as nd_choose_good / ss_choose_burn). decision_value = base_value + "
    "affect_gain * eff_distress * grief_affinity, eff_distress = grief_distress * "
    "clamp01(1-regulation). work has high base + NEGATIVE grief affinity (grief "
    "makes work unreachable); withdraw/drink(self-medicate)/snap(lowered snap "
    "threshold -> R15 violence) have increasing positive affinities, so grief "
    "SHIFTS the Argmax from work toward withdrawal->drink->snap. affect_gain is "
    "the COUPLING KNOB and the FALSIFIER: affect_gain=0 removes grief from "
    "decision_value -> base_value only -> identical under grief and contentment = "
    "the proven DIORAMA. The affect is FELT only because it is a TERM in the "
    "selector. Composes existing Terms only; ZERO new Rust.",
    [rule(
        "af_choose_action",
        [["m", "is_at", "cur"]],
        eq(rd("m", "decide_armed"), lit(1.0)),
        [["set_attr", "m", "chosen_action",
          term(attr(argmax(nodesof("Action"), "act", decision_value()), "code"))],
         ["set_attr", "m", "decide_armed", 0.0]],
    )],
)

# ----------------------------------------------------- bigville_affect_spiral
def _outcome(name, code, effects):
    guard = band(eq(rd("m", "outcome_armed"), lit(1.0)),
                 eq(rd("m", "chosen_action"), lit(float(code))))
    eff = list(effects) + [["set_attr", "m", "outcome_armed", 0.0]]
    return rule(name, [["m", "is_at", "cur"]], guard, eff)


SPIRAL = seed(
    "bigville_affect_spiral",
    "BIGVILLE R17 (block 265000) -- the negative spiral, REACHABLE + ENDOGENOUS. "
    "The four outcome rules apply each chosen action's material consequence "
    "(work -> income up + slight relief; withdraw -> income down; drink -> income "
    "down + wellbeing down; snap -> income down + wellbeing down + conflict up -> "
    "R15 violence), and af_hardship_grief closes the loop: coin below a floor "
    "raises grief_distress. grief -> worse decision -> worse outcome -> more grief "
    "(the R3 collapse-spiral at the affective level). It FALLS OUT of the coupling "
    "-- nothing scripts it; ablate affect_gain -> work every period -> no spiral. "
    "NO reward/punishment token (income/wellbeing are STATES). Composes existing "
    "Terms only; ZERO new Rust.",
    [
        _outcome("af_outcome_work", 1, [
            ["set_attr", "m", "coin", term(plus(rd("m", "coin"), lit(5.0)))],
            ["set_attr", "m", "grief_distress",
             term(tmax(lit(0.0), minus(rd("m", "grief_distress"), lit(1.0))))],
        ]),
        _outcome("af_outcome_withdraw", 2, [
            ["set_attr", "m", "coin", term(minus(rd("m", "coin"), lit(2.0)))],
            ["set_attr", "m", "missed_work",
             term(plus(rd("m", "missed_work"), lit(1.0)))],
        ]),
        _outcome("af_outcome_drink", 3, [
            ["set_attr", "m", "coin", term(minus(rd("m", "coin"), lit(3.0)))],
            ["set_attr", "m", "wellbeing",
             term(minus(rd("m", "wellbeing"), lit(4.0)))],
            ["set_attr", "m", "drank", term(plus(rd("m", "drank"), lit(1.0)))],
        ]),
        _outcome("af_outcome_snap", 4, [
            ["set_attr", "m", "coin", term(minus(rd("m", "coin"), lit(1.0)))],
            ["set_attr", "m", "wellbeing",
             term(minus(rd("m", "wellbeing"), lit(2.0)))],
            ["set_attr", "m", "conflict",
             term(plus(rd("m", "conflict"), lit(1.0)))],
        ]),
        rule(
            "af_hardship_grief",
            [["m", "is_at", "cur"]],
            band(eq(rd("m", "feedback_armed"), lit(1.0)),
                 lt(rd("m", "coin"), lit(1.0))),
            [["set_attr", "m", "grief_distress",
              term(plus(rd("m", "grief_distress"), lit(2.0)))],
             ["set_attr", "m", "feedback_armed", 0.0]],
        ),
    ],
)

# ------------------------------------------------------ bigville_affect_coreg
COREG = seed(
    "bigville_affect_coreg",
    "BIGVILLE R17 (block 265000) -- af_regulation_from_coreg: regulation is READ "
    "from the REUSED 239000 window the person holds -- regulation = clamp01(k * "
    "(widen_count - narrow_count)). Co-regulation (a regulated caregiver, run "
    "through the UNCHANGED 239000 stress-episode rules via R14 attend/rear_episode) "
    "WIDENS the window -> regulation rises -> eff_distress falls -> the regulated "
    "choice (work) becomes REACHABLE again -> recovery. No support -> the window "
    "narrows -> regulation stays 0 -> the spiral runs to breakdown. Breakdown vs "
    "recovery is a MEASURED function of support presence -- 'does well if it can', "
    "not a will to fail. This IS the RESTORE arm of the induce->measure->RESTORE "
    "ethics protocol (co-regulation, not a reset). Composes existing Terms only; "
    "ZERO new Rust.",
    [rule(
        "af_regulation_from_coreg",
        [["m", "has_window", "wot"]],
        eq(rd("m", "regul_armed"), lit(1.0)),
        [["set_attr", "m", "regulation",
          term(clamp01(times(lit(0.15),
                             minus(rd("wot", "widen_count"),
                                   rd("wot", "narrow_count")))))],
         ["set_attr", "m", "regul_armed", 0.0]],
    )],
)

# -------------------------------------------------- bigville_affect_propagate
PROPAGATE = seed(
    "bigville_affect_propagate",
    "BIGVILLE R17 (block 265000) -- af_grief_narrows_caregiving: a grief-narrowed "
    "PARENT who caregives a child cannot provide co-regulation -- the rule clears "
    "that caregiver's `regulated` flag -> the reused 239000 mark_coreg_support no "
    "longer sets got_coreg -> each of the child's stress episodes resolves down the "
    "239000 NARROW path -> the child's window NARROWS -> the child's adult priors "
    "shift DOWN via R14 bl_come_of_age. The failure mode crosses a GENERATION (ties "
    "R14 rearing + the three foundational priors). gen_gain=0 decouples grief from "
    "caregiving -> the caregiver stays regulated -> no cross-generation transfer. "
    "NO reward/punishment token. Composes existing Terms only; ZERO new Rust.",
    [rule(
        "af_grief_narrows_caregiving",
        [["parent", "caregives", "cg"]],
        band(eq(rd("parent", "gen_gain"), lit(1.0)),
             gt(rd("parent", "grief_distress"), lit(2.0))),
        [["set_attr", "cg", "regulated", 0.0]],
    )],
)


def main():
    seeds = [GRIEF, DECIDE, SPIRAL, COREG, PROPAGATE]
    for s in seeds:
        path = os.path.join(SEED_DIR, s["id"] + ".json")
        with open(path, "w") as f:
            json.dump(s, f, indent=1)
            f.write("\n")
        print("wrote", os.path.relpath(path, ROOT),
              "(%d rules)" % len(s["rules"]))


if __name__ == "__main__":
    main()
