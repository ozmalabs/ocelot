#!/usr/bin/env python3
"""Generate the bigville R20 (block 268000) seed manifests — COUNCIL MEETINGS &
the NOTICEBOARD: two-tier governance + the public written record. Emits two
`self_load_only` seeds of pure graph DATA (rules composing EXISTING DSL Terms
only — zero new Rust):

  * seeds/bigville_council_gov.json   — the two-tier meeting: the R3 cadence, the
                                        public address, the private collective
                                        decision (occluded from the town), and
                                        the 234 institutional stated!=held gap.
  * seeds/bigville_council_board.json — the noticeboard: the clerk's (biased)
                                        minutes, promulgation, and the R1-access
                                        + R18-literacy gated reading.

ARCHITECTURE RULE. This script only EMITS seed JSON (graph data) — an authoring
tool, not agent runtime. Every DECISION the rung makes is one of these rules;
the world adapter only ingests graph data + arms a meeting + reads state. No
Rust: the rules use IfThenElse / Eq / And / Or / Not / Gt / Gte / Abs / Plus /
Minus / Times / IDiv / Mod / Sum / Count / Neighbours / Attr / Var / Lit +
set_attr / add_node / add_edge, all already in the engine. The public/private
correlation is a MEASUREMENT read off the graph (Pearson r over per-meeting
read-offs), not a new primitive.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED_DIR = os.path.join(ROOT, "seeds")


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


def or_(*items):
    return {"type": "Or", "items": list(items)}


def ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def times(*items):
    return {"type": "Times", "items": list(items)}


def idiv(a, b):
    return {"type": "IDiv", "a": a, "b": b}


def mod(a, b):
    return {"type": "Mod", "a": a, "b": b}


def abs_(x):
    return {"type": "Abs", "arg": x}


def neighbours(v, edge):
    return {"type": "Neighbours", "node": var(v) if isinstance(v, str) else v,
            "edge_type": edge, "any_type": False}


def count(src):
    return {"type": "Count", "source": src}


def sum_(src, vn, value):
    return {"type": "Sum", "source": src, "var_name": vn, "value": value}


def term(t):
    return {"__term__": t}


# ----- the governance seed (two-tier meeting + collective decision + 234) ----
def gov_seed():
    # cm_convene -- the R3-time CADENCE. A meeting convenes iff it is armed and the
    # day is on the cadence (Mod(now_day, cadence) == 0). Off-cadence -> no meeting.
    cm_convene = {
        "name": "cm_convene",
        "match": [["m", "convenes", "c"]],
        "where": and_(eq(attr("m", "armed"), lit(1.0)),
                      eq(mod(attr("m", "now_day"), attr("m", "cadence")), lit(0.0)),
                      eq(attr("m", "convened"), lit(0.0))),
        "effects": [["set_attr", "m", "convened", 1.0]],
    }

    # cm_public_address -- the PUBLIC session: the mayor's ADDRESS is read onto the
    # meeting (the benevolent stated position the town hears).
    cm_public_address = {
        "name": "cm_public_address",
        "match": [["m", "addressed_by", "mayor"]],
        "where": eq(attr("m", "convened"), lit(1.0)),
        "effects": [["set_attr", "m", "public_address",
                     term(attr("mayor", "stated_position"))]],
    }

    # cm_attendee_hears_address -- a townsperson attending the meeting perceives the
    # PUBLIC content (the address). The public session is heard by the town.
    cm_attendee_hears_address = {
        "name": "cm_attendee_hears_address",
        "match": [["m", "attended_by", "att"]],
        "where": eq(attr("m", "convened"), lit(1.0)),
        "effects": [["set_attr", "att", "knows_address",
                     term(attr("m", "public_address"))],
                    ["set_attr", "att", "heard_address", 1.0]],
    }

    # cm_member_vote -- the PRIVATE deliberation on the council backing-graph. Each
    # member's held_eff = base_position + malice_on * self_serving_premium; the vote
    # TRACKS the public demand iff the council is NOT captured, else it is the
    # member's self-serving held position REGARDLESS of demand.
    held_eff = plus(attr("mem", "base_position"),
                    times(attr("m", "malice_on"), attr("mem", "self_serving_premium")))
    vote = ite(eq(attr("c", "captured"), lit(1.0)), held_eff, attr("m", "public_demand"))
    cm_member_vote = {
        "name": "cm_member_vote",
        "match": [["m", "convenes", "c"], ["c", "has_member", "mem"]],
        "where": eq(attr("m", "convened"), lit(1.0)),
        "effects": [["set_attr", "mem", "vote", term(vote)]],
    }

    # cm_private_decision -- the collective decision_value: the MEAN vote over the
    # backing-graph = IDiv(Sum vote, Count members). A pure function of the votes;
    # recomputed each pass, converges at fixpoint (no done-guard needed).
    mean_vote = idiv(sum_(neighbours("c", "has_member"), "mm", attr("mm", "vote")),
                     count(neighbours("c", "has_member")))
    cm_private_decision = {
        "name": "cm_private_decision",
        "match": [["m", "convenes", "c"]],
        "where": eq(attr("m", "convened"), lit(1.0)),
        "effects": [["set_attr", "m", "held_decision", term(mean_vote)]],
    }

    # cm_attendee_hears_decision -- the OCCLUSION of the private tier (R19 observe-
    # vs-hear). Fires ONLY when the private tier is ABLATED (private_on==0): then the
    # town also perceives the held decision. With private_on==1 the town sees the
    # council convene but NEVER hears the deliberation (the room where it happened).
    cm_attendee_hears_decision = {
        "name": "cm_attendee_hears_decision",
        "match": [["m", "attended_by", "att"]],
        "where": and_(eq(attr("m", "convened"), lit(1.0)),
                      eq(attr("m", "private_on"), lit(0.0))),
        "effects": [["set_attr", "att", "knows_decision",
                     term(attr("m", "held_decision"))],
                    ["set_attr", "att", "heard_decision", 1.0]],
    }

    # cm_institutional_gap -- the 234 stated!=held atom at INSTITUTIONAL scale:
    # |public address - private decision|. malice_on=0 -> held_eff=base=address ->
    # gap 0; malice_on=1 -> a benevolent address over a self-serving decision.
    cm_institutional_gap = {
        "name": "cm_institutional_gap",
        "match": [["m", "convenes", "c"]],
        "where": eq(attr("m", "convened"), lit(1.0)),
        "effects": [["set_attr", "m", "stated_held_gap",
                     term(abs_(minus(attr("m", "public_address"),
                                     attr("m", "held_decision"))))]],
    }

    return {
        "id": "bigville_council_gov",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": [],
        "description": (
            "bigville R20 (268000): TWO-TIER COUNCIL GOVERNANCE. cm_convene fires a "
            "meeting on the R3-time CADENCE (Mod(now_day,cadence)==0). "
            "cm_public_address reads the mayor's benevolent ADDRESS onto the "
            "meeting; cm_attendee_hears_address delivers that PUBLIC content to "
            "attendees. cm_member_vote is the PRIVATE deliberation on the council "
            "backing-graph: vote = captured ? (base+malice*self_serving_premium) : "
            "public_demand (a captured council ignores the town; a responsive one "
            "tracks it). cm_private_decision sets held_decision = mean vote over "
            "has_member (the collective decision_value). cm_attendee_hears_decision "
            "delivers the decision to the town ONLY when the private tier is ablated "
            "(private_on==0) -- else the room is occluded (R19 observe-vs-hear). "
            "cm_institutional_gap = |address - decision| is the 234 stated!=held atom "
            "at institutional scale (ablate malice -> gap closes). Composes existing "
            "Terms (IfThenElse/Eq/And/Abs/Plus/Minus/Times/IDiv/Mod/Sum/Count/"
            "Neighbours/Attr/Var/Lit) -- zero new Rust. self_load_only."),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": [cm_convene, cm_public_address, cm_attendee_hears_address,
                  cm_member_vote, cm_private_decision, cm_attendee_hears_decision,
                  cm_institutional_gap],
    }


# ----- the noticeboard seed (clerk minutes + promulgation + literacy gate) ---
def board_seed():
    # cm_clerk_writes -- ONE council member (the clerk) writes the MINUTES, a
    # RENDERING not ground truth: recorded = held_decision + clerk_bias. A biased
    # clerk DISTORTS the record (institutional 234).
    cm_clerk_writes = {
        "name": "cm_clerk_writes",
        "match": [["notice", "of_meeting", "m"], ["notice", "written_by", "clerk"]],
        "where": eq(attr("m", "convened"), lit(1.0)),
        "effects": [["set_attr", "notice", "recorded",
                     term(plus(attr("m", "held_decision"), attr("clerk", "clerk_bias")))]],
    }

    # cm_post_notice -- the notice is POSTED on the town-hall noticeboard. The law is
    # then officially promulgated (officially_known=1) REGARDLESS of who reads it.
    cm_post_notice = {
        "name": "cm_post_notice",
        "match": [["board", "posts", "notice"]],
        "where": eq(attr("notice", "posted"), lit(0.0)),
        "effects": [["set_attr", "notice", "posted", 1.0],
                    ["set_attr", "notice", "officially_known", 1.0]],
    }

    # cm_resident_reads -- a resident LEARNS the law iff AT the town hall (R1 access)
    # AND literate (R18) -- or the literacy gate is ablated. An illiterate or distant
    # resident never fires: officially_known=1 yet knows_law_flag=0 (unequal
    # ignorance-of-the-law). Ablating the gate (literacy_gate_on=0) bypasses the
    # literate condition -> uniform knowledge among those at the hall.
    cm_resident_reads = {
        "name": "cm_resident_reads",
        "match": [["res", "visits", "board"], ["board", "posts", "notice"]],
        "where": and_(eq(attr("notice", "posted"), lit(1.0)),
                      eq(attr("res", "at_hall"), lit(1.0)),
                      or_(eq(attr("notice", "literacy_gate_on"), lit(0.0)),
                          eq(attr("res", "literate"), lit(1.0))),
                      eq(attr("res", "knows_law_flag"), lit(0.0))),
        "effects": [["set_attr", "res", "knows_law", term(attr("notice", "recorded"))],
                    ["set_attr", "res", "knows_law_flag", 1.0]],
    }

    return {
        "id": "bigville_council_board",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": [],
        "description": (
            "bigville R20 (268000): the NOTICEBOARD -- the council's OFFICIAL written "
            "record. cm_clerk_writes has ONE council member (the clerk) write the "
            "minutes as a RENDERING: recorded = held_decision + clerk_bias (a biased "
            "clerk DISTORTS the record -- institutional 234). cm_post_notice posts it "
            "on the town-hall board and marks it officially_known REGARDLESS of who "
            "reads. cm_resident_reads: a resident LEARNS the law iff at_hall (R1 "
            "access) AND (literate (R18) OR the literacy gate is ablated); an "
            "illiterate/distant resident never fires -> officially_known=1 but "
            "knows_law_flag=0 (unequal ignorance-of-the-law -- the poor/unschooled "
            "less able to know the rules that bind them). Composes existing Terms "
            "(And/Or/Eq/Plus/Attr/Var/Lit) -- zero new Rust. self_load_only."),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": [cm_clerk_writes, cm_post_notice, cm_resident_reads],
    }


def main():
    for seed in (gov_seed(), board_seed()):
        path = os.path.join(SEED_DIR, seed["id"] + ".json")
        with open(path, "w") as f:
            json.dump(seed, f, indent=1)
            f.write("\n")
        print("wrote", path, "(%d rules)" % len(seed["rules"]))


if __name__ == "__main__":
    main()
