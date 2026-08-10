"""Generator for seeds/repair_escalation.json — FULL ladder integration (extension c, complete).

A failed self-repair now climbs the agent's EXISTING order-2..6 impasse_escalation ladder instead of a
standalone retry/latch. The jabberwock's design:

  FEED: a reverted repair leaves the axis non-improving, so the existing measure loop bumps mf_stall; at
        mf_stall>=4 `repair_escalate_open` mints an order-2 escalation Impasse for the repair-kind axis
        (the generic escalate_open can't — it requires investigated_by/taught_about a repair axis lacks),
        wiring the SAME surprised_by/about_axis edges so the GENERIC escalation_climb (2->6) and
        escalation_resolve (saturation>=0.95) drive it verbatim.
  RUNGS (repair specialisation, keyed on the escalation Impasse + a repair_kind axis; fire on
        order==N & acted_order<N — NO mf_stall requirement — so they take priority over the climb, which
        needs mf_stall>=4; each resets mf_stall so the climb only advances on fresh non-improvement):
        2 change-method  -> re-arm a DIFFERENT synthesised clause (bump attempt; reuse clause_synthesis)
        3 reframe        -> decompose: flip the field (effect<->where) + needs_decomposition, re-arm
        4 author-tool    -> honest need_template marker (no stored template covers it)
        5 re-prioritise  -> set aside: keep the shadow's last-good live, fault_open=0, shortfall *= 0.1
        6 rethink-self   -> mint an honest HumanImpasse, mark terminal

Termination: forward motion only on a rung fire, order strictly increases to 6, so the old
detect->repair->revert infinite loop cannot form. Pure graph data; no Rust; the generic ladder is untouched.

Run: python3 scripts/gen_repair_escalation_seed.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def V(n): return {"type": "Var", "name": n}
def Lit(v): return {"type": "Lit", "value": v}
def Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def P0(var, k): return {"type": "Plus", "items": [Attr(V(var), k), Lit(0.0)]}
def And(items): return {"type": "And", "items": items}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Plus(items): return {"type": "Plus", "items": items}
def Times(items): return {"type": "Times", "items": items}
def IfThenElse(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}


def REPAIR_AX():
    return Gte(P0("ax", "repair_kind"), Lit(0.5))


def rung_match():
    return [["mi", "about_axis", "ax"], ["ax", "has_fault", "f"]]


def rung_where(order):
    # keyed on a SEPARATE `repair_acted` marker (not the ladder's acted_order) so the generic rungs can't
    # pre-empt the repair rungs; and on order==N with no mf_stall requirement so the rung fires before the
    # climb (which needs mf_stall>=4) can advance past this order.
    return And([
        REPAIR_AX(),
        Eq(P0("mi", "order"), Lit(float(order))),
        Lt(P0("mi", "repair_acted"), Lit(float(order))),
    ])


def opener():
    return {
        "name": "repair_escalate_open",
        "comment": "Open an order-2 escalation Impasse for a repair-kind axis that keeps failing "
                   "(mf_stall>=4, not already escalating). The generic escalate_open can't fire here (a "
                   "repair axis has no investigated_by/taught_about), so this mirrors its edges "
                   "(surprised_by + about_axis) and resets mf_stall, letting the GENERIC escalation_climb / "
                   "escalation_resolve drive the 2->6 climb verbatim.",
        "match": [["ag", "operates_in", "w"], ["ax", "has_fault", "f"]],
        "where": And([REPAIR_AX(), Gte(P0("ax", "mf_stall"), Lit(4)), Lt(P0("ax", "escalating"), Lit(0.5))]),
        "effects": [
            ["add_node", "mi", "Impasse", {"resolved": False, "kind": "escalation", "order": 2,
                                           "acted_order": 1, "repair_acted": 1, "repair_imp": 1.0,
                                           "note": "self-repair stalled — escalate the approach"}],
            ["add_edge", "ag", "surprised_by", "mi"],
            ["add_edge", "mi", "about_axis", "ax"],
            ["set_attr", "ax", "escalating", 1.0],
            ["set_attr", "ax", "mf_stall", 0.0],
        ],
    }


def order2():
    return {
        "name": "repair_rung_order2_change_method",
        "comment": "ORDER 2 (change-method, repair form): re-arm a DIFFERENT synthesised clause — bump "
                   "f.attempt, awaiting_synth=1, applied=0, gated=0 so clause_synthesis builds a new clause and "
                   "repair_apply re-installs it. Fires on order==2 & acted_order<2 (no mf_stall req -> priority "
                   "over the climb); sets acted_order=2 and resets mf_stall.",
        "match": rung_match(),
        "where": rung_where(2),
        "effects": [
            ["set_attr", "f", "attempt", {"__term__": Plus([P0("f", "attempt"), Lit(1.0)])}],
            ["set_attr", "f", "awaiting_synth", 1.0],
            ["set_attr", "f", "applied", 0.0],
            ["set_attr", "f", "gated", 0.0],
            ["set_attr", "f", "outcome", "retrying"],
            ["set_attr", "mi", "repair_acted", 2],
            ["set_attr", "ax", "mf_stall", 0.0],
        ],
    }


def order3():
    return {
        "name": "repair_rung_order3_reframe",
        "comment": "ORDER 3 (reframe, repair form): decompose — flip the field the repair targets "
                   "(effect<->where) and mark needs_decomposition, then re-arm synthesis. Fires on order==3 & "
                   "acted_order<3.",
        "match": rung_match(),
        "where": rung_where(3),
        "effects": [
            ["set_attr", "f", "field",
                {"__term__": IfThenElse(Eq(Attr(V("f"), "field"), Lit("effect")), Lit("where"), Lit("effect"))}],
            ["set_attr", "f", "needs_decomposition", 1.0],
            ["set_attr", "f", "awaiting_synth", 1.0],
            ["set_attr", "f", "applied", 0.0],
            ["set_attr", "f", "gated", 0.0],
            ["set_attr", "f", "outcome", "reframing"],
            ["set_attr", "mi", "repair_acted", 3],
            ["set_attr", "ax", "mf_stall", 0.0],
        ],
    }


def order4():
    return {
        "name": "repair_rung_order4_author_tool",
        "comment": "ORDER 4 (author-tool, repair form): no synthesised clause worked — honestly mark "
                   "need_template (no held ClauseTemplate covers this fault); climb continues. Fires on "
                   "order==4 & acted_order<4.",
        "match": rung_match(),
        "where": rung_where(4),
        "effects": [
            ["set_attr", "f", "need_template", 1.0],
            ["set_attr", "mi", "repair_acted", 4],
            ["set_attr", "ax", "mf_stall", 0.0],
        ],
    }


def order5():
    return {
        "name": "repair_rung_order5_reprioritise",
        "comment": "ORDER 5 (re-prioritise, repair form): set the repair aside — the shadow already holds the "
                   "last-good live clause, so clear fault_open, mark repair_aside, and shrink shortfall so the "
                   "axis stops dominating without a false resolve. Fires on order==5 & acted_order<5.",
        "match": rung_match(),
        "where": rung_where(5),
        "effects": [
            ["set_attr", "ax", "repair_aside", 1.0],
            ["set_attr", "ax", "fault_open", 0.0],
            ["set_attr", "ax", "shortfall", {"__term__": Times([P0("ax", "shortfall"), Lit(0.1)])}],
            ["set_attr", "mi", "repair_acted", 5],
            ["set_attr", "ax", "mf_stall", 0.0],
        ],
    }


def order6():
    return {
        "name": "repair_rung_order6_human",
        "comment": "ORDER 6 (rethink-self, repair form): the whole approach failed — mint an honest "
                   "HumanImpasse (the world adapter surfaces it) and mark the fault terminal. The honest "
                   "terminal of the repair search; never a silent latch. Fires on order>=6 & acted_order<6.",
        "match": rung_match(),
        "where": And([REPAIR_AX(), Gte(P0("mi", "order"), Lit(6)), Lt(P0("f", "terminal"), Lit(0.5))]),
        "effects": [
            ["add_node", "hi", "HumanImpasse", {
                "kind": "repair_exhausted", "needs_human": 1.0, "resolved": False,
                "target_rule": {"__term__": Attr(V("f"), "target_rule")},
                "question": "I climbed the whole repair ladder (retry, reframe, author, set-aside) and nothing "
                            "lifted the measure — what should I be given or read to fix this rule?"}],
            ["add_edge", "f", "impasse", "hi"],
            ["set_attr", "f", "outcome", "human"],
            ["set_attr", "f", "terminal", 1.0],
        ],
    }


def main():
    seed = {
        "id": "repair_escalation",
        "version": "2.0.0",
        "depends_on": ["self_repair", "impasse_escalation", "clause_synthesis"],
        "description": "FULL ladder integration of self-repair escalation: a failed repair climbs the agent's "
                       "existing order-2..6 impasse_escalation ladder (repair_escalate_open feeds it; the "
                       "generic climb/resolve drive it), with repair-kind rung adapters specialising each "
                       "order (retry / reframe / author / set-aside / HumanImpasse). Pure graph data; the "
                       "generic ladder is untouched. Generated by scripts/gen_repair_escalation_seed.py.",
        "microtheory": {"name": "repair_escalation",
                        "description": "a failed repair climbs the order-2..6 ladder: retry->reframe->author->set-aside->HumanImpasse"},
        "nodes": [], "edges": [],
        "productions": [
            {"provenance": "seed:repair_escalation:impasse",
             "src": {"type": "Fault", "var": "x"}, "edge_type": "impasse",
             "tgt": {"type": "HumanImpasse", "var": "y"}, "where": None, "weight": {"type": "Lit", "value": 1.0}},
        ],
        "rules": [opener(), order2(), order3(), order4(), order5(), order6()],
    }
    out = os.path.join(ROOT, "seeds", "repair_escalation.json")
    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(seed, fh, indent=1)
    json.load(open(tmp))
    os.replace(tmp, out)
    print(f"wrote + validated {os.path.relpath(out, ROOT)} ({len(seed['rules'])} rules)")


if __name__ == "__main__":
    main()
