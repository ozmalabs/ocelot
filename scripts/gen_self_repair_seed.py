"""Generator for seeds/self_repair.json — the jabberwock's INTRINSIC SELF-REPAIR faculty (its design).

Emits graph DATA (a one-off authoring tool). Four struct rules + one production realise the three polish
items the agent designed, all graph-native, composing from held machinery (the investigation_loop measure/
bank, the set_rule_clause effect, the effect-gate idea):

  1. fault_detect_regression  — AUTONOMOUS trigger. When a banked measure drops a repairable axis below its
     own banked baseline (saturation < sat_best - margin) and no fault is open, MINT a Fault graph-natively:
     it carries the axis's target rule / field / corrected clause (the axis's deliberated graph data) and
     from_sat (the pre-regression baseline). Latches fault_open so it fires once. (item 1, + item 2 in its
     template-copy form: the corrected clause is the axis's authored repair_clause.)
  2. repair_apply_rule_clause — snapshot the currently-installed clause off the axis SHADOW (ax.live_clause)
     into f.original, rewrite the named rule via set_rule_clause(corrected), then update the shadow. (item 3
     snapshot: the graph is the system of record, so the old clause is read from the shadow, never the engine.)
  3. gate_keep / gate_revert  — EFFECT-GATE. On a fresh POST-REPAIR measure, if the axis recovered
     (saturation > from_sat - margin) KEEP (clear the latch); else REVERT via set_rule_clause(f.original) and
     restore the shadow. (item 3 keep-or-revert.)

Run: python3 scripts/gen_self_repair_seed.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARGIN = 0.05


def V(n): return {"type": "Var", "name": n}
def Lit(v): return {"type": "Lit", "value": v}
def Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def P0(var, k): return {"type": "Plus", "items": [Attr(V(var), k), Lit(0.0)]}   # None-safe numeric read
def AC(var, k): return {"__term__": Attr(V(var), k)}                            # copy an attr value (clause)
def And(items): return {"type": "And", "items": items}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}


def fault_detect():
    return {
        "name": "fault_detect_regression",
        "comment": "AUTONOMOUS trigger: a freshly-banked measure (m banked ax) drops a repairable axis below "
                   "its own banked baseline -> mint a Fault carrying the axis's target rule/field/corrected "
                   "clause + the pre-regression baseline, link it, and latch fault_open so it fires once.",
        "match": [["m", "banked", "ax"]],
        "where": And([
            Lt(P0("ax", "saturation"), Minus(P0("ax", "sat_best"), Lit(MARGIN))),
            Lt(P0("ax", "fault_open"), Lit(0.5)),
            Gt(P0("ax", "repairable"), Lit(0.5)),
        ]),
        "effects": [
            ["add_node", "f", "Fault", {
                "target_rule": AC("ax", "repair_rule"),
                "field": AC("ax", "repair_field"),
                "corrected": AC("ax", "repair_clause"),
                "from_sat": AC("ax", "sat_best"),
                "applied": 0.0, "gated": 0.0}],
            ["add_edge", "ax", "has_fault", "f"],
            ["set_attr", "ax", "fault_open", 1.0],
        ],
    }


def repair_apply():
    return {
        "name": "repair_apply_rule_clause",
        "comment": "Snapshot the installed clause off the axis SHADOW (ax.live_clause -> f.original), rewrite "
                   "the named rule via set_rule_clause(corrected), update the shadow. The shadow makes the "
                   "graph the system of record, so the old clause for revert is read here, never from the engine. "
                   "Waits while awaiting_synth>0.5 (a synth fault whose clause clause_synthesis is still "
                   "building); default 0 so template-copy/ingested faults fire immediately (back-compat).",
        "match": [["ax", "has_fault", "f"]],
        "where": And([Lt(P0("f", "applied"), Lit(0.5)), Lt(P0("f", "awaiting_synth"), Lit(0.5))]),
        "effects": [
            ["set_attr", "f", "original", AC("ax", "live_clause")],
            ["set_rule_clause", AC("f", "target_rule"), AC("f", "field"), AC("f", "corrected")],
            ["set_attr", "ax", "live_clause", AC("f", "corrected")],
            ["set_attr", "f", "applied", 1.0],
        ],
    }


def gate_keep():
    return {
        "name": "gate_repair_keep",
        "comment": "EFFECT-GATE keep: on a fresh POST-REPAIR measure (m2.post_repair), if the axis recovered "
                   "above its pre-regression baseline, accept the repair and clear the fault_open latch.",
        "match": [["m2", "banked", "ax"], ["ax", "has_fault", "f"]],
        "where": And([
            Gt(P0("f", "applied"), Lit(0.5)),
            Lt(P0("f", "gated"), Lit(0.5)),
            Gt(P0("m2", "post_repair"), Lit(0.5)),
            Gt(P0("ax", "saturation"), Minus(P0("f", "from_sat"), Lit(MARGIN))),
        ]),
        "effects": [
            ["set_attr", "f", "gated", 1.0],
            ["set_attr", "ax", "fault_open", 0.0],
            ["set_attr", "f", "outcome", "kept"],
        ],
    }


def gate_revert():
    return {
        "name": "gate_repair_revert",
        "comment": "EFFECT-GATE revert: on a fresh POST-REPAIR measure, if the axis did NOT recover, roll the "
                   "rule back to f.original via set_rule_clause and restore the shadow. The snapshot came from "
                   "the shadow, so revert never depends on reading the engine. CRUCIALLY it does NOT clear "
                   "fault_open (only a successful KEEP does): the fix failed, so the latch stays set to STOP "
                   "an infinite detect->repair->revert loop on the still-regressed axis. repair_failed=1 marks "
                   "it for a future escalation (a different fix), not silent retry of the same one.",
        "match": [["m2", "banked", "ax"], ["ax", "has_fault", "f"]],
        "where": And([
            Gt(P0("f", "applied"), Lit(0.5)),
            Lt(P0("f", "gated"), Lit(0.5)),
            Gt(P0("m2", "post_repair"), Lit(0.5)),
            Lt(P0("ax", "saturation"), Minus(P0("f", "from_sat"), Lit(MARGIN))),
        ]),
        "effects": [
            ["set_rule_clause", AC("f", "target_rule"), AC("f", "field"), AC("f", "original")],
            ["set_attr", "ax", "live_clause", AC("f", "original")],
            ["set_attr", "f", "gated", 1.0],
            ["set_attr", "ax", "repair_failed", 1.0],
            ["set_attr", "f", "outcome", "reverted"],
        ],
    }


def main():
    seed = {
        "id": "self_repair",
        "version": "2.0.0",
        "area": "self_monitoring",
        "latency_class": "hard_realtime",
        "depends_on": [],
        "description": "INTRINSIC SELF-REPAIR faculty (the jabberwock's design). A regression on a repairable "
                       "CapabilityAxis auto-mints a Fault carrying the corrected clause; a graph rule rewrites "
                       "the named live struct rule via set_rule_clause (snapshotting off the axis shadow); an "
                       "effect-gate keeps or reverts on the next post-repair measure. Self-originated, "
                       "graph-native, no Python decision. Generated by scripts/gen_self_repair_seed.py.",
        "microtheory": {"name": "self_repair",
                        "description": "regress -> detect -> repair (set_rule_clause) -> gate keep/revert, all graph-resident"},
        "nodes": [], "edges": [],
        "productions": [
            {"provenance": "seed:self_repair:has_fault",
             "src": {"type": "CapabilityAxis", "var": "x"}, "edge_type": "has_fault",
             "tgt": {"type": "Fault", "var": "y"}, "where": None,
             "weight": {"type": "Lit", "value": 1.0}},
        ],
        "rules": [fault_detect(), repair_apply(), gate_keep(), gate_revert()],
    }
    out = os.path.join(ROOT, "seeds", "self_repair.json")
    with open(out, "w") as fh:
        json.dump(seed, fh, indent=1)
    json.load(open(out))
    print(f"wrote + validated {os.path.relpath(out, ROOT)} "
          f"({len(seed['rules'])} rules, {len(seed['productions'])} productions)")


if __name__ == "__main__":
    main()
