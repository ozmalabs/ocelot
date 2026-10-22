#!/usr/bin/env python3
"""Generate bounded graph-owned representation proposal selection (P11.02)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "representation_search.json"
AREA = "representation_search"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(v): return {"__term__": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Concat(*xs): return {"type": "StringConcat", "parts": list(xs)}
def Count(src): return {"type": "Count", "source": src}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Lte(a, b): return {"type": "Lte", "a": a, "b": b}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Plus(*items): return {"type": "Plus", "items": list(items)}


def build_seed():
    # The proposal is evidence only. Costs are generated from the complete
    # canonical package; native rules compare these immutable measured costs.
    eligible = And(Eq(A("pol", "enabled"), L(1.0)),
                   Eq(A("proposal", "status"), L("verified_candidate")),
                   Eq(A("proposal", "owner_id"), A("request", "owner_id")),
                   Eq(A("proposal", "source_epoch"), A("request", "source_epoch")),
                   Eq(A("proposal", "model_epoch"), A("request", "model_epoch")),
                   Eq(A("proposal", "frame_epoch"), A("request", "frame_epoch")),
                   Eq(A("proposal", "training_split_id"), A("request", "training_split_id")),
                   Eq(A("proposal", "candidate_cap"), A("request", "candidate_cap")),
                   Eq(A("proposal", "package_cost_complete"), L(True)),
                   Eq(A("proposal", "heldout_used_for_selection"), L(False)),
                   Eq(A("proposal", "forced_frame_preserved"), L(True)),
                   Eq(A("proposal", "discriminating_evidence"), L(True)))
    candidates = Filter(N("request", "has_candidate_proposal"), "other",
                        And(Eq(A("other", "status"), L("verified_candidate")),
                            Eq(A("other", "owner_id"), A("request", "owner_id")),
                            Eq(A("other", "source_epoch"), A("request", "source_epoch")),
                            Eq(A("other", "model_epoch"), A("request", "model_epoch")),
                            Eq(A("other", "frame_epoch"), A("request", "frame_epoch")),
                            Eq(A("other", "training_split_id"), A("request", "training_split_id"))))
    best = {"type": "ArgminUnique", "source": candidates, "var_name": "other",
            "value": A("other", "training_total_bits"), "default": None}
    relations = [
        ("Agent", "has_representation_search_policy", "RepresentationSearchPolicy"),
        ("Agent", "has_representation_search_request", "RepresentationSearchRequest"),
        ("RepresentationSearchRequest", "funded_by_request", "ThinkingBudgetRequest"),
        ("RepresentationSearchRequest", "has_candidate_proposal", "RepresentationProposal"),
        ("RepresentationSearchRequest", "has_transform_evidence", "RepresentationTransformEvidence"),
        ("RepresentationProposal", "has_heldout_validation", "RepresentationHeldoutValidation"),
        ("RepresentationProposal", "has_development_validation", "RepresentationDevelopmentValidation"),
        ("Agent", "has_representation_proposal", "RepresentationProposal"),
        ("Agent", "has_thinking_budget_request", "ThinkingBudgetRequest"),
        ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("RepresentationProposal", "has_source_frame", "ObserverFrame"),
        ("RepresentationProposal", "has_target_frame", "ObserverFrame"),
        ("RepresentationProposal", "invalidates_recall", "RecallRecord"),
        ("RepresentationProposal", "invalidates_transfer", "ProcessTransferCandidate"),
    ]
    select_rule = {"name": "rs_select_training_minimum_for_heldout_check", "area": AREA,
            "order": 2, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_representation_search_policy", "pol"],
                      ["ag", "has_representation_search_request", "request"],
                      ["request", "has_candidate_proposal", "proposal"],
                      ["request", "funded_by_request", "fund"]],
            "where": And(eligible,
                         Eq(A("request", "status"), L("funding_pending")),
                         Eq(A("fund", "requester_kind"), L("representation_search")),
                         Eq(A("fund", "status"), L("approved")),
                         Eq(A("fund", "debited_epoch"), A("request", "search_epoch")),
                         Eq(A("fund", "operation_id"), A("request", "operation_id")),
                         Eq(V("proposal"), best)),
            "effects": [["set_attr", "proposal", "status", "selected_for_heldout_validation"],
                        ["set_attr", "request", "status", "holdout_pending"]]}
    adopt_rule = {"name": "rs_adopt_only_after_frozen_heldout_validation", "area": AREA,
            "order": 3, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_representation_search_policy", "pol"],
                      ["ag", "has_representation_search_request", "request"],
                      ["request", "has_candidate_proposal", "proposal"],
                      ["proposal", "has_heldout_validation", "validation"],
                      ["request", "funded_by_request", "fund"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("proposal", "status"), L("selected_for_heldout_validation")),
                         Eq(A("request", "status"), L("holdout_pending")),
                         Eq(A("proposal", "owner_id"), A("request", "owner_id")),
                         Eq(A("proposal", "source_epoch"), A("request", "source_epoch")),
                         Eq(A("proposal", "model_epoch"), A("request", "model_epoch")),
                         Eq(A("proposal", "frame_epoch"), A("request", "frame_epoch")),
                         Eq(A("validation", "candidate_id"), A("proposal", "candidate_id")),
                         Eq(A("validation", "status"), L("scored_frozen_heldout")),
                         Eq(A("validation", "training_model_epoch"), A("proposal", "model_epoch")),
                         Eq(A("validation", "heldout_used_for_selection"), L(False)),
                         Eq(A("validation", "refit_on_heldout"), L(False)),
                         Eq(A("validation", "exceptions_added"), L(False)),
                         Eq(A("validation", "target_effect_verified"), L(True)),
                         Eq(A("validation", "wrong_frame_acceptance"), L(False)),
                         Lte(A("validation", "solve_loss_pp"), L(2.0)),
                         {"type": "Lt", "a": A("validation", "candidate_total_bits"),
                          "b": A("validation", "baseline_total_bits")},
                         Eq(A("fund", "requester_kind"), L("representation_search")),
                         Eq(A("fund", "status"), L("approved")),
                         Eq(A("fund", "debited_epoch"), A("request", "search_epoch")),
                         Eq(A("fund", "operation_id"), A("request", "operation_id"))),
            "effects": [["set_attr", "proposal", "status", "adopted"],
                        ["set_attr", "proposal", "adopted_frame_epoch", T(A("proposal", "next_frame_epoch"))],
                        ["set_attr", "proposal", "transition_from_frame", T(A("proposal", "source_frame_id"))],
                        ["set_attr", "proposal", "transition_to_frame", T(A("proposal", "target_frame_id"))],
                        ["set_attr", "proposal", "recall_invalidated", True],
                        ["set_attr", "proposal", "transfer_invalidated", True]]}
    develop_rule = {"name": "rs_validate_candidate_on_frozen_development_rows", "area": AREA,
                    "order": 2, "latency_class": "hard_realtime", "batch": False,
                    "match": [["ag", "has_representation_search_policy", "pol"],
                              ["ag", "has_representation_search_request", "request"],
                              ["request", "has_candidate_proposal", "proposal"],
                              ["proposal", "has_development_validation", "validation"]],
                    "where": And(Eq(A("pol", "enabled"), L(1.0)),
                                 Eq(A("proposal", "status"), L("candidate")),
                                 Eq(A("validation", "status"), L("scored_frozen_training")),
                                 Eq(A("validation", "candidate_id"), A("proposal", "candidate_id")),
                                 Eq(A("validation", "training_split_id"), A("request", "training_split_id")),
                                 Eq(A("validation", "training_model_epoch"), A("proposal", "model_epoch")),
                                 Eq(A("validation", "package_bits"), A("proposal", "package_bits")),
                                 Eq(A("validation", "total_bits"),
                                    Plus(A("validation", "package_bits"),
                                         A("validation", "residual_bits"))),
                                 Gte(A("validation", "discriminating_rows"),
                                     A("pol", "minimum_discriminating_rows")),
                                 Eq(A("validation", "heldout_used"), L(False))),
                    "effects": [["set_attr", "proposal", "status", "verified_candidate"],
                                ["set_attr", "proposal", "training_total_bits", T(A("validation", "total_bits"))],
                                ["set_attr", "proposal", "training_residual_bits", T(A("validation", "residual_bits"))],
                                ["set_attr", "proposal", "discriminating_evidence", True]]}
    proposal_rule = {"name": "rs_propose_from_held_transform_evidence", "area": AREA,
                    "order": 1, "latency_class": "hard_realtime", "batch": False,
                    "match": [["ag", "has_representation_search_policy", "pol"],
                              ["ag", "has_representation_search_request", "request"],
                              ["request", "has_transform_evidence", "evidence"],
                              ["request", "funded_by_request", "fund"]],
                    "where": And(Eq(A("pol", "enabled"), L(1.0)),
                                 Eq(A("request", "status"), L("funding_pending")),
                                 Eq(A("fund", "status"), L("approved")),
                                 Eq(A("fund", "debited_epoch"), A("request", "search_epoch")),
                                 Eq(A("fund", "requester_kind"), L("representation_search")),
                                 Eq(A("evidence", "status"), L("acquired_transform")),
                                 Eq(A("evidence", "owner_id"), A("request", "owner_id")),
                                 Eq(A("evidence", "source_epoch"), A("request", "source_epoch")),
                                 Eq(A("evidence", "model_epoch"), A("request", "model_epoch")),
                                 Eq(A("evidence", "frame_epoch"), A("request", "frame_epoch")),
                                 Eq(A("evidence", "training_split_id"), A("request", "training_split_id")),
                                 Eq(A("evidence", "package_cost_complete"), L(True)),
                                 Not(Exists(N("request", "has_candidate_proposal"), "old",
                                            Eq(A("old", "candidate_id"), A("evidence", "candidate_id")))),
                                 Lt(Count(N("request", "has_candidate_proposal")),
                                    A("request", "candidate_cap"))),
                    "effects": [["add_node", "proposal", "RepresentationProposal", {
                        "candidate_id": T(A("evidence", "candidate_id")),
                        "owner_id": T(A("evidence", "owner_id")),
                        "source_epoch": T(A("evidence", "source_epoch")),
                        "model_epoch": T(A("evidence", "model_epoch")),
                        "frame_epoch": T(A("evidence", "frame_epoch")),
                        "training_split_id": T(A("evidence", "training_split_id")),
                        "candidate_cap": T(A("request", "candidate_cap")),
                        "status": "candidate",
                        "canonical_package": T(A("evidence", "canonical_package")),
                        "package_bits": T(A("evidence", "package_bits")),
                        "training_residual_bits": T(A("evidence", "training_residual_bits")),
                        "training_total_bits": T(A("evidence", "training_total_bits")),
                        "package_cost_complete": True,
                        "heldout_used_for_selection": False,
                        "forced_frame_preserved": T(A("evidence", "forced_frame_preserved")),
                        "discriminating_evidence": T(A("evidence", "discriminating_evidence")),
                        "target_effect_verified": False}],
                                ["add_edge", "request", "has_candidate_proposal", "proposal", {}],
                                ["add_edge", "ag", "has_representation_proposal", "proposal", {}]]}
    request_rule = {"name": "rs_request_shared_funded_bounded_search", "area": AREA,
                    "order": 1, "latency_class": "hard_realtime", "batch": False,
                    "match": [["ag", "has_representation_search_policy", "pol"],
                              ["ag", "has_representation_search_request", "request"],
                              ["ag", "has_thinking_budget", "budget"],
                              ["ag", "has_network_mode_state", "mode"]],
                    "where": And(Eq(A("pol", "enabled"), L(1.0)),
                                 Eq(A("budget", "enabled"), L(1.0)),
                                 Eq(A("request", "status"), L("requested")),
                                 Eq(A("request", "candidate_cap"), A("pol", "max_candidates")),
                                 Eq(A("request", "training_only"), L(True))),
                    "effects": [["add_node", "fund", "ThinkingBudgetRequest", {
                        "requester_kind": "representation_search",
                        "requester_key": T(Concat(L("representation-search:"), A("request", "operation_id"),
                                                   L(":"), A("request", "owner_id"), L(":"),
                                                   {"type": "ToJsonString", "value": A("request", "source_epoch")})),
                        "source_key": T(A("request", "operation_id")),
                        "operation_id": T(A("request", "operation_id")),
                        "source_epoch": T(A("request", "source_epoch")),
                        "requested_epoch": T(A("mode", "epoch")),
                        "cost": T(A("pol", "probe_cost")), "status": "pending"}],
                                ["add_edge", "ag", "has_thinking_budget_request", "fund", {}],
                                ["add_edge", "fund", "draws_on_thinking_budget", "budget", {}],
                                ["add_edge", "request", "funded_by_request", "fund", {}],
                                ["set_attr", "request", "status", "funding_pending"]]}
    return {"id": "representation_search", "version": "1.0.0",
            "depends_on": ["thinking_budget", "cognition_aperture", "similarity_recall", "process_lifting"],
            "self_load_only": True, "area": AREA,
            "description": "P11 bounded funded representation candidate selection over complete package costs.",
            "microtheory": {"name": AREA, "description": "Select only verified, current, development-supported proposals."},
            "nodes": [{"local_id": 0, "type": "RepresentationSearchPolicy",
                       "attrs": {"name": "representation_search_policy", "enabled": 0.0,
                                 "max_candidates": 16.0, "minimum_discriminating_rows": 3.0,
                                 "probe_cost": 1.0}}],
            "edges": [{"src": {"role": "agent_root"}, "type": "has_representation_search_policy",
                       "tgt": {"local": 0}, "attrs": {}}],
            "productions": [{"provenance": f"seed:{AREA}:{e}:{s}:{t}", "src": {"type": s, "var": "src"},
                             "edge_type": e, "tgt": {"type": t, "var": "tgt"}} for s,e,t in relations],
            "rules": [request_rule, proposal_rule, develop_rule, select_rule, adopt_rule]}


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__": main()
