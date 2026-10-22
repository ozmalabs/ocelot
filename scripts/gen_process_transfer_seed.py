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


def build_seed():
    relations = [
        ("Agent", "has_process_transfer_policy", "ProcessTransferPolicy"),
        ("Agent", "has_process_transfer_candidate", "ProcessTransferCandidate"),
        ("ProcessTransferCandidate", "maps_source_schema", "ProcessSchema"),
        ("ProcessTransferCandidate", "targets_domain", "ProcessDomain"),
        ("ProcessTransferCandidate", "uses_frame_map", "RepresentationMap"),
        ("ProcessTransferCandidate", "has_target_verification", "ProcessTransferVerification"),
        ("ProcessTransferCandidate", "funded_by_request", "ThinkingBudgetRequest"),
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
                      Eq(A("request", "terminal_status"), L("completed")),
                      Eq(A("candidate", "map_direction"), L("source_to_target")),
                      Eq(A("map", "is_bijection"), L(True)),
                      Eq(A("map", "inverse_verified"), L(True)),
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
                    ["set_attr", "candidate", "status", "adopted"]]
    }
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
            "rules": [rule]}


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__": main()
