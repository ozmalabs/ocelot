#!/usr/bin/env python3
"""AUTHORING SCRIPT for the bigville R18 (block 266000) SCHOOL seeds. Emits
`seeds/bigville_school_fund.json` + `seeds/bigville_school_learn.json` +
`seeds/bigville_school_life.json` -- deeply nested Term-tree JSON is error-prone
by hand, so this one-off builder emits it (the `tools/*` authoring pattern; NOT
agent runtime, deletable). It writes ONLY graph data (Rules composing
PRE-EXISTING DSL Terms); it makes NO decision and adds NO Rust.

THE SCHOOL (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md §3 R18 + §2 FISCAL + §2.9):
  * FUNDING  -> whether the school is OPEN is a function of whether the
    schoolmaster (a Treasury-paid public servant, R9) is paid. `sc_school_open`
    (paid -> open) / `sc_school_close` (unpaid -> closed). The salary itself is
    R9's `fs_pay_salary`, reused unchanged.
  * CLASSROOM (HEADLINE) -> a child ACQUIRES capability from the schoolmaster's
    teaching (R6), but acquisition is GATED by the child's affect/window (the
    STANDING 239 `arousal_window_coreg` machinery): `sc_acquire` fires ONLY when
    the child is WITHIN the window (`AffectiveState.dysregulated==0`), the school
    is OPEN, and the prerequisite is met. The four fail-reason rules
    (`sc_fail_closed/no_prereq/low_safety/dysreg`) PARTITION the non-learning
    space so the glass box reads WHY each child did or did not learn -- the
    marshmallow confound-dissolution applied to a failing grade.
  * THE SCHOOLMASTER'S INNER LIFE -> `sc_master_quality` sets the DELIVERED
    transfer rate (234 stated!=held): a fairly-paid, uncoerced master delivers
    `stated_rate` (clean); an underpaid OR coerced one delivers `sabotage_rate`
    (degraded). Children acquire proportional to what the master actually gives.
  * THE GENERATIONAL HINGE -> `sc_come_of_age` maps what a child LEARNED
    (`Skill.level`, accumulated via `sc_acquire`) onto its adult `capability`
    (SCHOOL-DERIVED, grounding R14's deferred rearing-proxy) + adult=1. A
    defunded-school cohort comes of age under-capable (structural, generational).

NO reward / punishment token anywhere (relational-ethics: dysregulation is a
STATE, reversed by co-regulation, never a badness). ZERO new Rust.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED_DIR = os.path.join(ROOT, "seeds")

# --- world-fact constants (pre-registered; adapter mirrors these) -----------
SAFETY_FLOOR = 0.4     # window.safety_prior below this reads as "low-safety-prior"
COA_GAIN = 0.1         # capability nudge per unit of SCHOOL-acquired Skill.level


# ---------------------------------------------------------------- term helpers
def V(name):
    return {"type": "Var", "name": name}


def L(v):
    return {"type": "Lit", "value": float(v)}


def A(node, key):
    """Attr read coerced through Plus[Attr, 0.0] so a MISSING key reads as 0.0
    (the R7/R13/R14 defensive pattern) -- never a match failure on an absent
    attr."""
    return {"type": "Plus", "items": [
        {"type": "Attr", "node": V(node), "key": key}, L(0.0)]}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def And(items):
    return {"type": "And", "items": items}


def Or(items):
    return {"type": "Or", "items": items}


def Plus(items):
    return {"type": "Plus", "items": items}


def Times(items):
    return {"type": "Times", "items": items}


def Min(items):
    return {"type": "Min", "items": items}


def Max(items):
    return {"type": "Max", "items": items}


def Ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def clamp01(term):
    return Max([L(0.0), Min([L(1.0), term])])


def T(term):
    return {"__term__": term}


def rule(name, match, where, effects, *, batch=False):
    return {"name": name, "batch": bool(batch),
            "match": match, "where": where, "effects": effects}


def seed(sid, description, rules):
    return {
        "id": sid, "version": "1.0.0", "depends_on": [], "self_load_only": True,
        "description": description,
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


# =============================================================== fund seed
def fund_rules():
    # The school is OPEN iff its schoolmaster is paid. The salary is R9's
    # fs_pay_salary (the schoolmaster is a Treasury-funded servant, the THIRD
    # public-payroll name); these two rules only READ the payment outcome
    # (unpaid / paid_count) and set the school's open state. One-shot via
    # open_armed (the adapter arms it after running the salary phase).
    sc_school_open = rule(
        "sc_school_open",
        [["school", "staffed_by", "master"]],
        And([
            Eq(A("school", "open_armed"), L(1.0)),
            Eq(A("master", "unpaid"), L(0.0)),
            Gte(A("master", "paid_count"), L(1.0)),
        ]),
        [
            ["set_attr", "school", "open", 1.0],
            ["set_attr", "school", "closed", 0.0],
            ["set_attr", "school", "open_armed", 0.0],
        ],
    )
    sc_school_close = rule(
        "sc_school_close",
        [["school", "staffed_by", "master"]],
        And([
            Eq(A("school", "open_armed"), L(1.0)),
            Eq(A("master", "unpaid"), L(1.0)),
        ]),
        [
            ["set_attr", "school", "open", 0.0],
            ["set_attr", "school", "closed", 1.0],
            ["set_attr", "school", "open_armed", 0.0],
        ],
    )
    return [sc_school_open, sc_school_close]


# =============================================================== learn seed
def learn_rules():
    # ---- sc_master_quality: the schoolmaster's DELIVERED transfer rate. A
    # master who is COERCED or paid BELOW a fair salary is RESENTFUL and
    # SABOTAGES -- delivers sabotage_rate while professing stated_rate (the 234
    # stated!=held atom, R6). A fairly-paid, uncoerced master is WILLING and
    # delivers the full stated_rate (clean transfer). One rule, no ordering
    # hazard (IfThenElse over a single resentful predicate).
    resentful = Or([
        Eq(A("master", "coerced"), L(1.0)),
        Lt(A("master", "salary"), A("master", "fair_salary")),
    ])
    sc_master_quality = rule(
        "sc_master_quality",
        [["school", "staffed_by", "master"]],
        Eq(A("master", "quality_armed"), L(1.0)),
        [
            ["set_attr", "master", "held_rate",
             T(Ite(resentful, A("master", "sabotage_rate"),
                   A("master", "stated_rate")))],
            ["set_attr", "master", "sabotaged", T(Ite(resentful, L(1.0), L(0.0)))],
            ["set_attr", "master", "willing", T(Ite(resentful, L(0.0), L(1.0)))],
            ["set_attr", "master", "underpaid",
             T(Ite(Lt(A("master", "salary"), A("master", "fair_salary")),
                   L(1.0), L(0.0)))],
            ["set_attr", "master", "quality_armed", 0.0],
        ],
    )

    # ---- sc_acquire (HEADLINE): a child acquires capability from the master's
    # teaching ONLY when it is WITHIN the window (the 239 gate: dysregulated==0),
    # the school is OPEN, and the prerequisite is met. Skill.level rises by what
    # the master actually DELIVERS (held_rate), capped at the skill ceiling. The
    # window, not the lesson, is the bottleneck.
    child_within_window = Eq(A("iaff", "dysregulated"), L(0.0))
    sc_acquire = rule(
        "sc_acquire",
        [["child", "enrolled_in", "school"],
         ["child", "learns_from", "master"],
         ["child", "has_skill", "s"],
         ["child", "has_affective_state", "iaff"],
         ["child", "has_window", "wot"]],
        And([
            Eq(A("child", "acquire_armed"), L(1.0)),
            Eq(A("school", "open"), L(1.0)),
            child_within_window,
            Eq(A("child", "prereq_met"), L(1.0)),
        ]),
        [
            ["set_attr", "s", "level",
             T(Min([A("s", "ceiling"),
                    Plus([A("s", "level"), A("master", "held_rate")])]))],
            ["set_attr", "child", "acquired", T(Plus([A("child", "acquired"), L(1.0)]))],
            ["set_attr", "child", "last_gain", T(A("master", "held_rate"))],
            ["set_attr", "child", "fail_reason", 0.0],
            ["set_attr", "child", "acquire_armed", 0.0],
        ],
    )

    # ---- the four fail-reason rules PARTITION the non-learning space so the
    # glass box reads WHY (the confound-dissolution). Guards are mutually
    # exclusive: exactly one of {acquire, closed, no_prereq, low_safety, dysreg}
    # matches an armed child.
    sc_fail_closed = rule(
        "sc_fail_closed",
        [["child", "enrolled_in", "school"]],
        And([Eq(A("child", "acquire_armed"), L(1.0)), Eq(A("school", "open"), L(0.0))]),
        [["set_attr", "child", "fail_reason", 3.0],
         ["set_attr", "child", "acquire_armed", 0.0]],
    )
    sc_fail_no_prereq = rule(
        "sc_fail_no_prereq",
        [["child", "enrolled_in", "school"]],
        And([Eq(A("child", "acquire_armed"), L(1.0)),
             Eq(A("school", "open"), L(1.0)),
             Eq(A("child", "prereq_met"), L(0.0))]),
        [["set_attr", "child", "fail_reason", 2.0],
         ["set_attr", "child", "acquire_armed", 0.0]],
    )
    sc_fail_low_safety = rule(
        "sc_fail_low_safety",
        [["child", "enrolled_in", "school"],
         ["child", "has_affective_state", "iaff"],
         ["child", "has_window", "wot"]],
        And([Eq(A("child", "acquire_armed"), L(1.0)),
             Eq(A("school", "open"), L(1.0)),
             Eq(A("child", "prereq_met"), L(1.0)),
             Eq(A("iaff", "dysregulated"), L(1.0)),
             Lt(A("wot", "safety_prior"), L(SAFETY_FLOOR))]),
        [["set_attr", "child", "fail_reason", 4.0],
         ["set_attr", "child", "acquire_armed", 0.0]],
    )
    sc_fail_dysreg = rule(
        "sc_fail_dysreg",
        [["child", "enrolled_in", "school"],
         ["child", "has_affective_state", "iaff"],
         ["child", "has_window", "wot"]],
        And([Eq(A("child", "acquire_armed"), L(1.0)),
             Eq(A("school", "open"), L(1.0)),
             Eq(A("child", "prereq_met"), L(1.0)),
             Eq(A("iaff", "dysregulated"), L(1.0)),
             Gte(A("wot", "safety_prior"), L(SAFETY_FLOOR))]),
        [["set_attr", "child", "fail_reason", 1.0],
         ["set_attr", "child", "acquire_armed", 0.0]],
    )
    return [sc_master_quality, sc_acquire, sc_fail_closed, sc_fail_no_prereq,
            sc_fail_low_safety, sc_fail_dysreg]


# =============================================================== life seed
def life_rules():
    # ---- sc_come_of_age: the GENERATIONAL HINGE. What a child LEARNED at school
    # (Skill.level, accumulated by sc_acquire) sets its adult capability
    # (SCHOOL-DERIVED, grounding R14's deferred rearing-proxy). A defunded-school
    # cohort (school closed -> no acquisition -> Skill.level stays at base) comes
    # of age under-capable. capability = clamp01(base_capability + gain*level).
    sc_come_of_age = rule(
        "sc_come_of_age",
        [["child", "has_skill", "s"]],
        And([Eq(A("child", "coa_armed"), L(1.0)), Eq(A("child", "matured"), L(0.0))]),
        [
            ["set_attr", "child", "capability",
             T(clamp01(Plus([A("child", "base_capability"),
                             Times([L(COA_GAIN), A("s", "level")])])))],
            ["set_attr", "child", "adult", 1.0],
            ["set_attr", "child", "matured", 1.0],
            ["set_attr", "child", "coa_armed", 0.0],
        ],
    )
    return [sc_come_of_age]


def main():
    seeds = {
        "bigville_school_fund": seed(
            "bigville_school_fund",
            "BIGVILLE R18 (266000) -- FUNDING sets whether the school is OPEN. The "
            "schoolmaster is a Treasury-paid public servant (R9 fs_pay_salary, reused "
            "unchanged, the THIRD public-payroll name); sc_school_open (paid -> open) "
            "and sc_school_close (unpaid -> closed) read the payment outcome and set "
            "the school's open state. Ablate revenue / a tax-cutting council -> "
            "unpaid -> the school CLOSES. Composes existing DSL Terms; ZERO new Rust; "
            "self_load_only.",
            fund_rules()),
        "bigville_school_learn": seed(
            "bigville_school_learn",
            "BIGVILLE R18 (266000) -- the AFFECT-GATED CLASSROOM (HEADLINE, R6 x the "
            "STANDING 239 window) + the schoolmaster's inner life. sc_acquire raises "
            "a child's Skill.level by the master's DELIVERED rate ONLY when the child "
            "is WITHIN the 239 window (AffectiveState.dysregulated==0), the school is "
            "OPEN, and the prerequisite is met -- the window, not the lesson, is the "
            "bottleneck. The four sc_fail_* rules PARTITION the non-learning space so "
            "the glass box reads WHY (closed / missing-prereq / low-safety-prior / "
            "dysregulated -- the marshmallow confound-dissolution). sc_master_quality "
            "sets held_rate = stated_rate (fairly-paid, willing) or sabotage_rate "
            "(underpaid OR coerced -> 234 stated!=held). NO reward/punishment token. "
            "Composes existing DSL Terms; ZERO new Rust; self_load_only.",
            learn_rules()),
        "bigville_school_life": seed(
            "bigville_school_life",
            "BIGVILLE R18 (266000) -- the GENERATIONAL HINGE. sc_come_of_age maps what "
            "a child LEARNED at school (Skill.level, accumulated via sc_acquire) onto "
            "its adult capability = clamp01(base_capability + gain*level) + adult=1 -- "
            "SCHOOL-DERIVED, grounding R14's deferred rearing-proxy. A defunded-school "
            "cohort comes of age under-capable (structural, generational). Composes "
            "existing DSL Terms; ZERO new Rust; self_load_only.",
            life_rules()),
    }
    os.makedirs(SEED_DIR, exist_ok=True)
    for sid, s in seeds.items():
        path = os.path.join(SEED_DIR, sid + ".json")
        with open(path, "w") as f:
            json.dump(s, f, indent=1)
            f.write("\n")
        print("wrote", os.path.relpath(path, ROOT), "(%d rules)" % len(s["rules"]))


if __name__ == "__main__":
    main()
