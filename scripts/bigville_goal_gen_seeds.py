#!/usr/bin/env python3
"""bigville R8 (block 256000) SEED BUILDER -- emits the LIFE-GOAL + DREAM seeds
(the identity / soul layer).

This is a TOOL (a seed BUILDER that emits graph data, explicitly allowed by
experiments/gamma-substrate/CLAUDE.md -- the same class as
`bigville_fin_gen_seeds.py`). It writes two self-contained seed manifests the
Rust runtime loads. NO agent decision lives here -- every soul-layer DECISION
(orient sub-goal choice / ungrounded-boundary audit / dream-invoked affect
relief / dream collapse into a leave-goal / latent resignation) is a RULE in the
emitted JSON; this file only assembles Term-trees.

ZERO new Rust. Everything composes EXISTING DSL Terms:

  * G-life-goal-orients -- the sub-goal SELECTION is the substrate's
    `decision_value` Argmax (the SAME Argmax family as bigville R2 nd_choose_good
    and the drama's ss_choose_burn): the chosen sub-option is the Argmax over the
    soul's REACHABLE `considers` options of
        base_appeal(opt) + Sum_{lg in has_life_goal} [ opt.serves_aim==lg.aim ?
                                                        lg.orient_weight : 0 ]
    A "become wealthy" life-goal (aim=wealth, high orient_weight) tips a
    lower-base-appeal SAVE option above a higher-base-appeal LEISURE option.
    ABLATE the life-goal (drop the has_life_goal edge) -> the Sum is empty -> the
    base appeal decides -> LEISURE wins -> no long-horizon bias (load-bearing).

  * G-dream-is-ungrounded -- the DREAM is held on the UNGROUNDED side of the
    grounding boundary: it carries NO `grounded_path` edge in the map-belief,
    UNLIKE a LIFE-GOAL (which carries a `path_to` -- a real, if long, path). The
    audit is a rule reading edge presence/absence, never Python.

  * G-dream-regulates-affect (HEADLINE) -- when the present turns aversive
    (valence driven below `aversive_threshold` via R7 foreclosure/homeless
    distress), invoking the dream gives TEMPORARY RELIEF (valence UP by
    relief_valence, arousal DOWN by relief_arousal) WITHOUT touching any material
    attr (coin / balance / homeless UNCHANGED) -- the escape valve, cousin of
    intellectualisation's residual-quarantine. ABLATE the dream -> the identical
    aversive state has NO relief valve.

  * G-dream-collapses -- push valence past `collapse_threshold` (the present
    unbearable) OR a recruiter mints a `grounded_path` (a real path appears) ->
    the dream COLLAPSES into an actionable Goal (add_node ActionGoal{kind:leave})
    and the soul ACTS (left=1). CONTROL: below threshold + no path -> the dream
    stays LATENT (latent=1, resigned=1, left=0) -- resignation / the
    learned-helplessness floor (the abuse line).

  seeds/bigville_goal_life.json    -- gg_lifegoal_grounded, gg_orient_choice.
  seeds/bigville_goal_dream.json   -- gg_dream_ungrounded, gg_dream_relief,
        gg_dream_collapse_threshold, gg_dream_collapse_path, gg_dream_latent.
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
    """Read attr as a number with default 0 (the `Plus[Attr, 0]` idiom the
    R4/R6/R7 seeds use so a missing key never aborts a match)."""
    return {"type": "Plus", "items": [
        {"type": "Attr", "node": var(node), "key": key}, lit(0)]}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def mx(*items):
    return {"type": "Max", "items": list(items)}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def lte(a, b):
    return {"type": "Lte", "a": a, "b": b}


def a_and(*items):
    return {"type": "And", "items": list(items)}


def a_not(arg):
    return {"type": "Not", "arg": arg}


def neighbours(node, edge):
    return {"type": "Neighbours", "node": var(node), "edge_type": edge,
            "any_type": False}


def exists(node, edge):
    """Exists an out-neighbour of `node` along `edge` (map-belief path presence)."""
    return {"type": "Exists", "source": neighbours(node, edge),
            "var_name": "_p", "predicate": {"type": "Lit", "value": True}}


def ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def term(t):
    return {"__term__": t}


# ---- the decision_value Argmax (G-life-goal-orients) -------------------------
# chosen sub-option = Argmax over the soul's `considers` options of
#   base_appeal(opt) + Sum_{lg in has_life_goal} [serves_aim==aim ? orient_weight : 0]
# The life-goal term is empty under ablation (no has_life_goal edge) -> base
# appeal alone decides. Identical Argmax family to R2 nd_choose_good.
def decision_value():
    bias = {"type": "Sum",
            "source": neighbours("m", "has_life_goal"),
            "var_name": "lg",
            "value": ite(eq(attr("opt", "serves_aim"), attr("lg", "aim")),
                         attr("lg", "orient_weight"), lit(0.0))}
    return plus(attr("opt", "base_appeal"), bias)


def orient_argmax():
    return {"type": "Argmax",
            "source": neighbours("m", "considers"),
            "var_name": "opt",
            "value": decision_value()}


# ============================================================ THE LIFE-GOAL
def build_life():
    rules = []

    # --- gg_lifegoal_grounded: a LIFE-GOAL is GROUNDED -- it carries a real
    #     `path_to` in the map-belief (the grounded side of the boundary),
    #     unlike a dream. One-shot via the grounded_flag==0 done-guard (no
    #     disarm, so it never races the dream audit on the shared audit_armed).
    rules.append({
        "name": "gg_lifegoal_grounded",
        "match": [["m", "has_life_goal", "lg"], ["lg", "path_to", "dest"]],
        "where": a_and(
            eq(attr("m", "audit_armed"), lit(1.0)),
            eq(attr("lg", "grounded_flag"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "lg", "grounded_flag", 1.0],
        ],
    })

    # --- gg_orient_choice: the sub-goal SELECTION Argmax, biased by the
    #     life-goal (save > leisure for a become-wealthy soul; ablate -> leisure).
    rules.append({
        "name": "gg_orient_choice",
        "match": [["m", "weighs", "cp"]],
        "where": eq(attr("m", "orient_armed"), lit(1.0)),
        "effects": [
            ["set_attr", "m", "chosen_subgoal",
             term({"type": "Attr", "node": orient_argmax(), "key": "code"})],
            ["set_attr", "m", "orient_armed", 0.0],
        ],
    })

    return {
        "id": "bigville_goal_life",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R8 (block 256000) -- the LIFE-GOAL layer (identity / soul). "
            "gg_lifegoal_grounded affirms a life-goal is GROUNDED (carries a real "
            "`path_to` in the map-belief -- the grounded side of the boundary), "
            "one-shot via a grounded_flag done-guard. gg_orient_choice is "
            "G-life-goal-orients: the sub-goal SELECTION is the substrate's "
            "decision_value Argmax (the SAME family as R2 nd_choose_good / the "
            "drama's ss_choose_burn) over the soul's `considers` options of "
            "base_appeal + Sum_{has_life_goal}[serves_aim==aim ? orient_weight : "
            "0]. A become-wealthy life-goal (high orient_weight on the SAVE aim) "
            "tips a lower-base-appeal SAVE above a higher-base-appeal LEISURE; "
            "ABLATE the life-goal (drop the has_life_goal edge) -> the Sum is "
            "empty -> base appeal decides -> LEISURE wins -> no long-horizon bias "
            "(load-bearing). Composes existing Terms; zero new Rust."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


# ============================================================ THE DREAM
def build_dream():
    rules = []

    # --- gg_dream_ungrounded: the DREAM is on the UNGROUNDED side -- NO
    #     `grounded_path` edge in the map-belief (unlike a life-goal's path_to).
    #     One-shot via the ungrounded==0 done-guard (no disarm; shares audit_armed
    #     safely with gg_lifegoal_grounded).
    rules.append({
        "name": "gg_dream_ungrounded",
        "match": [["m", "has_dream", "dr"]],
        "where": a_and(
            eq(attr("m", "audit_armed"), lit(1.0)),
            eq(attr("dr", "ungrounded"), lit(0.0)),
            a_not(exists("dr", "grounded_path")),
        ),
        "effects": [
            ["set_attr", "dr", "ungrounded", 1.0],
        ],
    })

    # --- gg_dream_relief (HEADLINE): aversive present -> invoke the dream ->
    #     TEMPORARY RELIEF (valence up, arousal down) WITHOUT touching any
    #     material attr. relief_armed one-shot; guarded on not-collapsed and
    #     valence < aversive_threshold. Arousal floored at 0 via Max.
    rules.append({
        "name": "gg_dream_relief",
        "match": [["m", "has_dream", "dr"], ["m", "has_affective_state", "aff"]],
        "where": a_and(
            eq(attr("m", "relief_armed"), lit(1.0)),
            eq(attr("dr", "collapsed"), lit(0.0)),
            lt(attr("aff", "valence"), attr("dr", "aversive_threshold")),
        ),
        "effects": [
            ["set_attr", "aff", "valence",
             term(plus(attr("aff", "valence"), attr("dr", "relief_valence")))],
            ["set_attr", "aff", "arousal",
             term(mx(lit(0.0),
                     minus(attr("aff", "arousal"), attr("dr", "relief_arousal"))))],
            ["set_attr", "dr", "invoked",
             term(plus(attr("dr", "invoked"), lit(1.0)))],
            ["set_attr", "m", "relief_armed", 0.0],
        ],
    })

    # --- gg_dream_collapse_threshold: present UNBEARABLE (valence <=
    #     collapse_threshold) AND no grounded path -> COLLAPSE into a leave-goal;
    #     the soul ACTS (left=1). Disjoint from the path collapse (Not path).
    rules.append({
        "name": "gg_dream_collapse_threshold",
        "match": [["m", "has_dream", "dr"], ["m", "has_affective_state", "aff"]],
        "where": a_and(
            eq(attr("m", "collapse_armed"), lit(1.0)),
            eq(attr("dr", "collapsed"), lit(0.0)),
            lte(attr("aff", "valence"), attr("dr", "collapse_threshold")),
            a_not(exists("dr", "grounded_path")),
        ),
        "effects": [
            ["set_attr", "dr", "collapsed", 1.0],
            ["set_attr", "dr", "latent", 0.0],
            ["add_node", "g", "ActionGoal", {"kind": "leave", "trigger": 1.0}],
            ["add_edge", "m", "has_goal", "g"],
            ["set_attr", "m", "left", 1.0],
            ["set_attr", "m", "collapse_armed", 0.0],
        ],
    })

    # --- gg_dream_collapse_path: a recruiter minted a `grounded_path` (a real
    #     path from here appears) -> COLLAPSE into a leave-goal regardless of
    #     valence; the soul ACTS (left=1). trigger=2 (path).
    rules.append({
        "name": "gg_dream_collapse_path",
        "match": [["m", "has_dream", "dr"]],
        "where": a_and(
            eq(attr("m", "collapse_armed"), lit(1.0)),
            eq(attr("dr", "collapsed"), lit(0.0)),
            exists("dr", "grounded_path"),
        ),
        "effects": [
            ["set_attr", "dr", "collapsed", 1.0],
            ["set_attr", "dr", "latent", 0.0],
            ["add_node", "g", "ActionGoal", {"kind": "leave", "trigger": 2.0}],
            ["add_edge", "m", "has_goal", "g"],
            ["set_attr", "m", "left", 1.0],
            ["set_attr", "m", "collapse_armed", 0.0],
        ],
    })

    # --- gg_dream_latent: below threshold + no path -> the dream stays LATENT
    #     (held, NOT acted) -- resignation / the learned-helplessness floor.
    #     Disjoint from both collapses (valence > threshold AND no path).
    rules.append({
        "name": "gg_dream_latent",
        "match": [["m", "has_dream", "dr"], ["m", "has_affective_state", "aff"]],
        "where": a_and(
            eq(attr("m", "collapse_armed"), lit(1.0)),
            eq(attr("dr", "collapsed"), lit(0.0)),
            gt(attr("aff", "valence"), attr("dr", "collapse_threshold")),
            a_not(exists("dr", "grounded_path")),
        ),
        "effects": [
            ["set_attr", "dr", "latent", 1.0],
            ["set_attr", "m", "resigned", 1.0],
            ["set_attr", "m", "collapse_armed", 0.0],
        ],
    })

    return {
        "id": "bigville_goal_dream",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R8 (block 256000) -- the DREAM layer (the ungrounded escape "
            "fantasy that makes a soul more than a utility function). "
            "gg_dream_ungrounded audits the dream onto the UNGROUNDED side of the "
            "grounding boundary (NO grounded_path edge, unlike a life-goal's "
            "path_to). gg_dream_relief (HEADLINE) is AFFECT REGULATION: when the "
            "present turns aversive (valence < aversive_threshold, driven there by "
            "R7 foreclosure/homeless distress) invoking the dream gives TEMPORARY "
            "relief (valence up by relief_valence, arousal down by relief_arousal, "
            "arousal floored at 0) WITHOUT touching any material attr (coin / "
            "balance / homeless UNCHANGED) -- the escape valve; ABLATE the dream "
            "(no has_dream edge) -> the identical aversive state has NO relief. "
            "gg_dream_collapse_threshold (valence <= collapse_threshold, present "
            "unbearable) and gg_dream_collapse_path (a recruiter minted a "
            "grounded_path -- a real path appears) COLLAPSE the dream into an "
            "actionable ActionGoal{kind:leave} (add_node) and the soul ACTS "
            "(left=1). gg_dream_latent is the CONTROL: below threshold + no path "
            "-> the dream stays LATENT (latent=1, resigned=1, left=0) -- "
            "resignation / the learned-helplessness floor (the abuse line). The "
            "three collapse/latent rules are DISJOINT (threshold: valence<=thr & "
            "no path; path: path present; latent: valence>thr & no path) so "
            "exactly one fires per collapse arm. Composes existing Terms; zero new "
            "Rust."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


def main():
    os.makedirs(SEEDS, exist_ok=True)
    for seed in (build_life(), build_dream()):
        path = os.path.join(SEEDS, seed["id"] + ".json")
        with open(path, "w") as f:
            json.dump(seed, f, indent=1)
        print("wrote", path, "--", len(seed["rules"]), "rules")


if __name__ == "__main__":
    main()
