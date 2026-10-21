#!/usr/bin/env python3
"""Generate the opt-in, versioned signature projection seed (P4.D3.2)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "cognition_signature.json"
AREA = "cognition_signature"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(x): return {"__term__": x}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def And(*xs): return {"type": "And", "items": list(xs)}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(arg): return {"type": "Not", "arg": arg}
def Count(source): return {"type": "Count", "source": source}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Append(seq, item): return {"type": "Append", "seq": seq, "item": item}
def Json(value): return {"type": "ToJsonString", "value": value}
def ShapeRankSig(node="obs"):
    return {"type": "ShapeRankSignature", "samples": A(node, "coordinate"),
            "order": A(node, "order"), "width": L(8)}
def At(seq, index): return {"type": "IndexAt", "seq": seq, "index": L(index)}
def MapList(src, var, value): return {"type": "MapList", "source": src, "var_name": var, "value": value}
def StringConcat(parts): return {"type": "StringConcat", "parts": list(parts)}
def Json(value): return {"type": "ToJsonString", "value": value}


def project_rule():
    prior = Exists(N("ag", "has_cognition_signature"), "old",
                   And(Eq(A("old", "signature_key"), A("src", "signature_key")),
                       Eq(A("old", "source_epoch"), A("src", "source_epoch"))))
    attrs = {
        "schema_version": "1",
        "record_key": T(A("src", "signature_key")),
        "signature_key": T(A("src", "signature_key")),
        "owner_id": T(A("src", "owner_id")),
        "source_id": T(A("src", "source_id")),
        "source_kind": T(A("src", "source_kind")),
        "source_epoch": T(A("src", "source_epoch")),
        "frame_id": T(A("src", "frame_id")),
        "evidence_status": T(A("src", "evidence_status")),
        "dimension_ids": T(A("src", "dimension_ids")),
        "coordinates": T(A("src", "coordinates")),
        "standing_coordinates": T(A("src", "standing_coordinates")),
        "live_overlay": T(A("src", "live_overlay")),
        "status": "current",
        "live": True,
    }
    return {"name": "cs_project_versioned_signature", "area": AREA, "order": 10,
            "latency_class": "hard_realtime",
            "match": [["ag", "has_cognition_signature_policy", "pol"],
                      ["ag", "has_signature_source", "src"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("src", "schema_version"), L(1)),
                         {"type": "Not", "arg": prior}),
            "effects": [["add_node", "sig", "CognitionSignatureDescriptor", attrs],
                        ["add_edge", "ag", "has_cognition_signature", "sig", {}],
                        ["add_edge", "sig", "projects_signature_source", "src", {}]]}


def stale_rule():
    return {"name": "cs_retire_stale_signature_epoch", "area": AREA, "order": 11,
            "latency_class": "hard_realtime",
            "match": [["ag", "has_cognition_signature", "sig"],
                      ["ag", "has_signature_source", "src"]],
            "where": And(Eq(A("sig", "status"), L("current")),
                         Eq(A("sig", "signature_key"), A("src", "signature_key")),
                         Eq(A("sig", "source_id"), A("src", "source_id")),
                         {"type": "Not", "arg": Eq(A("sig", "source_epoch"), A("src", "source_epoch"))}),
            "effects": [["set_attr", "sig", "status", "stale"]]}


def observation_source_rule():
    key = Json(A("obs", "key"))
    prior = Exists(N("ag", "has_signature_source"), "old",
                   And(Eq(A("old", "source_id"), L("observation.signature")),
                       Eq(A("old", "signature_key"), key),
                       Eq(A("old", "source_epoch"), A("obs", "decoded_epoch"))))
    coordinates = MapList(A("obs", "signature"), "coordinate",
                          Append(Append(Append(Append(Append(L([]), At(V("coordinate"), 0)),
                                                        At(V("coordinate"), 1)),
                                                 At(V("coordinate"), 2)),
                                          L(False)), L(0)))
    attrs = {
        "schema_version": 1,
        "signature_key": T(key),
        "source_id": "observation.signature",
        "source_kind": "observation_signature",
        "source_epoch": T(A("obs", "decoded_epoch")),
        "owner_id": "agent-root",
        "frame_id": T(A("obs", "frame_id")),
        "evidence_status": "observed",
        "dimension_ids": T(MapList(A("obs", "signature"), "coordinate", At(V("coordinate"), 0))),
        "coordinates": T(coordinates),
        "standing_coordinates": [],
        "live_overlay": [],
    }
    return {"name": "cs_adapt_measured_observation_signature", "area": AREA, "order": 0,
            "latency_class": "hard_realtime",
            "match": [["ag", "has_cognition_signature_policy", "pol"],
                      ["ag", "observed", "obs"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         {"type": "Not", "arg": Eq(A("obs", "signature"), L(None))},
                         Gte(A("obs", "decoded_epoch"), L(0)),
                         {"type": "Not", "arg": prior}),
            "effects": [["add_node", "src", "CognitionSignatureSource", attrs],
                        ["add_edge", "ag", "has_signature_source", "src", {}],
                        ["add_edge", "obs", "has_signature_source", "src", {}]]}


def verified_shape_observation_source_rule():
    dimension = StringConcat([L("numeric:shape_rank:"), Json(A("shape", "order"))])
    key = StringConcat([L("shape-observation:"), Json(A("obs", "key"))])
    prior = Exists(N("ag", "has_signature_source"), "old",
                   And(Eq(A("old", "source_id"), L("qualia_shape")),
                       Eq(A("old", "signature_key"), key),
                       Eq(A("old", "source_epoch"), A("obs", "source_epoch"))))
    coord = Append(Append(Append(Append(Append(L([]), dimension),
                                        L("sequence_ref")),
                                 A("shape", "signature")), L(False)), L(0))
    attrs = {
        "schema_version": 1,
        "signature_key": T(key),
        "source_id": "qualia_shape",
        "source_kind": "numeric_shape",
        "source_epoch": T(A("obs", "source_epoch")),
        "owner_id": T(A("obs", "owner_id")),
        "frame_id": T(A("obs", "frame_id")),
        "evidence_status": "observed",
        "dimension_ids": T(Append(L([]), dimension)),
        "coordinates": T(Append(L([]), coord)),
        "standing_coordinates": [],
        "live_overlay": [],
    }
    return {"name": "cs_adapt_verified_shape_observation", "area": AREA,
            "order": 0, "latency_class": "hard_realtime",
        "match": [["ag", "has_cognition_signature_policy", "pol"],
                  ["ag", "observed", "obs"],
                  ["ag", "has_qualia_shape", "shape"],
                  ["shape", "has_shape_evidence", "evidence"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("obs", "outcome_status"), L("verified")),
                         Eq(A("evidence", "outcome_id"), A("obs", "outcome_id")),
                         Eq(A("shape", "evidence_status"), L("verified")),
                         Eq(A("shape", "owner_id"), A("obs", "owner_id")),
                         Eq(A("shape", "frame_id"), A("obs", "frame_id")),
                         Eq(A("shape", "source_epoch"), A("obs", "source_epoch")),
                         Not(Eq(A("shape", "signature"), L(None))),
                         Not(prior)),
            "effects": [["add_node", "src", "CognitionSignatureSource", attrs],
                        ["add_edge", "ag", "has_signature_source", "src", {}],
                        ["add_edge", "obs", "has_signature_source", "src", {}]]}


def numeric_shape_source_rule():
    dimension = StringConcat([L("numeric:shape_rank:"), Json(A("shape", "order"))])
    key = StringConcat([L("qualia-shape:"), A("shape", "owner_id"), L(":"),
                        A("shape", "frame_id"), L(":"), Json(A("shape", "order")),
                        L(":"), Json(A("shape", "source_epoch"))])
    prior = Exists(N("ag", "has_signature_source"), "old",
                   And(Eq(A("old", "source_id"), L("qualia_shape")),
                       Eq(A("old", "signature_key"), key),
                       Eq(A("old", "source_epoch"), A("shape", "source_epoch"))))
    coordinate = {"type": "Append", "seq": {
        "type": "Append", "seq": {
            "type": "Append", "seq": {
                "type": "Append", "seq": {
                    "type": "Append", "seq": L([]), "item": dimension},
                "item": L("sequence_ref")},
            "item": A("shape", "signature")},
        "item": L(False)}, "item": L(0)}
    attrs = {
        "schema_version": 1,
        "signature_key": T(key),
        "source_id": "qualia_shape",
        "source_kind": "numeric_shape",
        "source_epoch": T(A("shape", "source_epoch")),
        "owner_id": T(A("shape", "owner_id")),
        "frame_id": T(A("shape", "frame_id")),
        "evidence_status": "verified",
        "dimension_ids": T({"type": "Append", "seq": L([]), "item": dimension}),
        "coordinates": T({"type": "Append", "seq": L([]), "item": coordinate}),
        "standing_coordinates": [],
        "live_overlay": [],
    }
    return {"name": "cs_adapt_verified_numeric_shape", "area": AREA,
            "order": 0, "latency_class": "hard_realtime",
            "match": [["ag", "has_cognition_signature_policy", "pol"],
                      ["ag", "has_qualia_shape", "shape"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("shape", "evidence_status"), L("verified")),
                         {"type": "Not", "arg": prior}),
            "effects": [["add_node", "src", "CognitionSignatureSource", attrs],
                        ["add_edge", "ag", "has_signature_source", "src", {}],
                        ["add_edge", "shape", "has_signature_source", "src", {}]]}


def numeric_shape_valence_source_rule():
    key = StringConcat([L("qualia-shape-valence:"), A("shape", "owner_id"),
                        L(":"), A("shape", "frame_id")])
    epoch = {"type": "Plus", "items": [A("shape", "source_epoch"),
                                             Count(N("shape", "has_shape_evidence"))]}
    prior = Exists(N("ag", "has_signature_source"), "old",
                   And(Eq(A("old", "source_id"), L("qualia_shape.valence")),
                       Eq(A("old", "signature_key"), key)))
    dimension = L("qualia:valence")
    coordinate = Append(
        Append(Append(Append(Append(L([]), dimension), L("finite_number")),
                      A("shape", "valence")), L(False)), L(0))
    attrs = {
        "schema_version": 1,
        "signature_key": T(key),
        "source_id": "qualia_shape.valence",
        "source_kind": "valence",
        "source_epoch": T(epoch),
        "owner_id": T(A("shape", "owner_id")),
        "frame_id": T(A("shape", "frame_id")),
        "evidence_status": "verified",
        "dimension_ids": T(Append(L([]), dimension)),
        "coordinates": T(Append(L([]), coordinate)),
        "standing_coordinates": [],
        "live_overlay": [],
    }
    return {"name": "cs_adapt_verified_shape_valence", "area": AREA,
            "order": 0, "latency_class": "hard_realtime",
            "match": [["ag", "has_cognition_signature_policy", "pol"],
                      ["ag", "has_qualia_shape", "shape"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("shape", "evidence_status"), L("verified")),
                         {"type": "Gt", "a": Count(N("shape", "has_shape_evidence")),
                          "b": L(0)}, Not(prior)),
            "effects": [["add_node", "src", "CognitionSignatureSource", attrs],
                        ["add_edge", "ag", "has_signature_source", "src", {}],
                        ["add_edge", "shape", "has_signature_source", "src", {}]]}


def refresh_verified_shape_valence_source_rule():
    key = StringConcat([L("qualia-shape-valence:"), A("shape", "owner_id"),
                        L(":"), A("shape", "frame_id")])
    epoch = {"type": "Plus", "items": [A("shape", "source_epoch"),
                                             Count(N("shape", "has_shape_evidence"))]}
    dimension = L("qualia:valence")
    coordinate = Append(
        Append(Append(Append(Append(L([]), dimension), L("finite_number")),
                      A("shape", "valence")), L(False)), L(0))
    return {"name": "cs_refresh_verified_shape_valence_source", "area": AREA,
            "order": 1, "latency_class": "hard_realtime",
            "match": [["ag", "has_cognition_signature_policy", "pol"],
                      ["ag", "has_qualia_shape", "shape"],
                      ["shape", "has_signature_source", "src"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("src", "source_id"), L("qualia_shape.valence")),
                         Eq(A("src", "signature_key"), key),
                         {"type": "Not", "arg": Eq(A("src", "source_epoch"), epoch)},
                         Eq(A("shape", "evidence_status"), L("verified"))),
            "effects": [["set_attr", "src", "source_epoch", T(epoch)],
                        ["set_attr", "src", "coordinates", T(Append(L([]), coordinate))],
                        ["set_attr", "src", "evidence_status", "verified"]]}


def build_seed():
    production_edges = [
        ("Agent", "has_cognition_signature_policy", "CognitionSignaturePolicy"),
        ("Agent", "has_signature_source", "CognitionSignatureSource"),
        ("Agent", "has_qualia_shape", "QualiaShape"),
        ("Agent", "has_cognition_signature", "CognitionSignatureDescriptor"),
        ("Agent", "observed", "Observation"),
        ("Agent", "observed", "ShapeObservation"),
        ("Observation", "has_signature_source", "CognitionSignatureSource"),
        ("ShapeObservation", "has_signature_source", "CognitionSignatureSource"),
        ("QualiaShape", "has_signature_source", "CognitionSignatureSource"),
        ("CognitionSignatureDescriptor", "projects_signature_source", "CognitionSignatureSource"),
    ]
    return {
        "id": "cognition_signature", "version": "1.1.0", "self_load_only": True,
        "depends_on": ["qualia_shape_mint"], "area": AREA,
        "description": "Versioned, owner/source/frame-scoped projection of already-typed signature sources. Missing and zero remain distinct; standing and live overlays are retained in separate fields.",
        "nodes": [{"local_id": 0, "type": "CognitionSignaturePolicy",
                   "attrs": {"name": "cognition_signature_policy", "enabled": 0.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_cognition_signature_policy",
                   "tgt": {"local": 0}, "attrs": {}, "provenance": "cognition_signature:policy"}],
        "productions": [{"src": {"type": src, "var": "src"}, "edge_type": edge,
                         "tgt": {"type": tgt, "var": "tgt"}, "where": None,
                         "weight": L(1.0), "provenance": f"cognition_signature:{edge}:{src}:{tgt}"}
                        for src, edge, tgt in production_edges],
        "rules": [observation_source_rule(), verified_shape_observation_source_rule(),
                  numeric_shape_source_rule(),
                  numeric_shape_valence_source_rule(),
                  refresh_verified_shape_valence_source_rule(),
                  project_rule(), stale_rule()],
    }


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__": main()
