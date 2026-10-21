#!/usr/bin/env python3
"""Generate P5.G3.2's disabled-by-default graph stop lifecycle."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "response_inhibition.json"
AREA = "response_inhibition"


def V(n): return {"type": "Var", "name": n}
def L(x): return {"type": "Lit", "value": x}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def T(x): return {"__term__": x}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Exists(src, name, pred):
    return {"type": "Exists", "source": src, "var_name": name, "predicate": pred}


def same_stop(req="req", stop="stop"):
    return And(Eq(A(stop, "request_id"), A(req, "request_id")),
               Eq(A(stop, "source_epoch"), A(req, "source_epoch")))


def build_seed():
    active = Or(Eq(A("req", "status"), L("proposed")),
                Eq(A("req", "status"), L("selected")),
                Eq(A("req", "status"), L("authorized")))
    return {
        "id": "response_inhibition",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": [],
        "description": "P5.G3.2 opt-in graph stop lifecycle; sink enforcement is G3.3.",
        "microtheory": {"name": "response_inhibition", "description": "request-scoped stop/withhold lifecycle"},
        "nodes": [{"local_id": 0, "type": "ResponseInhibitionPolicy",
                   "attrs": {"enabled": 0.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_response_inhibition_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": [
            {"provenance": "response_inhibition:agent_request", "src": {"type": "Agent", "var": "ag"},
             "edge_type": "has_action_request", "tgt": {"type": "ActionRequest", "var": "req"}},
            {"provenance": "response_inhibition:request_stop", "src": {"type": "ActionRequest", "var": "req"},
             "edge_type": "has_action_stop", "tgt": {"type": "ActionStopEvent", "var": "stop"}},
            {"provenance": "response_inhibition:request_auth", "src": {"type": "ActionRequest", "var": "req"},
             "edge_type": "has_action_authorization", "tgt": {"type": "ActionAuthorization", "var": "auth"}},
            {"provenance": "response_inhibition:agent_policy", "src": {"type": "Agent", "var": "ag"},
             "edge_type": "has_response_inhibition_policy", "tgt": {"type": "ResponseInhibitionPolicy", "var": "policy"}},
        ],
        "rules": [
            {
                "name": "ri_withhold_same_epoch_precommit_stop", "area": AREA, "order": 1,
                "latency_class": "hard_realtime", "batch": False,
                "match": [["ag", "has_response_inhibition_policy", "policy"],
                          ["ag", "has_action_request", "req"],
                          ["req", "has_action_stop", "stop"]],
                "where": And(Eq(A("policy", "enabled"), L(1.0)),
                              same_stop(), active),
                "effects": [["set_attr", "req", "status", "withheld"],
                            ["set_attr", "req", "terminal_reason", "stop_before_commit"],
                            ["set_attr", "stop", "status", "withheld"]],
            },
            {
                "name": "ri_revoke_authorization_for_withheld_request", "area": AREA, "order": 2,
                "latency_class": "hard_realtime", "batch": False,
                "match": [["ag", "has_response_inhibition_policy", "policy"],
                          ["ag", "has_action_request", "req"],
                          ["req", "has_action_authorization", "auth"]],
                "where": And(Eq(A("policy", "enabled"), L(1.0)),
                              Eq(A("req", "status"), L("withheld")),
                              Eq(A("auth", "status"), L("pending"))),
                "effects": [["set_attr", "auth", "status", "revoked"]],
            },
            {
                "name": "ri_record_stop_after_emission_without_undo", "area": AREA, "order": 3,
                "latency_class": "hard_realtime", "batch": False,
                "match": [["ag", "has_response_inhibition_policy", "policy"],
                          ["ag", "has_action_request", "req"],
                          ["req", "has_action_stop", "stop"]],
                "where": And(Eq(A("policy", "enabled"), L(1.0)),
                              same_stop(), Eq(A("req", "status"), L("emitted")),
                              Not(Eq(A("stop", "status"), L("already_emitted")))),
                "effects": [["set_attr", "stop", "status", "already_emitted"],
                            ["set_attr", "stop", "terminal_reason", "effect_already_committed"]],
            },
        ],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n")
