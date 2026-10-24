#!/usr/bin/env python3
"""Generate the opt-in P24 single-receipt fan-out rules."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "common_target_evidence.json"
AREA = "common_target_evidence"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def T(v): return {"__term__": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Exists(source, name, predicate):
    return {"type": "Exists", "source": source, "var_name": name, "predicate": predicate}
def N(n, edge): return {"type": "Neighbours", "node": V(n), "edge_type": edge, "any_type": False}


def build_seed():
    relations = [
        ("Agent", "has_common_target_evidence_policy", "CommonTargetEvidencePolicy"),
        ("Agent", "has_common_target_evidence", "CommonTargetEvidence"),
        ("CommonTargetEvidence", "projects_to_transition", "TransitionObservation"),
        ("CommonTargetEvidence", "projects_to_map_pair", "TargetMapObservation"),
    ]
    fields = ("owner_id", "episode_id", "event_id", "source_epoch", "model_epoch",
              "frame_epoch", "object_id", "object_type", "action_kind", "feature_key",
              "before_value", "after_value", "split")
    observation_attrs = {k: T(A("ev", k)) for k in fields}
    observation_attrs["status"] = "observed"
    common_attrs = {k: T(A("ev", k)) for k in fields[:6]}
    common_attrs["status"] = "observed"
    ordinary = {
        "name": "cte_project_one_event_to_ordinary_transition",
        "area": AREA, "order": 1, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_common_target_evidence_policy", "pol"],
                  ["ag", "has_common_target_evidence", "ev"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("ev", "status"), L("observed")),
                      Eq(A("ev", "action_authorized"), L(True)),
                      Not(Exists(N("ag", "has_transition_observation"), "old",
                                 Eq(A("old", "event_id"), A("ev", "event_id"))))),
        "effects": [
            ["add_node", "obs", "TransitionObservation", observation_attrs],
            ["add_node", "ar", "TransitionActionReceipt", dict(common_attrs)],
            ["add_node", "orr", "TransitionOutcomeReceipt", dict(common_attrs)],
            ["add_edge", "ag", "has_transition_observation", "obs", {}],
            ["add_edge", "obs", "has_action_receipt", "ar", {}],
            ["add_edge", "obs", "has_outcome_receipt", "orr", {}],
            ["add_edge", "ev", "projects_to_transition", "obs", {}],
        ],
    }
    map_fields = {
        "pair_id": "map_pair_id", "source_event_id": "source_event_id",
        "source_status": "source_status",
        "source_action_authorized": "source_action_authorized",
        "target_event_id": "event_id", "source_object_id": "source_object_id",
        "target_object_id": "object_id", "source_action": "source_action",
        "target_action": "action_kind", "source_object_type": "source_object_type",
        "target_object_type": "object_type", "source_feature": "source_feature",
        "target_feature": "feature_key", "source_before": "source_before",
        "target_before": "before_value", "source_after": "source_after",
        "target_after": "after_value", "source_epoch": "map_source_epoch",
        "target_frame_epoch": "frame_epoch",
    }
    map_attrs = {out: T(A("ev", src)) for out, src in map_fields.items()}
    # This is a pending projection request until the additive-transfer rule
    # validates a typed source receipt and funds the native map work.
    map_attrs.update({"status": "map_pending", "same_target_event": True,
                      "target_action_authorized": T(A("ev", "action_authorized"))})
    map_rule = {
        "name": "cte_project_optional_map_view_of_same_event",
        "area": AREA, "order": 2, "latency_class": "background", "batch": False,
        "match": [["ag", "has_common_target_evidence_policy", "pol"],
                  ["ag", "has_common_target_evidence", "ev"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("ev", "status"), L("observed")),
                      Eq(A("ev", "action_authorized"), L(True)),
                      Eq(A("ev", "map_requested"), L(True)),
                      Not(Exists(N("ag", "has_target_map_observation"), "old",
                                 Eq(A("old", "pair_id"), A("ev", "map_pair_id"))))),
        "effects": [["add_node", "pair", "TargetMapObservation", map_attrs],
                    ["add_edge", "ag", "has_target_map_observation", "pair", {}],
                    ["add_edge", "ev", "projects_to_map_pair", "pair", {}]],
    }
    return {
        "id": "common_target_evidence", "version": "1.0.0",
        "depends_on": ["process_induction", "target_learning"],
        "self_load_only": True, "area": AREA,
        "description": "Opt-in P24 common target receipt projection; one event may have an ordinary view and an optional map view.",
        "microtheory": {"name": AREA, "description": "Ordinary learning is independent of optional map projection."},
        "nodes": [{"local_id": 0, "type": "CommonTargetEvidencePolicy",
                   "attrs": {"name": "common_target_evidence_policy", "enabled": 0.0}}],
        "edges": [{"src": {"role": "agent_root"},
                   "type": "has_common_target_evidence_policy", "tgt": {"local": 0},
                   "attrs": {}}],
        "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
                         "src": {"type": src, "var": "src"},
                         "edge_type": edge, "tgt": {"type": tgt, "var": "tgt"}}
                        for src, edge, tgt in relations],
        "rules": [ordinary, map_rule],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(OUT)
