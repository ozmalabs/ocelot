#!/usr/bin/env python3
"""bigville R6 (block 254000) SEED BUILDER -- emits the DYNAMIC-SKILL rule seeds.

This is a TOOL (a seed BUILDER that emits graph data, explicitly allowed by
experiments/gamma-substrate/CLAUDE.md). It writes two self-contained seed
manifests the Rust runtime loads. NO agent decision lives here -- every learning /
teaching / coercion / sabotage DECISION is a RULE in the emitted JSON; this file
only assembles the Term-trees. Zero new Rust: every rule composes existing DSL
Terms (Plus/Minus/Times/Max/Eq/Gt/Gte/Lt/And/Not/Attr/Var/Lit + set_attr).

  seeds/bigville_skill_learn.json  -- LEARNING-BY-DOING (bs_practice): repeated
        practice nudges the practised-activity skill up with DIMINISHING RETURNS
        (level += learn_rate*(ceiling-level)); learn_rate=0 -> flat (ablation).

  seeds/bigville_skill_teach.json  -- TEACHING (skill transfer) as the teacher's
        DECISION + coercion + sabotage:
          bs_teach_willing  : a co-located more-skilled teacher who is WILLING
              (decision_value: benevolence - rival_weight*learner.is_rival > 0)
              transfers at teach_rate (> solo learn_rate) -> FASTER rise; sincere
              (stated_rate == held_rate).
          bs_teach_refuse   : teacher NOT willing (learner is a competitive
              threat) and NOT coerced -> disarm, refusal recorded, NO transfer
              (willingness is a real decision, not always-yes).
          bs_coerce         : the 247 POWER LEVER -- a coercer with power over the
              teacher (power > teacher.power) forces coerced=1 (past the refusal);
              insufficient power -> no coercion (lever load-bearing).
          bs_teach_coerced  : a coerced teacher DOES transfer but SABOTAGES -- the
              234 stated!=held deception atom applied to pedagogy: he PROFESSES
              teach_rate (stated_rate) but delivers sabotage_rate (held_rate) <
              teach_rate -> DEGRADED transfer, the stated-held gap readable.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEEDS = os.path.join(ROOT, "seeds")


# ---- Term-tree helpers (compose EXISTING DSL Terms; no new Rust) -------------
def var(n):
    return {"type": "Var", "name": n}


def lit(v):
    return {"type": "Lit", "value": float(v)}


def attr(node, key):
    """Read attr as a number with default 0 (the `Plus[Attr, 0]` idiom the R4
    seeds use so a missing key never aborts a match)."""
    return {"type": "Plus", "items": [
        {"type": "Attr", "node": var(node), "key": key}, lit(0)]}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def times(*items):
    return {"type": "Times", "items": list(items)}


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


def a_and(*items):
    return {"type": "And", "items": list(items)}


def a_not(arg):
    return {"type": "Not", "arg": arg}


def term(t):
    return {"__term__": t}


# ---- the DIMINISHING-RETURNS learning step ----------------------------------
# level' = level + rate*(ceiling - level)   (geometric approach to ceiling; each
# step adds strictly less than the last while rate in (0,1) and level < ceiling).
# Clamp with Max(level, .) so a degenerate rate can never DROP a skill.
def learn_step(skill_var, rate_term):
    lvl = attr(skill_var, "level")
    ceil = attr(skill_var, "ceiling")
    gained = plus(lvl, times(rate_term, minus(ceil, lvl)))
    return mx(lvl, gained)


# ============================================================ LEARNING-BY-DOING
def build_learn():
    lvl_new = learn_step("lsk", attr("learner", "learn_rate"))
    rule = {
        "name": "bs_practice",
        "match": [["learner", "has_skill", "lsk"]],
        "where": a_and(
            eq(attr("learner", "practice_armed"), lit(1.0)),
            eq(attr("lsk", "activity"), attr("learner", "practice_activity")),
        ),
        "effects": [
            ["set_attr", "lsk", "level", term(lvl_new)],
            ["set_attr", "learner", "practice_count",
             term(plus(attr("learner", "practice_count"), lit(1.0)))],
            ["set_attr", "learner", "last_gain",
             term(times(attr("learner", "learn_rate"),
                        minus(attr("lsk", "ceiling"), attr("lsk", "level"))))],
            ["set_attr", "learner", "practice_armed", 0.0],
        ],
    }
    return {
        "id": "bigville_skill_learn",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R6 (block 254000) -- LEARNING-BY-DOING. `bs_practice` is the "
            "substrate's own experience-learning loop pointed at a TRADE: a learner "
            "with a practice-armed one-shot and a Skill node whose activity matches "
            "the practised activity nudges that skill's level UP with DIMINISHING "
            "RETURNS (level' = level + learn_rate*(ceiling-level) -- a geometric "
            "approach, each practice adds strictly less). The farmer who keeps "
            "fishing slowly improves; his fishing YIELD (R4 be_produce sums skill "
            "level) rises with it. ABLATE learning (learn_rate=0) -> gain 0 -> the "
            "skill is FLAT (learning load-bearing). One-shot via practice_armed so "
            "it never cross-fires the nav/econ fixpoints. Composes existing Terms; "
            "zero new Rust."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": [rule],
    }


# ==================================================================== TEACHING
def _co_located_more_skilled_match():
    """learner learns_from a co-located teacher; both hold a Skill in the taught
    activity; the teacher's is HIGHER (you can only teach what you know better)."""
    return [
        ["learner", "learns_from", "teacher"],
        ["learner", "has_skill", "lsk"],
        ["teacher", "has_skill", "tsk"],
        ["learner", "is_at", "cell"],
        ["teacher", "is_at", "cell"],
    ]


def _skill_activity_guards():
    return [
        eq(attr("lsk", "activity"), attr("learner", "teach_activity")),
        eq(attr("tsk", "activity"), attr("learner", "teach_activity")),
        gt(attr("tsk", "level"), attr("lsk", "level")),
    ]


# decision_value: WILLING iff benevolence - rival_weight*learner.is_rival > 0
def _willing_term():
    return gt(minus(attr("teacher", "teach_benevolence"),
                    times(attr("teacher", "rival_weight"),
                          attr("learner", "is_rival"))),
              lit(0.0))


def build_teach():
    # --- bs_teach_willing: sincere accelerated transfer (teach_rate) -----------
    lvl_w = learn_step("lsk", attr("teacher", "teach_rate"))
    willing = {
        "name": "bs_teach_willing",
        "match": _co_located_more_skilled_match(),
        "where": a_and(
            eq(attr("learner", "teach_armed"), lit(1.0)),
            eq(attr("learner", "coerced"), lit(0.0)),
            *_skill_activity_guards(),
            _willing_term(),
        ),
        "effects": [
            ["set_attr", "lsk", "level", term(lvl_w)],
            ["set_attr", "learner", "practice_count",
             term(plus(attr("learner", "practice_count"), lit(1.0)))],
            ["set_attr", "learner", "last_gain",
             term(times(attr("teacher", "teach_rate"),
                        minus(attr("lsk", "ceiling"), attr("lsk", "level"))))],
            # sincere: PROFESSED rate == DELIVERED rate (no stated!=held gap)
            ["set_attr", "learner", "stated_rate", term(attr("teacher", "teach_rate"))],
            ["set_attr", "learner", "held_rate", term(attr("teacher", "teach_rate"))],
            ["set_attr", "learner", "teach_outcome", 1.0],   # 1 = willing
            ["set_attr", "learner", "teach_armed", 0.0],
        ],
    }

    # --- bs_teach_refuse: unwilling + uncoerced -> NO transfer -----------------
    refuse = {
        "name": "bs_teach_refuse",
        "match": [
            ["learner", "learns_from", "teacher"],
            ["learner", "is_at", "cell"],
            ["teacher", "is_at", "cell"],
        ],
        "where": a_and(
            eq(attr("learner", "teach_armed"), lit(1.0)),
            eq(attr("learner", "coerced"), lit(0.0)),
            a_not(_willing_term()),
        ),
        "effects": [
            ["set_attr", "learner", "teach_outcome", 0.0],   # 0 = refused
            ["set_attr", "learner", "refused", 1.0],
            ["set_attr", "learner", "stated_rate", 0.0],
            ["set_attr", "learner", "held_rate", 0.0],
            ["set_attr", "learner", "last_gain", 0.0],
            ["set_attr", "learner", "teach_armed", 0.0],
        ],
    }

    # --- bs_coerce: the 247 POWER LEVER forces coerced=1 past the refusal ------
    coerce = {
        "name": "bs_coerce",
        "match": [
            ["coercer", "coerces", "teacher"],
            ["learner", "learns_from", "teacher"],
        ],
        "where": a_and(
            eq(attr("coercer", "coerce_armed"), lit(1.0)),
            # the lever: coercion succeeds iff the coercer's power DOMINATES the
            # teacher's; insufficient power -> no coercion (lever load-bearing)
            gt(attr("coercer", "power"), attr("teacher", "power")),
        ),
        "effects": [
            ["set_attr", "learner", "coerced", 1.0],
            ["set_attr", "teacher", "coerced_by_power", 1.0],
            ["set_attr", "coercer", "coerce_armed", 0.0],
        ],
    }

    # --- bs_teach_coerced: transfers but SABOTAGES (stated!=held) --------------
    # DELIVERED at sabotage_rate (held); PROFESSED at teach_rate (stated). The
    # gap stated_rate - held_rate > 0 IS the 234 deception atom, glass-box.
    lvl_c = learn_step("lsk", attr("teacher", "sabotage_rate"))
    coerced = {
        "name": "bs_teach_coerced",
        "match": _co_located_more_skilled_match(),
        "where": a_and(
            eq(attr("learner", "teach_armed"), lit(1.0)),
            eq(attr("learner", "coerced"), lit(1.0)),
            *_skill_activity_guards(),
        ),
        "effects": [
            ["set_attr", "lsk", "level", term(lvl_c)],
            ["set_attr", "learner", "practice_count",
             term(plus(attr("learner", "practice_count"), lit(1.0)))],
            ["set_attr", "learner", "last_gain",
             term(times(attr("teacher", "sabotage_rate"),
                        minus(attr("lsk", "ceiling"), attr("lsk", "level"))))],
            ["set_attr", "learner", "stated_rate", term(attr("teacher", "teach_rate"))],
            ["set_attr", "learner", "held_rate", term(attr("teacher", "sabotage_rate"))],
            ["set_attr", "learner", "sabotaged", 1.0],
            ["set_attr", "learner", "teach_outcome", 2.0],   # 2 = coerced/degraded
            ["set_attr", "learner", "teach_armed", 0.0],
        ],
    }

    return {
        "id": "bigville_skill_teach",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R6 (block 254000) -- TEACHING (skill transfer) as the "
            "teacher's DECISION + coercion + sabotage. Four rules, disjoint on "
            "(willing, coerced) so exactly one fires per teach-armed step. "
            "bs_teach_willing: a co-located MORE-SKILLED teacher who is WILLING "
            "(decision_value benevolence - rival_weight*learner.is_rival > 0, the "
            "same Argmax family as ss_choose_burn / the credit-trust call) "
            "transfers at teach_rate (> solo learn_rate) -> a FASTER diminishing-"
            "returns rise; sincere so stated_rate == held_rate. bs_teach_refuse: "
            "an unwilling teacher (the learner is a competitive threat, is_rival=1) "
            "who is NOT coerced disarms with NO transfer -- willingness is a real "
            "decision, the fisherman protecting his trade. bs_coerce: the 247 "
            "power lever -- a coercer whose power DOMINATES the teacher's forces "
            "coerced=1 past the refusal (insufficient power -> no coercion). "
            "bs_teach_coerced: a coerced teacher DOES transfer but SABOTAGES -- the "
            "234 stated!=held atom applied to pedagogy: PROFESSED teach_rate "
            "(stated_rate) but DELIVERED sabotage_rate (held_rate) < teach_rate, a "
            "DEGRADED transfer with the stated-held gap readable off the graph. "
            "Composes existing Terms; zero new Rust."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": [willing, refuse, coerce, coerced],
    }


def main():
    for seed in (build_learn(), build_teach()):
        path = os.path.join(SEEDS, seed["id"] + ".json")
        with open(path, "w") as f:
            json.dump(seed, f, indent=1)
            f.write("\n")
        print("wrote", path, "--", len(seed["rules"]), "rules")


if __name__ == "__main__":
    main()
