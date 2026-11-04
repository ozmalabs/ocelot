#!/usr/bin/env python3
"""Generate P28's opt-in bridge from P17 acquired axes to flex-frame proposals."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "ousiometric_acquisition.json"
AREA = "ousiometric_acquisition"


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(node, key): return {"type": "Attr", "node": V(node), "key": key}
def T(value): return {"__term__": value}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Not(item): return {"type": "Not", "arg": item}
def Exists(source, name, predicate): return {"type": "Exists", "source": source, "var_name": name, "predicate": predicate}
def N(node, edge): return {"type": "Neighbours", "node": V(node), "edge_type": edge, "any_type": False}
def Count(source): return {"type": "Count", "source": source}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Times(*items): return {"type": "Times", "items": list(items)}
def Concat(*parts): return {"type": "StringConcat", "parts": list(parts)}
def Json(value): return {"type": "ToJsonString", "value": value}


def _request_key():
    return Concat(L("ousiometric-flex-frame:"), Json(A("cand", "candidate_key")))


def request_rule():
    prior = Exists(N("ag", "has_thinking_budget_request"), "old",
                   Eq(A("old", "requester_key"), _request_key()))
    return {
        "name": "oua_request_funded_flex_frame_proposal",
        "area": AREA, "order": 1, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_ousiometric_acquisition_policy", "pol"],
                  ["ag", "has_thinking_budget", "budget"],
                  ["ag", "has_network_mode_state", "mode"],
                  ["ag", "has_qualia_axis_candidate", "cand"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("budget", "enabled"), L(1.0)),
                     Eq(A("cand", "status"), L("validated")),
                     Gte(Count(N("cand", "has_acquisition_witness")), A("pol", "recurrence_episodes")),
                     Gte(Count(N("cand", "has_acquisition_validation")), A("pol", "fresh_validation_episodes")),
                     Lt(Count(N("ag", "has_ousiometric_frame_candidate")), A("pol", "max_candidates")),
                     Not(Eq(A("cand", "heldout_used_for_selection"), L(True))),
                     Not(prior)),
        "effects": [
            ["add_node", "req", "ThinkingBudgetRequest", {
                "requester_kind": "ousiometric_frame_proposal",
                "requester_key": T(_request_key()),
                "source_key": T(A("cand", "candidate_key")),
                "source_epoch": T(A("cand", "source_epoch")),
                "requested_epoch": T(A("mode", "epoch")),
                "deadline_epoch": T(Plus(A("mode", "epoch"), L(1.0))),
                "cost": T(A("pol", "proposal_work_cost")),
                "status": "pending",
            }],
            ["add_edge", "ag", "has_thinking_budget_request", "req", {}],
            ["add_edge", "req", "draws_on_thinking_budget", "budget", {}],
            ["add_edge", "req", "funds_ousiometric_candidate", "cand", {}],
        ],
    }


def proposal_rule():
    prior = Exists(N("ag", "has_ousiometric_frame_candidate"), "old",
                   Eq(A("old", "source_candidate_key"), A("cand", "candidate_key")))
    package_bits = Plus(A("pol", "schema_overhead_bits"),
                        Times(A("pol", "stable_id_count"), A("pol", "stable_id_bits")))
    return {
        "name": "oua_propose_flex_coordinate_from_validated_observed_axis",
        "area": AREA, "order": 2, "latency_class": "background", "batch": False,
        "match": [["ag", "has_ousiometric_acquisition_policy", "pol"],
                  ["ag", "has_qualia_axis_candidate", "cand"],
                  ["req", "funds_ousiometric_candidate", "cand"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("cand", "status"), L("validated")),
                     Eq(A("req", "status"), L("approved")),
                     Eq(A("req", "requester_kind"), L("ousiometric_frame_proposal")),
                     Eq(A("req", "source_epoch"), A("cand", "source_epoch")),
                     Gte(Count(N("cand", "has_acquisition_witness")), A("pol", "recurrence_episodes")),
                     Gte(Count(N("cand", "has_acquisition_validation")), A("pol", "fresh_validation_episodes")),
                     {"type": "Lte", "a": package_bits, "b": A("pol", "max_package_bits")},
                     Not(Eq(A("cand", "heldout_used_for_selection"), L(True))),
                     Not(prior)),
        "effects": [
            ["add_node", "frame_candidate", "OusiometricFrameCandidate", {
                "candidate_id": T(A("cand", "candidate_key")),
                "source_candidate_key": T(A("cand", "candidate_key")),
                "dimension_id": T(A("cand", "dimension_id")),
                "feature_key": T(A("cand", "feature_key")),
                "feature_family": T(A("cand", "feature_family")),
                "owner_id": T(A("cand", "owner_id")),
                "source_epoch": T(A("cand", "source_epoch")),
                "model_epoch": T(A("cand", "model_epoch")),
                "frame_epoch": T(A("cand", "frame_epoch")),
                "frame_class": "learned_flex",
                "status": "proposed",
                "adds_observed_coordinate": True,
                "rotation_only": False,
                "source_coordinate_count": 3.0,
                "target_coordinate_count": 4.0,
                "observed_witness_count": T(Count(N("cand", "has_acquisition_witness"))),
                "fresh_validation_count": T(Count(N("cand", "has_acquisition_validation"))),
                "heldout_used_for_selection": False,
                "lexical_labels_available": False,
                "description_cost_schema": "p28_flex_coordinate_v1",
                "schema_overhead_bits": T(A("pol", "schema_overhead_bits")),
                "stable_id_count": T(A("pol", "stable_id_count")),
                "stable_id_bits": T(A("pol", "stable_id_bits")),
                "exception_bits": 0.0,
                "total_description_bits": T(package_bits),
                "package_cost_complete": True,
                "proposal_work_cost": T(A("req", "cost")),
                "proposal_work_funded": True,
            }],
            ["add_edge", "ag", "has_ousiometric_frame_candidate", "frame_candidate", {}],
            ["add_edge", "frame_candidate", "derived_from_axis_candidate", "cand", {}],
            ["add_edge", "frame_candidate", "funded_by_request", "req", {}],
        ],
    }


def retire_stale_candidate_rule():
    return {
        "name": "oua_retire_frame_candidate_when_source_is_contested_or_stale",
        "area": AREA, "order": 3, "latency_class": "background", "batch": False,
        "match": [["ag", "has_ousiometric_acquisition_policy", "pol"],
                  ["ag", "has_ousiometric_frame_candidate", "fc"],
                  ["fc", "derived_from_axis_candidate", "cand"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("fc", "status"), L("proposed")),
                     {"type": "Or", "items": [
                         Eq(A("cand", "status"), L("contested")),
                         {"type": "Not", "arg": Eq(A("fc", "source_epoch"), A("cand", "source_epoch"))},
                     ]}),
        "effects": [["set_attr", "fc", "status", "retired"],
                    ["set_attr", "fc", "retirement_reason", "source_contested_or_stale"]],
    }


def build_seed():
    relations = [
        ("Agent", "has_ousiometric_acquisition_policy", "OusiometricAcquisitionPolicy"),
        ("Agent", "has_qualia_axis_candidate", "QualiaAxisCandidate"),
        ("Agent", "has_ousiometric_frame_candidate", "OusiometricFrameCandidate"),
        ("QualiaAxisCandidate", "has_acquisition_witness", "QualiaAcquisitionWitness"),
        ("QualiaAxisCandidate", "has_acquisition_validation", "QualiaAcquisitionValidation"),
        ("ThinkingBudgetRequest", "funds_ousiometric_candidate", "QualiaAxisCandidate"),
        ("OusiometricFrameCandidate", "derived_from_axis_candidate", "QualiaAxisCandidate"),
        ("OusiometricFrameCandidate", "has_support_witness", "QualiaAcquisitionWitness"),
        ("OusiometricFrameCandidate", "has_fresh_validation", "QualiaAcquisitionValidation"),
        ("OusiometricFrameCandidate", "funded_by_request", "ThinkingBudgetRequest"),
    ]
    return {
        "id": AREA, "version": "1.0.0",
        "depends_on": ["ousiometric_frames", "qualia_acquisition", "thinking_budget"],
        "self_load_only": True, "area": AREA,
        "description": "P28 bridge from already verified, episode-grounded native axes to costed learned-flex frame proposals; no lexical labels or implicit adoption.",
        "microtheory": {"name": AREA, "description": "A coordinate becomes a flex-frame proposal only after P17 observed recurrence and two fresh validations, plus a separately funded proposal."},
        "nodes": [{"local_id": 0, "type": "OusiometricAcquisitionPolicy", "attrs": {
            "name": "p28_ousiometric_acquisition_policy", "enabled": 0.0,
            "recurrence_episodes": 3.0, "fresh_validation_episodes": 2.0,
            "max_candidates": 8.0, "proposal_work_cost": 1.0,
            "schema_overhead_bits": 128.0, "stable_id_count": 8.0,
            "stable_id_bits": 64.0, "max_package_bits": 4096.0,
            "lexical_labels_available": False,
        }}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_ousiometric_acquisition_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{dst}",
                         "src": {"type": src, "var": "src"}, "edge_type": edge,
                         "tgt": {"type": dst, "var": "tgt"}}
                        for src, edge, dst in relations],
        "rules": [request_rule(), proposal_rule(), retire_stale_candidate_rule()],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(OUT)
