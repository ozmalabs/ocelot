#!/usr/bin/env python3
"""Generate the guarded graph-native numeric Shape evidence seed (P4.D2.2)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "qualia_shape_mint.json"
AREA = "qualia_shape_mint"


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(node, key): return {"type": "Attr", "node": V(node), "key": key}
def T(term): return {"__term__": term}
def N(node, edge): return {"type": "Neighbours", "node": V(node), "edge_type": edge, "any_type": False}
def Exists(source, var, predicate): return {"type": "Exists", "source": source, "var_name": var, "predicate": predicate}
def Filter(source, var, predicate): return {"type": "Filter", "source": source, "var_name": var, "predicate": predicate}
def Count(source): return {"type": "Count", "source": source}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}


def signature():
    return {"type": "ShapeRankSignature", "samples": A("obs", "coordinate"),
            "order": A("obs", "order"), "width": L(8)}


def same_shape(var="sh"):
    return And(Eq(A(var, "owner_id"), A("obs", "owner_id")),
               Eq(A(var, "frame_id"), A("obs", "frame_id")),
               Eq(A(var, "schema_version"), L(1)),
               Eq(A(var, "order"), A("obs", "order")),
               Eq(A(var, "signature"), signature()))


def prior_outcome():
    return Exists(N("ag", "has_shape_evidence"), "prior",
                  Eq(A("prior", "outcome_id"), A("obs", "outcome_id")))


def evidence_attrs(positive):
    return {"outcome_id": T(A("obs", "outcome_id")),
            "valence": T(A("obs", "valence")),
            "reading": T(A("obs", "reading") if positive else L(None)),
            "evidence_status": "verified",
            "source_epoch": T(A("obs", "source_epoch"))}


def mint_rule(name, positive):
    comparison = Gt(A("obs", "valence"), L(0.0)) if positive else Lt(A("obs", "valence"), L(0.0))
    attrs = {"owner_id": T(A("obs", "owner_id")), "frame_id": T(A("obs", "frame_id")),
             "source_epoch": T(A("obs", "source_epoch")), "schema_version": 1,
             "order": T(A("obs", "order")), "coordinate": T(A("obs", "coordinate")),
             "signature": T(signature()), "valence": T(A("obs", "valence")),
             "evidence_status": "verified", "reading": T(A("obs", "reading") if positive else L(None))}
    return {"name": name, "area": AREA, "order": 10, "latency_class": "hard_realtime",
            "match": [["ag", "has_qualia_shape_mint_policy", "pol"], ["ag", "observed", "obs"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("obs", "outcome_status"), L("verified")),
                         comparison, {"type": "Not", "arg": Eq(signature(), L(None))},
                         {"type": "Not", "arg": prior_outcome()},
                         Eq(Count(Filter(N("ag", "has_qualia_shape"), "sh", same_shape())), L(0))),
            "effects": [["add_node", "shape", "QualiaShape", attrs],
                        ["add_edge", "ag", "has_qualia_shape", "shape", {}],
                        ["add_node", "ev", "ShapeOutcomeEvidence", evidence_attrs(positive)],
                        ["add_edge", "ag", "has_shape_evidence", "ev", {}],
                        ["add_edge", "shape", "has_shape_evidence", "ev", {}]]}


def update_rule(name, positive):
    comparison = Gt(A("obs", "valence"), L(0.0)) if positive else Lt(A("obs", "valence"), L(0.0))
    effects = [["add_node", "ev", "ShapeOutcomeEvidence", evidence_attrs(positive)],
               ["add_edge", "ag", "has_shape_evidence", "ev", {}],
               ["add_edge", "sh", "has_shape_evidence", "ev", {}],
               ["set_attr", "sh", "valence", {"__term__": {"type": "Plus", "items": [A("sh", "valence"), A("obs", "valence")]}}]]
    if positive:
        effects.append(["set_attr", "sh", "reading", T(A("obs", "reading"))])
    return {"name": name, "area": AREA, "order": 11, "latency_class": "hard_realtime",
            "match": [["ag", "has_qualia_shape_mint_policy", "pol"], ["ag", "observed", "obs"],
                      ["ag", "has_qualia_shape", "sh"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("obs", "outcome_status"), L("verified")), comparison,
                         {"type": "Not", "arg": Eq(signature(), L(None))},
                         {"type": "Not", "arg": prior_outcome()}, same_shape("sh"),
                         Eq(Count(Filter(N("ag", "has_qualia_shape"), "candidate", same_shape("candidate"))), L(1))),
            "effects": effects}


def build_seed():
    productions = [
        ("Agent", "observed", "ShapeObservation"),
        ("Agent", "has_qualia_shape_mint_policy", "QualiaShapeMintPolicy"),
        ("Agent", "has_qualia_shape", "QualiaShape"),
        ("Agent", "has_shape_evidence", "ShapeOutcomeEvidence"),
        ("QualiaShape", "has_shape_evidence", "ShapeOutcomeEvidence"),
    ]
    return {
        "id": "qualia_shape_mint", "version": "1.0.0", "self_load_only": True,
        "depends_on": [], "area": AREA,
        "description": "P4 guarded graph-native minting and signed updates of numeric Shape evidence. The native ShapeRankSignature Term matches the frozen legacy oracle; verified outcome IDs are idempotent, and negative outcomes never license a reading.",
        "nodes": [{"local_id": 0, "type": "QualiaShapeMintPolicy",
                   "attrs": {"name": "qualia_shape_mint_policy", "enabled": 0.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_qualia_shape_mint_policy",
                   "tgt": {"local": 0}, "attrs": {},
                   "provenance": "qualia_shape_mint:policy"}],
        "productions": [{"src": {"type": src, "var": "src"}, "edge_type": edge,
                         "tgt": {"type": tgt, "var": "tgt"}, "where": None,
                         "weight": L(1.0), "provenance": f"qualia_shape_mint:{edge}:{src}:{tgt}"}
                        for src, edge, tgt in productions],
        "rules": [mint_rule("qsm_mint_positive_new", True), mint_rule("qsm_mint_negative_new", False),
                  update_rule("qsm_update_positive", True), update_rule("qsm_update_negative", False)],
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
