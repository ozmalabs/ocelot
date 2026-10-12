#!/usr/bin/env python3
"""Emit the `self_promote_noted_concern` rule into seeds/self_promotion.json
(tranche 20). See that seed's description. Idempotent: rewrites the rules list.

IDLE is scoped to the loop's own promoted concerns (StandingConcern.source ==
'conversation_promoted' and the Experiments whose axis_tag names one): a
seeded standing concern's world experiment (e.g. standing_self_improvement's
'navigate' episode, dispatched only when a world is attached) must not block
self-promotion forever.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/self_promotion.json"


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def In(m, c): return {"type": "In", "member": m, "container": c}
def Cnt(src): return {"type": "Count", "source": src}
def F(t, var, pred): return {"type": "Filter", "source": {"type": "NodesOfType", "node_type": t}, "var_name": var, "predicate": pred}
def Zero(src): return Eq(Cnt(src), L(0))
def Or0(x): return {"type": "IfThenElse", "cond": Eq(x, L(None)), "then": L(0), "other": x}


def eligible(var):
    """A noted SelfConcern of an eligible kind not yet self-promoted or requested."""
    return And(Eq(A(var, "status"), L("noted")),
               In(A(var, "kind"), A("pol", "eligible_kinds")),
               Not(Eq(A(var, "self_promote_attempted"), L(1))),
               Not(Eq(A(var, "promote_requested"), L(1.0))))


PROMOTED = lambda var: Eq(A(var, "source"), L("conversation_promoted"))   # a promoted SelfConcern's StandingConcern
IDLE = And(
    Zero(F("StandingConcern", "st", And(PROMOTED("st"), Eq(A("st", "status"), L("pending"))))),
    Zero(F("Experiment", "e", And(In(A("e", "status"), L(["requested", "running"])),
                                  Eq(A("e", "outcome"), L(None)),
                                  {"type": "Exists", "source": F("StandingConcern", "st2", And(
                                      PROMOTED("st2"), Eq(A("st2", "name"), A("e", "axis_tag")))),
                                   "var_name": "st3", "predicate": L(True)}))),
    Zero(F("SelfConcern", "q", And(Eq(A("q", "promote_requested"), L(1.0)), Eq(A("q", "status"), L("noted"))))),
    Zero(F("SelfConcern", "r", Eq(A("r", "retry_requested"), L(1)))))

OLDEST = Eq(V("sc"), {"type": "Argmin", "source": F("SelfConcern", "y", eligible("y")),
                      "var_name": "y", "value": V("y"), "default": None})

RULE = {
    "name": "self_promote_noted_concern",
    "comment": ("The agent requests promotion of its own oldest eligible noted concern when its "
                "improvement loop is idle, once per concern, within the policy budget "
                "(seeds/self_promotion.json). The steer hook performs it, as for a human steer."),
    "match": [["ag", "has_self_promotion_policy", "pol"], ["ag", "has_self_concern", "sc"]],
    "where": And(Eq(A("pol", "enabled"), L(1)),
                 {"type": "Lt", "a": Or0(A("pol", "promoted_count")), "b": A("pol", "max_promotions")},
                 eligible("sc"), IDLE, OLDEST),
    "effects": [
        ["set_attr", "sc", "promote_requested", 1.0],
        ["set_attr", "sc", "self_promote_attempted", 1],
        ["set_attr", "sc", "promoted_by", "self"],
        ["add_edge", "sc", "promote_requested_by", "pol"],
        ["set_attr", "pol", "promoted_count",
         {"__term__": {"type": "Plus", "items": [Or0(A("pol", "promoted_count")), L(1)]}}],
    ],
}

d = json.loads(P.read_text())
d["rules"] = [RULE]
P.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n")
print("self_promotion", d["version"], [r["name"] for r in d["rules"]])
