#!/usr/bin/env python3
"""Generate guarded signatures over source-bound observed episode events."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "experience_signature.json"
AREA = "experience_signature"


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(node, key): return {"type": "Attr", "node": V(node), "key": key}
def T(value): return {"__term__": value}
def N(node, edge): return {"type": "Neighbours", "node": V(node), "edge_type": edge, "any_type": False}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Not(item): return {"type": "Not", "arg": item}
def Json(value): return {"type": "ToJsonString", "value": value}
def Concat(*parts): return {"type": "StringConcat", "parts": list(parts)}
def Append(seq, item): return {"type": "Append", "seq": seq, "item": item}


def signature_key():
    return Concat(L("episode:"), A("ep", "owner_id"), L(":"),
                  A("ep", "episode_id"), L(":"), A("ev", "event_id"),
                  L(":"), Json(A("ev", "source_epoch")), L(":"),
                  Json(A("ev", "frame_epoch")))


def prior_source():
    return {"type": "Exists", "source": N("ag", "has_signature_source"),
            "var_name": "old", "predicate": And(
                Eq(A("old", "signature_key"), signature_key()),
                Eq(A("old", "source_epoch"), A("ev", "source_epoch")))}


def observed_episode_signature_rule():
    dimension = L("experience:event_features")
    coordinates = Append(Append(Append(Append(Append(L([]), dimension),
                                               L("sequence_ref")),
                                        A("ev", "features")), L(False)), L(0))
    attrs = {
        "schema_version": 1,
        "signature_key": T(signature_key()),
        "source_id": T(A("ev", "event_id")),
        "source_kind": "experience_event",
        "owner_id": T(A("ep", "owner_id")),
        "episode_id": T(A("ep", "episode_id")),
        "event_id": T(A("ev", "event_id")),
        "action_id": T(A("ev", "action_id")),
        "outcome_id": T(A("receipt", "outcome_id")),
        "receipt_id": T(A("receipt", "receipt_id")),
        "source_epoch": T(A("ev", "source_epoch")),
        "model_epoch": T(A("ev", "model_epoch")),
        "frame_epoch": T(A("ev", "frame_epoch")),
        "frame_id": T(A("ev", "frame_id")),
        "evidence_status": "observed",
        "dimension_ids": T(Append(L([]), dimension)),
        "coordinates": T(Append(L([]), coordinates)),
        "standing_coordinates": [],
        "live_overlay": T(A("ev", "live_overlay")),
        "status": "current",
    }
    return {
        "name": "es_project_measured_episode_event",
        "area": AREA,
        "order": 10,
        "latency_class": "hard_realtime",
        "match": [["ag", "has_experience_signature_policy", "pol"],
                  ["ag", "has_experience_episode", "ep"],
                  ["ep", "has_experience_event", "ev"],
                  ["ev", "has_experience_outcome_receipt", "receipt"]],
        "where": And(
            Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("ep", "status"), L("observed")),
            Eq(A("ev", "status"), L("observed")),
            {"type": "In", "member": A("ev", "modality"),
             "container": L(["tool_contact", "social_request_repair"])},
            Eq(A("receipt", "status"), L("observed")),
            Eq(A("receipt", "evidence_status"), L("observed")),
            Eq(A("receipt", "owner_id"), A("ep", "owner_id")),
            Eq(A("ev", "owner_id"), A("ep", "owner_id")),
            Eq(A("receipt", "episode_id"), A("ep", "episode_id")),
            Eq(A("receipt", "event_id"), A("ev", "event_id")),
            Eq(A("receipt", "action_id"), A("ev", "action_id")),
            Eq(A("receipt", "source_epoch"), A("ev", "source_epoch")),
            Eq(A("receipt", "model_epoch"), A("ev", "model_epoch")),
            Eq(A("receipt", "frame_epoch"), A("ev", "frame_epoch")),
            Not(Eq(A("ev", "features"), L(None))),
            Not(Eq(A("ev", "features"), L([]))),
            Not(Eq(A("ev", "frame_id"), L(None))),
            Not(prior_source())),
        "effects": [
            ["add_node", "src", "CognitionSignatureSource", attrs],
            ["add_edge", "ag", "has_signature_source", "src", {}],
            ["add_edge", "ev", "has_signature_source", "src", {}],
            ["add_edge", "src", "projects_episode", "ep", {}],
            ["add_edge", "src", "projects_episode_event", "ev", {}],
            ["add_edge", "src", "uses_outcome_receipt", "receipt", {}],
        ],
    }


def build_seed():
    relations = [
        ("Agent", "has_experience_signature_policy", "ExperienceSignaturePolicy"),
        ("Agent", "has_experience_episode", "ExperienceEpisode"),
        ("ExperienceEpisode", "has_experience_event", "ExperienceEvent"),
        ("ExperienceEvent", "has_experience_outcome_receipt", "ExperienceOutcomeReceipt"),
        ("Agent", "has_signature_source", "CognitionSignatureSource"),
        ("ExperienceEvent", "has_signature_source", "CognitionSignatureSource"),
        ("CognitionSignatureSource", "projects_episode", "ExperienceEpisode"),
        ("CognitionSignatureSource", "projects_episode_event", "ExperienceEvent"),
        ("CognitionSignatureSource", "uses_outcome_receipt", "ExperienceOutcomeReceipt"),
    ]
    return {
        "id": "experience_signature",
        "version": "1.0.0",
        "depends_on": ["cognition_signature"],
        "self_load_only": True,
        "area": AREA,
        "description": (
            "P7.02: guarded, owner/epoch-bound signature projection over measured "
            "episode events. It preserves raw feature bundles and requires an "
            "exact observed outcome receipt; it does not infer or name a target axis."),
        "microtheory": {"name": AREA,
                        "description": "Project only source-bound observed episode events."},
        "nodes": [{"local_id": 0, "type": "ExperienceSignaturePolicy",
                   "attrs": {"name": "experience_signature_policy", "enabled": 0.0}}],
        "edges": [{"src": {"role": "agent_root"},
                   "type": "has_experience_signature_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": [
            {"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
             "src": {"type": src, "var": "src"}, "edge_type": edge,
             "tgt": {"type": tgt, "var": "tgt"}}
            for src, edge, tgt in relations
        ],
        "rules": [observed_episode_signature_rule()],
    }


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
