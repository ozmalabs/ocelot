#!/usr/bin/env python3
"""Generate the disabled-by-default native recursive ToM seed (P5.F2.2)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "recursive_tom.json"
AREA = "recursive_tom"

def V(n): return {"type": "Var", "name": n}
def L(x): return {"type": "Lit", "value": x}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(x): return {"__term__": x}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}

def rules():
    prior = Exists(N("ag", "has_recursive_tom_belief"), "old",
                   And(Eq(A("old", "event_id"), A("ev", "event_id")),
                       Eq(A("old", "actual_world_version"), A("ev", "actual_world_version"))))
    belief = {
        "name": "rtom_materialize_accessed_belief",
        "area": AREA, "order": 10, "latency_class": "hard_realtime",
        "match": [["ag", "has_recursive_tom_policy", "pol"],
                  ["ag", "has_recursive_tom_event", "ev"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("ev", "schema_version"), L(1)),
                      Eq(A("ev", "accessible"), L(True)),
                      Eq(A("ev", "has_cycle"), L(False)),
                      Lt(A("ev", "depth"), L(3)), Not(prior)),
        "effects": [
            ["add_node", "belief", "RecursiveTomBelief", {
                "event_id": T(A("ev", "event_id")),
                "holder_path": T(A("ev", "holder_path")),
                "holder_path_key": T(A("ev", "holder_path_key")),
                "depth": T(A("ev", "depth")),
                "referent": T(A("ev", "referent")),
                "content_ref": T(A("ev", "content_ref")),
                "value": T(A("ev", "value")),
                "actual_world_version": T(A("ev", "actual_world_version")),
                "access_event_id": T(A("ev", "event_id")),
            }],
            ["add_edge", "ag", "has_recursive_tom_belief", "belief", {}],
            ["add_edge", "belief", "derived_from_access_event", "ev", {}],
        ],
    }
    answers = []
    for name, status, value_predicate in (
        ("rtom_answer_true", "true", Eq(A("belief", "value"), A("q", "expected_value"))),
        ("rtom_answer_false", "false", Not(Eq(A("belief", "value"), A("q", "expected_value")))),
    ):
        prior_answer = Exists(N("ag", "has_recursive_tom_answer"), "old_answer",
                              Eq(A("old_answer", "query_id"), A("q", "query_id")))
        answers.append({
            "name": name, "area": AREA, "order": 20, "latency_class": "hard_realtime",
            "match": [["ag", "has_recursive_tom_policy", "pol"],
                      ["ag", "has_recursive_tom_query", "q"],
                      ["ag", "has_recursive_tom_belief", "belief"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                          Eq(A("q", "holder_path_key"), A("belief", "holder_path_key")),
                          Eq(A("q", "referent"), A("belief", "referent")),
                          Eq(A("q", "content_ref"), A("belief", "content_ref")),
                          Eq(A("q", "actual_world_version"), A("belief", "actual_world_version")),
                          value_predicate, Not(prior_answer)),
            "effects": [["add_node", "answer", "RecursiveTomAnswer", {
                "query_id": T(A("q", "query_id")),
                "holder_path_key": T(A("q", "holder_path_key")),
                "referent": T(A("q", "referent")),
                "content_ref": T(A("q", "content_ref")),
                "actual_world_version": T(A("q", "actual_world_version")),
                "status": status,
                "evidence_event_id": T(A("belief", "access_event_id")),
            }], ["add_edge", "ag", "has_recursive_tom_answer", "answer", {}],
                ["add_edge", "answer", "answers_recursive_tom_query", "q", {}]],
        })
    return [belief, *answers]

def build_seed():
    return {
        "id": "recursive_tom", "version": "1.0.0", "depends_on": [],
        "description": "P5.F2.2 opt-in native materialization of bounded, access-backed recursive ToM events; actual-world records are never targets of update rules.",
        "microtheory": {"name": "recursive_tom", "description": "bounded recursive belief worlds"},
        "nodes": [{"local_id": 0, "type": "RecursiveTomPolicy", "attrs": {"enabled": 0.0, "max_depth": 2}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_recursive_tom_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": [], "rules": rules(),
    }

if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n")
