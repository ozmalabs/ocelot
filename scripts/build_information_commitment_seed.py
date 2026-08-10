"""Emit graph-native thermodynamic wait/refine/commit policy."""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "information_commitment.json")


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(*xs): return {"type": "Times", "items": list(xs)}
def Neg(x): return {"type": "Neg", "arg": x}
def Neighbours(n, et): return {"type": "Neighbours", "node": n, "edge_type": et, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def ArgminUnique(src, var, value): return {
    "type": "ArgminUnique", "source": src, "var_name": var,
    "value": value, "default": None,
}


def set_if(var, key, value, computed=False):
    return ["set_attr_if_different", var, key, {"__term__": value} if computed else value]


CANDIDATES = Neighbours(V("ctx"), "has_candidate")
ADMISSIBLE = Filter(CANDIDATES, "option", Eq(A("option", "hard_veto"), L(0.0)))
WINNER = ArgminUnique(ADMISSIBLE, "option", Neg(A("option", "net_value")))

WAIT_VALUE = Minus(
    Plus(A("candidate", "preservation_value"), A("candidate", "expected_information_gain")),
    Plus(A("candidate", "delay_cost"), A("candidate", "opportunity_cost")),
)
REFINE_VALUE = Minus(
    Plus(
        A("candidate", "preservation_value"),
        Times(A("candidate", "expected_information_gain"), A("candidate", "decision_relevance")),
    ),
    Plus(A("candidate", "refinement_cost"), A("candidate", "delay_cost")),
)
COMMIT_VALUE = Minus(
    Plus(A("candidate", "expected_goal_work"), A("candidate", "expected_information_gain")),
    Plus(
        A("candidate", "information_destroyed"),
        A("candidate", "option_volume_lost"),
        A("candidate", "resource_cost"),
        Times(A("candidate", "uncertainty"), A("candidate", "irreversibility")),
    ),
)

RULES = [
    {
        "name": "ic_commit_without_footprint_fails_closed",
        "area": "executive", "order": 3, "latency_class": "soft_realtime",
        "match": [["ctx", "has_candidate", "candidate"]],
        "where": And(
            Eq(A("candidate", "decision_kind"), L("commit")),
            Not(Exists(Neighbours(V("candidate"), "has_effect_footprint"), "fp", L(True))),
            Eq(A("candidate", "hard_veto"), L(0.0)),
        ),
        "effects": [
            set_if("candidate", "hard_veto", 1.0),
            set_if("candidate", "veto_reason", "unknown_effect_footprint"),
        ],
    },
    {
        "name": "ic_derive_information_destruction",
        "area": "executive", "order": 3, "latency_class": "soft_realtime",
        "match": [
            ["ctx", "has_candidate", "candidate"],
            ["candidate", "has_effect_footprint", "fp"],
        ],
        "where": Eq(A("candidate", "decision_kind"), L("commit")),
        "effects": [
            set_if("candidate", "information_destroyed", Plus(
                A("fp", "deleted_facts"),
                Times(A("fp", "overwritten_facts"),
                      Minus(L(1.0), A("fp", "recoverability"))),
                A("fp", "externality"),
            ), True),
            set_if("candidate", "irreversibility", Minus(
                L(1.0), A("fp", "recoverability")), True),
        ],
    },
    {
        "name": "ic_score_wait",
        "area": "executive", "order": 3, "latency_class": "soft_realtime",
        "match": [["ctx", "has_candidate", "candidate"]],
        "where": Eq(A("candidate", "decision_kind"), L("wait")),
        "effects": [set_if("candidate", "net_value", WAIT_VALUE, True)],
    },
    {
        "name": "ic_score_refine",
        "area": "executive", "order": 3, "latency_class": "soft_realtime",
        "match": [["ctx", "has_candidate", "candidate"]],
        "where": Eq(A("candidate", "decision_kind"), L("refine")),
        "effects": [set_if("candidate", "net_value", REFINE_VALUE, True)],
    },
    {
        "name": "ic_score_commit",
        "area": "executive", "order": 3, "latency_class": "soft_realtime",
        "match": [["ctx", "has_candidate", "candidate"]],
        "where": Eq(A("candidate", "decision_kind"), L("commit")),
        "effects": [set_if("candidate", "net_value", COMMIT_VALUE, True)],
    },
    {
        "name": "ic_choose_unique_admissible_option",
        "area": "executive", "order": 3, "latency_class": "soft_realtime",
        "match": [["ctx", "has_candidate", "candidate"]],
        "where": And(Eq(V("candidate"), WINNER), Eq(A("ctx", "decided"), L(0.0))),
        "effects": [
            set_if("candidate", "chosen", 1.0),
            set_if("ctx", "decided", 1.0),
            set_if("ctx", "decision", A("candidate", "decision_kind"), True),
            ["add_node", "decision", "CommitDecision", {
                "decision_kind": {"__term__": A("candidate", "decision_kind")},
                "candidate_name": {"__term__": A("candidate", "name")},
                "net_value": {"__term__": A("candidate", "net_value")},
                "status": "resolved"
            }],
            ["add_edge", "ctx", "has_commit_decision", "decision", {}],
            ["add_edge", "decision", "selected", "candidate", {}],
        ],
    },
]

MANIFEST = {
    "id": "information_commitment",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": ["cognitive_areas"],
    "area": "executive",
    "description": (
        "Thermodynamic commitment as graph cognition. Wait, refine and commit "
        "are co-present candidates; concrete effect footprints determine "
        "information destruction and irreversibility; hard host vetoes remain "
        "outside scalar trade-offs."
    ),
    "microtheory": {
        "name": "information_commitment",
        "description": "goal work and information gain versus erasure, option loss, uncertainty and delay",
    },
    "nodes": [],
    "edges": [],
    "productions": [
        {"provenance": "seed:information_commitment:candidates",
         "src": {"type": "DecisionContext", "var": "ctx"},
         "edge_type": "has_candidate",
         "tgt": {"type": "CommitOption", "var": "candidate"}},
        {"provenance": "seed:information_commitment:footprint",
         "src": {"type": "CommitOption", "var": "candidate"},
         "edge_type": "has_effect_footprint",
         "tgt": {"type": "EffectFootprint", "var": "fp"}},
        {"provenance": "seed:information_commitment:decision",
         "src": {"type": "DecisionContext", "var": "ctx"},
         "edge_type": "has_commit_decision",
         "tgt": {"type": "CommitDecision", "var": "decision"}},
        {"provenance": "seed:information_commitment:selected",
         "src": {"type": "CommitDecision", "var": "decision"},
         "edge_type": "selected",
         "tgt": {"type": "CommitOption", "var": "candidate"}},
    ],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
    print(f"wrote {OUT} with {len(RULES)} rules")
