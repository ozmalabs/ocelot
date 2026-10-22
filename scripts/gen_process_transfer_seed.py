#!/usr/bin/env python3
"""Generate conservative, target-verified process transfer rules (P11.03)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "process_transfer.json"
AREA = "process_transfer"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(v): return {"__term__": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Not(x): return {"type": "Not", "arg": x}
def Concat(*xs): return {"type": "StringConcat", "parts": list(xs)}


def conjugate_term():
    # Native convention is "a then b", so inverse-map -> source process -> map.
    inv = {"type": "Attr", "node": V("map"), "key": "inverse_map"}
    source = {"type": "Attr", "node": V("source"), "key": "params"}
    forward = {"type": "Attr", "node": V("map"), "key": "forward_map"}
    return {"type": "ProcessCompose",
            "a": {"type": "ProcessCompose", "a": inv, "b": source},
            "b": forward}


def build_seed():
    relations = [
        ("Agent", "has_process_transfer_policy", "ProcessTransferPolicy"),
        ("Agent", "has_process_transfer_candidate", "ProcessTransferCandidate"),
        ("ProcessTransferCandidate", "maps_source_schema", "ProcessSchema"),
        ("ProcessTransferCandidate", "targets_domain", "ProcessDomain"),
        ("ProcessTransferCandidate", "uses_frame_map", "RepresentationMap"),
        ("ProcessTransferCandidate", "has_target_verification", "ProcessTransferVerification"),
        ("ProcessTransferCandidate", "funded_by_request", "ThinkingBudgetRequest"),
        ("RepresentationProposal", "transfers_source_schema", "ProcessSchema"),
        ("RepresentationProposal", "transfers_to_domain", "ProcessDomain"),
        ("RepresentationProposal", "uses_transfer_map", "RepresentationMap"),
        ("Agent", "has_process_schema", "ProcessSchema"),
    ]
    rule = {
        "name": "pt_adopt_only_fresh_exact_target_verified_candidate",
        "area": AREA, "order": 1, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_process_transfer_policy", "pol"],
                  ["ag", "has_process_transfer_candidate", "candidate"],
                  ["candidate", "maps_source_schema", "source"],
                  ["candidate", "targets_domain", "target"],
                  ["candidate", "uses_frame_map", "map"],
                  ["candidate", "has_target_verification", "verification"],
                  ["candidate", "funded_by_request", "request"],
                  ["request", "draws_on_thinking_budget", "budget"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("candidate", "status"), L("candidate")),
                      Eq(A("request", "requester_kind"), L("process_transfer")),
                      Eq(A("request", "status"), L("approved")),
                      Eq(A("request", "debited_epoch"), A("candidate", "search_epoch")),
                      Eq(A("candidate", "map_direction"), L("source_to_target")),
                      Eq(A("map", "is_bijection"), L(True)),
                      Eq(A("map", "inverse_verified"), L(True)),
                      Eq({"type": "ProcessInverse", "a": A("map", "forward_map")},
                         A("map", "inverse_map")),
                      Eq({"type": "ProcessInverse", "a": A("map", "inverse_map")},
                         A("map", "forward_map")),
                      Eq(A("map", "source_epoch"), A("candidate", "source_epoch")),
                      Eq(A("map", "target_frame_epoch"), A("candidate", "target_frame_epoch")),
                      Eq(A("candidate", "source_epoch"), A("source", "source_epoch")),
                      Eq(A("candidate", "target_probe_epoch"), A("target", "probe_epoch")),
                      Eq(A("verification", "status"), L("verified")),
                      Eq(A("verification", "verification_kind"), L("fresh_native_target_effect")),
                      Eq(A("verification", "candidate_id"), A("candidate", "candidate_id")),
                      Eq(A("verification", "source_epoch"), A("candidate", "source_epoch")),
                      Eq(A("verification", "target_probe_epoch"), A("target", "probe_epoch")),
                      Eq(A("verification", "composition_order"), L("f_after_g_after_f_inv")),
                      Eq(A("candidate", "nonconjugate"), L(False)),
                      Eq(A("candidate", "wrong_frame"), L(False)),
                      Eq(A("candidate", "complete_separating_set"), L(True))),
        "effects": [["add_node", "transferred", "ProcessSchema", {
            "name": T(A("candidate", "target_process_name")),
            "kind": T(A("target", "kind")), "domain": T(A("target", "name")),
            "domain_kind": T(A("target", "kind")),
            "operator": T(A("source", "operator")),
            "status": "active", "provenance": "verified_process_transfer",
            "effect_evaluation": "exact:native_target_conjugacy",
            "source_epoch": T(A("candidate", "source_epoch")),
            "model_epoch": T(A("candidate", "model_epoch")),
            "frame_epoch": T(A("candidate", "target_frame_epoch")),
            "probe_epoch": T(A("target", "probe_epoch")),
            "params": T(A("candidate", "composed_target_program")),
            "verification_receipt": T(A("verification", "receipt_id"))}],
                    ["add_edge", "ag", "has_process_schema", "transferred", {}],
                    ["set_attr", "candidate", "status", "adopted"],
                    ["set_attr", "request", "terminal_status", "completed"]]
    }
    candidate_rule = {
        "name": "pt_compose_candidate_with_native_process_algebra",
        "area": AREA, "order": 0, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_process_transfer_policy", "pol"],
                  ["ag", "has_representation_proposal", "proposal"],
                  ["proposal", "transfers_source_schema", "source"],
                  ["proposal", "transfers_to_domain", "target"],
                  ["proposal", "uses_transfer_map", "map"],
                  ["ag", "has_thinking_budget_request", "request"],
                  ["request", "draws_on_thinking_budget", "budget"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("proposal", "status"), L("adopted")),
                      Eq(A("proposal", "package_cost_complete"), L(True)),
                      Eq(A("map", "is_bijection"), L(True)),
                      Eq(A("map", "inverse_verified"), L(True)),
                      Eq({"type": "ProcessInverse", "a": A("map", "forward_map")},
                         A("map", "inverse_map")),
                      Eq({"type": "ProcessInverse", "a": A("map", "inverse_map")},
                         A("map", "forward_map")),
                      Eq(A("map", "source_epoch"), A("proposal", "source_epoch")),
                      Eq(A("map", "target_frame_epoch"), A("proposal", "target_frame_epoch")),
                      Eq(A("source", "source_epoch"), A("proposal", "source_epoch")),
                      Eq(A("source", "model_epoch"), A("proposal", "model_epoch")),
                      Eq(A("source", "frame_epoch"), A("proposal", "frame_epoch")),
                      Eq(A("request", "requester_kind"), L("process_transfer")),
                      Eq(A("request", "status"), L("approved")),
                      Not(Exists(N("ag", "has_process_transfer_candidate"), "old",
                                 Eq(A("old", "candidate_id"),
                                    Concat(A("proposal", "candidate_id"), L("->"), A("target", "name")))))),
        "effects": [["add_node", "candidate", "ProcessTransferCandidate", {
            "candidate_id": T(Concat(A("proposal", "candidate_id"), L("->"), A("target", "name"))),
            "status": "candidate", "map_direction": "source_to_target",
            "source_epoch": T(A("proposal", "source_epoch")),
            "model_epoch": T(A("proposal", "model_epoch")),
            "target_frame_epoch": T(A("proposal", "target_frame_epoch")),
            "target_probe_epoch": T(A("target", "probe_epoch")),
            "search_epoch": T(A("request", "debited_epoch")),
            "nonconjugate": False, "wrong_frame": False,
            "complete_separating_set": T(A("map", "complete_separating_set")),
            "target_process_name": T(Concat(L("transfer:"), A("source", "name"))),
            "composed_target_program": T(conjugate_term())}],
                    ["add_edge", "ag", "has_process_transfer_candidate", "candidate", {}],
                    ["add_edge", "candidate", "maps_source_schema", "source", {}],
                    ["add_edge", "candidate", "targets_domain", "target", {}],
                    ["add_edge", "candidate", "uses_frame_map", "map", {}],
                    ["add_edge", "candidate", "funded_by_request", "request", {}]]}
    return {"id": "process_transfer", "version": "1.0.0",
            "depends_on": ["process_schema", "process_lifting", "representation_search"],
            "self_load_only": True, "area": AREA,
            "description": "P11 exact process transfer requires a typed bijection and fresh native target verification.",
            "microtheory": {"name": AREA, "description": "Candidate recall with local fallback unless exact transfer is verified."},
            "nodes": [{"local_id": 0, "type": "ProcessTransferPolicy",
                       "attrs": {"name": "process_transfer_policy", "enabled": 0.0,
                                 "max_candidates": 16.0, "fresh_target_probes": 3.0}}],
            "edges": [{"src": {"role": "agent_root"}, "type": "has_process_transfer_policy",
                       "tgt": {"local": 0}, "attrs": {}}],
            "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
                             "src": {"type": src, "var": "src"}, "edge_type": edge,
                             "tgt": {"type": tgt, "var": "tgt"}} for src, edge, tgt in relations],
            "rules": [candidate_rule, rule]}


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__": main()
