#!/usr/bin/env python3
"""Generate the default-off graph caller for the native finite SCM Term."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "scm_reasoning.json"


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(node, key): return {"type": "Attr", "node": V(node), "key": key}
def T(term): return {"__term__": term}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Not(term): return {"type": "Not", "arg": term}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def MkDict(*items): return {"type": "MkDict", "items": list(items)}


def scm_query_term():
    return {
        "type": "SCMIntervene",
        "model": A("m", "snapshot"),
        "query": MkDict(
            L("kind"), A("q", "kind"),
            L("outcome"), A("q", "outcome"),
            L("adjustment"), A("q", "adjustment"),
        ),
        "intervention": A("q", "intervention"),
        "exogenous_assignments": A("q", "exogenous_assignments"),
        "assignment_cap": A("q", "assignment_cap"),
    }


def evaluate_rule():
    return {
        "name": "scm_evaluate_detached_query",
        "batch": False,
        "comment": "Evaluate one current, funded, detached SCM request; write only to its query record and retain model identity.",
        "match": [
            ["ag", "has_scm_reasoning_policy", "pol"],
            ["q", "uses_scm_model", "m"],
        ],
        "where": And(
            Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("q", "scm_status"), L("pending")),
            Eq(A("q", "funding_approved"), L(True)),
            Eq(A("q", "source_epoch"), A("m", "source_epoch")),
            Gte(A("pol", "remaining"), L(1.0)),
        ),
        "effects": [
            ["set_attr", "q", "scm_result", T(scm_query_term())],
            ["set_attr", "q", "scm_status", "evaluated"],
            ["set_attr", "q", "model_hash_used", T(A("m", "model_hash"))],
            ["set_attr", "q", "evaluated_source_epoch", T(A("m", "source_epoch"))],
            ["set_attr", "pol", "remaining", T(Minus(A("pol", "remaining"), L(1.0)))],
        ],
    }


def refuse_stale_rule():
    return {
        "name": "scm_refuse_stale_query",
        "batch": False,
        "comment": "Close a pending request as stale without evaluating or spending budget when its model epoch changed.",
        "match": [["ag", "has_scm_reasoning_policy", "pol"], ["q", "uses_scm_model", "m"]],
        "where": And(
            Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("q", "scm_status"), L("pending")),
            Not(Eq(A("q", "source_epoch"), A("m", "source_epoch"))),
        ),
        "effects": [
            ["set_attr", "q", "scm_status", "unknown"],
            ["set_attr", "q", "scm_reason", "source_model_epoch_mismatch"],
        ],
    }


def build():
    productions = [
        ("Agent", "has_scm_reasoning_policy", "ScmReasoningPolicy"),
        ("ScmQuery", "uses_scm_model", "ScmModel"),
    ]
    return {
        "id": "scm_reasoning",
        "version": "1.0.0",
        "depends_on": [],
        "area": "cognition",
        "self_load_only": True,
        "description": "Default-off funded caller for detached native SCM queries; results remain query records and never become observations.",
        "microtheory": {"name": "scm_reasoning", "description": "Evaluate explicitly supplied finite models without treating associations as mechanisms."},
        "nodes": [{"local_id": 0, "type": "ScmReasoningPolicy", "attrs": {"enabled": 0.0, "remaining": 0.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_scm_reasoning_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": [
            {"provenance": f"seed:scm_reasoning:{edge}", "src": {"type": src, "var": "src"},
             "edge_type": edge, "tgt": {"type": tgt, "var": "tgt"}}
            for src, edge, tgt in productions
        ],
        "rules": [evaluate_rule(), refuse_stale_rule()],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
