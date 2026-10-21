#!/usr/bin/env python3
"""Generate the opt-in native projection layer for P5.F1.2."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "tom_unified_view.json"
AREA = "tom_unified_view"


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(node, key): return {"type": "Attr", "node": V(node), "key": key}
def T(value): return {"__term__": value}
def N(node, edge): return {"type": "Neighbours", "node": V(node), "edge_type": edge, "any_type": False}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Not(item): return {"type": "Not", "arg": item}
def Exists(source, var, predicate):
    return {"type": "Exists", "source": source, "var_name": var, "predicate": predicate}


def rules():
    current = Exists(N("ag", "has_tom_attributed_view"), "old",
                     And(Eq(A("old", "source_key"), A("src", "source_key")),
                         Eq(A("old", "source_epoch"), A("src", "source_epoch"))))
    project = {
        "name": "tuv_project_source_epoch",
        "area": AREA,
        "order": 10,
        "latency_class": "hard_realtime",
        "match": [["ag", "has_tom_view_policy", "pol"],
                  ["ag", "has_tom_attributed_source", "src"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("src", "schema_version"), L(1)), Not(current)),
        "effects": [
            ["add_node", "view", "TomAttributedStateView", {
                "schema_version": 1,
                "view_key": T(A("src", "source_key")),
                "source_key": T(A("src", "source_key")),
                "source_kind": T(A("src", "source_kind")),
                "source_node": T(A("src", "source_node")),
                "source_epoch": T(A("src", "source_epoch")),
                "owner_id": T(A("src", "owner_id")),
                "holder": T(A("src", "holder")),
                "target": T(A("src", "target")),
                "content_ref": T(A("src", "content_ref")),
                "modality": T(A("src", "modality")),
                "epistemic_kind": T(A("src", "epistemic_kind")),
                "status": "current",
            }],
            ["add_edge", "ag", "has_tom_attributed_view", "view", {}],
            ["add_edge", "view", "projects_tom_source", "src", {}],
        ],
    }
    retire = {
        "name": "tuv_retire_stale_source_epoch",
        "area": AREA,
        "order": 11,
        "latency_class": "hard_realtime",
        "match": [["ag", "has_tom_attributed_view", "view"],
                  ["ag", "has_tom_attributed_source", "src"]],
        "where": And(Eq(A("view", "status"), L("current")),
                      Eq(A("view", "source_key"), A("src", "source_key")),
                      Not(Eq(A("view", "source_epoch"), A("src", "source_epoch"))),
                      Not(Exists(N("ag", "has_tom_attributed_source"), "same_epoch",
                                  And(Eq(A("same_epoch", "source_key"), A("view", "source_key")),
                                      Eq(A("same_epoch", "source_epoch"), A("view", "source_epoch")))))),
        "effects": [["set_attr", "view", "status", "stale"]],
    }
    return [project, retire]


def build_seed():
    return {
        "id": "tom_unified_view",
        "version": "1.0.0",
        "depends_on": [],
        "description": (
            "P5.F1.2 opt-in, provenance-preserving projection of standardized "
            "TomAttributedStateSource graph events. Domain adapters translate "
            "source fields; native rules own projection and epoch retirement."
        ),
        "microtheory": {"name": "tom_unified_view", "description": "disabled-by-default attributed-state projections"},
        "nodes": [{"local_id": 0, "type": "TomViewPolicy", "attrs": {"enabled": 0.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_tom_view_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": [],
        "rules": rules(),
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n")
