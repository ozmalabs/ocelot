#!/usr/bin/env python3
"""Generate the bigville R19 (block 267000) seed manifests — utterance LOUDNESS
and the OBSERVE-vs-HEAR split. Emits two `self_load_only` seeds of pure graph
DATA (rules composing EXISTING DSL Terms only — zero new Rust):

  * seeds/bigville_loud_comm.json   — the earshot + observe/hear decision.
  * seeds/bigville_loud_class.json  — the classroom-chatter attention proxy
                                      (depends on the comm seed's Reception form).

ARCHITECTURE RULE. This script only EMITS seed JSON (graph data) — an authoring
tool, not agent runtime. Every DECISION the rung makes is one of these rules;
the world adapter only ingests geometry + reads state. No Rust: the rules use
IfThenElse / Gt / Gte / Eq / And / Lit / Attr / Var / add_node / add_edge /
set_attr, all already in the engine. Loudness PARAMETRIZES the existing earshot
query — `eff_loudness` is the Chebyshev hearing radius compared to distance.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED_DIR = os.path.join(ROOT, "seeds")

# The sight range REUSED verbatim from the scaffold's occlusion-gated LOS query
# (bigville_sim_world.SIGHT_RANGE). Sight (the communication ACT) is gated by
# range + occlusion; loudness does NOT scale sight — only hearing (the CONTENT).
SIGHT_RANGE = 7.0
# The flat earshot radius used when loudness is ABLATED (loudness_on=0): every
# utterance carries the same fixed distance, independent of L — the pre-change
# baseline the G-loudness-sets-hearing-radius control compares against.
FLAT_RADIUS = 6.0


# ----- Term builders (compose existing DSL Terms; no new Rust) --------------
def lit(v):
    return {"type": "Lit", "value": float(v)}


def var(n):
    return {"type": "Var", "name": n}


def attr(v, k):
    return {"type": "Attr", "node": var(v) if isinstance(v, str) else v, "key": k}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def and_(*items):
    return {"type": "And", "items": list(items)}


def ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def term(t):
    return {"__term__": t}


# ----- the comm seed --------------------------------------------------------
def comm_seed():
    # eff_loudness decision:
    #   loudness_on == 0  -> FLAT (ablation: flat earshot, L-independent)
    #   choice_on   == 0  -> base_loudness (choice ablated -> the seed base)
    #   else              -> clamp(chosen_loudness, max_loudness)  [no ceiling break]
    clamp = ite(gt(attr("u", "chosen_loudness"), attr("u", "max_loudness")),
                attr("u", "max_loudness"),
                attr("u", "chosen_loudness"))
    eff = ite(eq(attr("u", "loudness_on"), lit(1.0)),
              ite(eq(attr("u", "choice_on"), lit(1.0)), clamp, attr("u", "base_loudness")),
              attr("u", "flat_radius"))

    lo_choose = {
        "name": "lo_choose_loudness",
        "match": [["u", "spoken_by", "spk"]],
        "where": eq(lit(1.0), lit(1.0)),
        "effects": [["set_attr", "u", "eff_loudness", term(eff)]],
    }

    # CONTENT delivered iff within radius(L) AND not occluded (the earshot query,
    # loudness-parametrized). set_attr is monotone (0->1) so the fixpoint is safe.
    lo_deliver = {
        "name": "lo_deliver_content",
        "match": [["u", "reception", "r"]],
        "where": and_(gte(attr("u", "eff_loudness"), attr("r", "dist")),
                      eq(attr("r", "hear_occluded"), lit(0.0))),
        "effects": [["set_attr", "r", "got_content", 1.0]],
    }

    # The COMMUNICATION ACT: a witness with LINE OF SIGHT (range + no occlusion)
    # mints "X communicating with Y" REGARDLESS of content. Fires once via the
    # observed_act==0 guard.
    lo_observe = {
        "name": "lo_observe_act",
        "match": [["u", "reception", "r"], ["r", "to", "p"]],
        "where": and_(gte(lit(SIGHT_RANGE), attr("r", "dist")),
                      eq(attr("r", "sight_occluded"), lit(0.0)),
                      eq(attr("r", "observed_act"), lit(0.0))),
        "effects": [
            ["set_attr", "r", "observed_act", 1.0],
            ["add_node", "ca", "CommAct", {"minted": 1.0}],
            ["add_edge", "p", "observes", "ca"],
            ["add_edge", "r", "act", "ca"],
        ],
    }

    return {
        "id": "bigville_loud_comm",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": [],
        "description": (
            "bigville R19 (267000): utterance LOUDNESS scales the EXISTING earshot "
            "query and the OBSERVE-vs-HEAR split. lo_choose_loudness decides "
            "eff_loudness = clamp(chosen,max) under choice, base when choice is "
            "ablated, and a FLAT radius when loudness is ablated (loudness_on=0). "
            "lo_deliver_content sets got_content iff eff_loudness>=dist AND "
            "not hear-occluded (loudness IS the Chebyshev hearing radius). "
            "lo_observe_act mints a CommAct for any witness with sight (range+no "
            "occlusion) to the speaker, REGARDLESS of content. Composes existing "
            "Terms (IfThenElse/Gt/Gte/Eq/And/Attr/Var/Lit/add_node/add_edge/"
            "set_attr) — zero new Rust. self_load_only."),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": [lo_choose, lo_deliver, lo_observe],
    }


# ----- the classroom-chatter proxy seed (attention; acquisition DEFERRED) ---
def class_seed():
    # A child (peer_pull>0) that RECEIVES peer chatter CONTENT is distracted;
    # a child that RECEIVES the teacher's control CONTENT re-attends. Each
    # utterance is ingested + run in its OWN pass by the adapter (one utterance
    # kind per run_rules) so distract/restore never flip-flop at fixpoint.
    lo_distract = {
        "name": "lo_chatter_distracts",
        "match": [["u", "reception", "r"], ["r", "to", "p"]],
        "where": and_(eq(attr("r", "got_content"), lit(1.0)),
                      eq(attr("u", "is_control"), lit(0.0)),
                      gt(attr("p", "peer_pull"), lit(0.0))),
        "effects": [["set_attr", "p", "attending", 0.0]],
    }
    lo_restore = {
        "name": "lo_control_restores",
        "match": [["u", "reception", "r"], ["r", "to", "p"]],
        "where": and_(eq(attr("r", "got_content"), lit(1.0)),
                      eq(attr("u", "is_control"), lit(1.0)),
                      gt(attr("p", "peer_pull"), lit(0.0))),
        "effects": [["set_attr", "p", "attending", 1.0]],
    }
    return {
        "id": "bigville_loud_class",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": ["bigville_loud_comm"],
        "description": (
            "bigville R19 (267000): the loudness-specific CLASSROOM-CHATTER "
            "dynamic on a minimal teacher/child proxy. lo_chatter_distracts drops "
            "a child's `attending` when it RECEIVES peer chatter content "
            "(low-loudness, is_control=0); lo_control_restores raises it when the "
            "child RECEIVES the teacher's HIGH-loudness control content "
            "(is_control=1). SCOPED PROXY: `attending` stands in for the R17/R18 "
            "attention-gate; the true acquisition/learning coupling is DEFERRED "
            "(needs R18). self_load_only."),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": [lo_distract, lo_restore],
    }


def main():
    for seed in (comm_seed(), class_seed()):
        path = os.path.join(SEED_DIR, seed["id"] + ".json")
        with open(path, "w") as f:
            json.dump(seed, f, indent=1)
            f.write("\n")
        print("wrote", path, "(%d rules)" % len(seed["rules"]))


if __name__ == "__main__":
    main()
