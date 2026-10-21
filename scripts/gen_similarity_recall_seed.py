#!/usr/bin/env python3
"""Generate candidate-only bounded similarity recall rules (P4.D4.2)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "similarity_recall.json"
AREA = "similarity_recall"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(x): return {"__term__": x}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Count(x): return {"type": "Count", "source": x}
def At(seq, index): return {"type": "IndexAt", "seq": seq, "index": L(index)}
def MapList(src, var, value): return {"type": "MapList", "source": src, "var_name": var, "value": value}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Dict(items): return {"type": "MkDict", "items": [term for pair in items for term in pair]}
def FilterList(src, var, predicate): return {"type": "FilterList", "source": src, "var_name": var, "predicate": predicate}
def Json(value): return {"type": "ToJsonString", "value": value}


RECORD_FIELDS = ["record_key", "owner_id", "source_id", "frame_id", "schema_version",
                 "source_epoch", "live", "coordinates"]


def record(var):
    values = {key: A(var, key) for key in RECORD_FIELDS}
    values["live"] = And(Eq(A(var, "status"), L("current")), Eq(A(var, "live"), L(True)))
    return Dict([[L(key), values[key]] for key in RECORD_FIELDS])


def query_record(var):
    return Dict([[L(key), A(var, "query_key" if key == "record_key" else key)] for key in RECORD_FIELDS])


def recall_rule():
    exists_result = Exists(N("ag", "has_similarity_recall_result"), "old",
                           And(Eq(A("old", "observation_key"), A("q", "observation_key")),
                               Eq(A("old", "query_epoch"), A("q", "query_epoch"))))
    call = {"type": "RecallNearest",
            "records": MapList(FilterList(N("ag", "has_cognition_signature"), "sig",
                                          Not(Eq(A("sig", "record_key"), A("q", "query_key")))),
                               "sig", record("sig")),
            "query": query_record("q"), "k": A("pol", "k"), "candidate_cap": A("pol", "candidate_cap")}
    attrs = {
        "query_key": T(A("q", "query_key")),
        "query_epoch": T(A("q", "source_epoch")),
        "observation_key": T(A("q", "observation_key")),
        "candidate_scan": T(call),
        "status": "candidate_only",
        "requires_verification": True,
    }
    return {"name": "sr_publish_bounded_candidate_recall", "area": AREA, "order": 2,
            "latency_class": "hard_realtime",
            "match": [["ag", "has_similarity_recall_policy", "pol"],
                      ["ag", "has_similarity_query", "q"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("q", "status"), L("ready")), Not(exists_result)),
            "effects": [["add_node", "result", "SimilarityRecallResult", attrs],
                        ["add_edge", "ag", "has_similarity_recall_result", "result", {}],
                        ["add_edge", "result", "recall_for_query", "q", {}],
                        ["set_attr", "q", "status", "recalled"]]}


def project_query_rule():
    prior = Exists(N("ag", "has_similarity_query"), "old",
                   Eq(A("old", "observation_key"), Json(A("obs", "key"))))
    attrs = {
        "query_key": T(A("src", "signature_key")),
        "owner_id": T(A("src", "owner_id")),
        "source_id": T(A("src", "source_id")),
        "frame_id": T(A("src", "frame_id")),
        "schema_version": "1",
        "source_epoch": T(A("src", "source_epoch")),
        "live": True,
        "coordinates": T(A("src", "coordinates")),
        "observation_key": T(Json(A("obs", "key"))),
    }
    attrs.update({"k": 8, "candidate_cap": 256, "status": "ready"})
    return {"name": "sr_project_observed_signature_query", "area": AREA, "order": 1,
            "latency_class": "hard_realtime",
            "match": [["ag", "has_similarity_recall_policy", "pol"],
                      ["ag", "observed", "obs"],
                      ["obs", "has_signature_source", "src"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("src", "evidence_status"), L("observed")),
                         Eq(A("src", "schema_version"), L(1)), Not(prior)),
            "effects": [["add_node", "q", "CognitionSignatureQuery", attrs],
                        ["add_edge", "ag", "has_similarity_query", "q", {}],
                        ["add_edge", "q", "projects_query_source", "src", {}],
                        ["add_edge", "q", "projects_observation", "obs", {}]]}


def exact_verify_rule():
    candidates = At(A("result", "candidate_scan"), 0)
    zero_hits = FilterList(candidates, "candidate",
                           Eq(At(V("candidate"), 1), L(0)))
    unique_candidate_key = At(At(candidates, 0), 0)
    return {"name": "sr_verify_unique_exact_signature_hit", "area": AREA, "order": 4,
            "latency_class": "hard_realtime",
            "match": [["ag", "has_similarity_recall_result", "result"],
                      ["result", "recall_for_query", "q"],
                      ["q", "projects_observation", "obs"],
                      ["ag", "has_cognition_signature", "sig"],
                      ["obs", "has_signature_verification_receipt", "receipt"],
                      ["receipt", "verifies_signature", "sig"]],
            "where": And(Eq(A("result", "status"), L("candidate_only")),
                         Eq(A("result", "requires_verification"), L(True)),
                         Eq(At(A("result", "candidate_scan"), 2), L(True)),
                         Eq(Count(zero_hits), L(1)),
                         Eq(Json(A("sig", "record_key")), Json(unique_candidate_key)),
                         Eq(A("sig", "status"), L("current")),
                         Eq(A("sig", "coordinates"), A("q", "coordinates")),
                         Eq(A("receipt", "status"), L("verified")),
                         Eq(Json(A("receipt", "record_key")), Json(unique_candidate_key)),
                         Eq(Json(A("receipt", "observation_key")), Json(A("q", "observation_key"))),
                         Eq(A("receipt", "source_epoch"), A("q", "source_epoch"))),
            "effects": [["set_attr", "result", "status", "accepted_verified_exact"],
                        ["set_attr", "result", "verified_record_key", T(unique_candidate_key)],
                        ["add_edge", "result", "verified_signature", "sig", {}],
                        ["set_attr", "q", "status", "accepted"],
                        ["set_attr", "obs", "dim_explained", 1],
                        ["set_attr", "obs", "status", "recognized_duplicate"]]}


def verified_shape_outcome_receipt_rule():
    candidates = At(A("result", "candidate_scan"), 0)
    zero_hits = FilterList(candidates, "candidate",
                           Eq(At(V("candidate"), 1), L(0)))
    record_key = At(At(candidates, 0), 0)
    prior = Exists(N("obs", "has_signature_verification_receipt"), "old",
                   And(Eq(A("old", "record_key"), record_key),
                       Eq(A("old", "observation_key"), A("q", "observation_key")),
                       Eq(A("old", "source_epoch"), A("q", "source_epoch"))))
    return {"name": "sr_mint_receipt_from_verified_shape_outcome", "area": AREA,
            "order": 3, "latency_class": "hard_realtime",
            "match": [["ag", "has_similarity_recall_result", "result"],
                      ["result", "recall_for_query", "q"],
                      ["q", "projects_observation", "obs"],
                      ["obs", "has_signature_source", "source"],
                      ["ag", "has_cognition_signature", "sig"]],
            "where": And(Eq(A("result", "status"), L("candidate_only")),
                         Eq(A("result", "requires_verification"), L(True)),
                         Eq(At(A("result", "candidate_scan"), 2), L(True)),
                         Eq(Count(zero_hits), L(1)),
                         Eq(Json(A("sig", "record_key")), Json(record_key)),
                         Eq(A("sig", "status"), L("current")),
                         Eq(A("sig", "live"), L(True)),
                         Eq(A("sig", "coordinates"), A("q", "coordinates")),
                         Eq(A("sig", "owner_id"), A("q", "owner_id")),
                         Eq(A("sig", "source_id"), A("q", "source_id")),
                         Eq(A("sig", "frame_id"), A("q", "frame_id")),
                         Eq(A("sig", "source_epoch"), A("q", "source_epoch")),
                         Eq(A("source", "source_id"), L("qualia_shape")),
                         Eq(A("source", "evidence_status"), L("observed")),
                         Eq(A("obs", "outcome_status"), L("verified")),
                         Not(Eq(A("obs", "outcome_id"), L(None))),
                         Not(prior)),
            "effects": [["add_node", "receipt", "CognitionSignatureVerificationReceipt", {
                            "status": "verified", "record_key": T(record_key),
                            "observation_key": T(A("q", "observation_key")),
                            "source_epoch": T(A("q", "source_epoch")),
                            "verifier_kind": "verified_shape_outcome",
                            "verifier_evidence_id": T(A("obs", "outcome_id"))}],
                        ["add_edge", "obs", "has_signature_verification_receipt", "receipt", {}],
                        ["add_edge", "receipt", "verifies_signature", "sig", {}]]}


def fallback_rule():
    candidates = At(A("result", "candidate_scan"), 0)
    zero_hits = FilterList(candidates, "candidate",
                           Eq(At(V("candidate"), 1), L(0)))
    unique_candidate_key = At(At(candidates, 0), 0)
    receipt_match = Exists(N("obs", "has_signature_verification_receipt"), "receipt",
        And(Eq(A("receipt", "status"), L("verified")),
            Eq(A("receipt", "record_key"), unique_candidate_key),
            Eq(A("receipt", "observation_key"), A("q", "observation_key")),
            Eq(A("receipt", "source_epoch"), A("q", "source_epoch"))))
    return {"name": "sr_request_funded_ladder_fallback_on_unverified_miss", "area": AREA, "order": 5,
            "latency_class": "hard_realtime",
            "match": [["ag", "has_similarity_recall_result", "result"],
                      ["result", "recall_for_query", "q"],
                      ["q", "projects_observation", "obs"]],
            "where": And(Eq(A("result", "status"), L("candidate_only")),
                         Or(Not(Eq(A("result", "requires_verification"), L(True))),
                            Not(Eq(At(A("result", "candidate_scan"), 2), L(True))),
                            Not(Eq(Count(zero_hits), L(1))),
                            Not(receipt_match))),
            "effects": [["set_attr", "result", "status", "fallback_required"],
                        ["set_attr", "q", "status", "fallback_required"],
                        ["add_node", "fallback", "SimilarityRecallFallback", {
                            "query_key": T(A("q", "query_key")),
                            "observation_key": T(A("q", "observation_key")),
                            "source_epoch": T(A("q", "source_epoch")),
                            "status": "funded_ladder_required",
                            "funding_required": True,
                        }],
                        ["add_edge", "ag", "has_similarity_recall_fallback", "fallback", {}],
                        ["add_edge", "fallback", "fallback_for_query", "q", {}],
                        ["add_edge", "obs", "has_similarity_recall_fallback", "fallback", {}]]}


def fallback_handoff_rule():
    return {"name": "sr_record_fallback_handoff_to_funded_episode", "area": AREA,
            "order": 6, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_similarity_recall_fallback", "fallback"],
                      ["fallback", "fallback_for_query", "query"],
                      ["query", "projects_observation", "obs"],
                      ["obs", "has_extended_thinking_episode", "episode"]],
            "where": Eq(A("fallback", "status"), L("funded_ladder_required")),
            "effects": [["set_attr", "fallback", "status", "funded_ladder_opened"],
                        ["add_edge", "fallback", "hands_off_to_episode", "episode", {}]]}


def build_seed():
    edges = [("Agent", "has_similarity_recall_policy", "SimilarityRecallPolicy"),
             ("Agent", "has_similarity_query", "CognitionSignatureQuery"),
             ("Agent", "has_cognition_signature", "CognitionSignatureDescriptor"),
             ("Agent", "has_similarity_recall_result", "SimilarityRecallResult"),
             ("Agent", "has_similarity_recall_fallback", "SimilarityRecallFallback"),
             ("SimilarityRecallResult", "recall_for_query", "CognitionSignatureQuery"),
             ("SimilarityRecallResult", "verified_signature", "CognitionSignatureDescriptor"),
             ("SimilarityRecallFallback", "fallback_for_query", "CognitionSignatureQuery"),
             ("CognitionSignatureQuery", "projects_query_source", "CognitionSignatureSource"),
             ("CognitionSignatureQuery", "projects_observation", "Observation"),
             ("Agent", "observed", "Observation"),
             ("Agent", "observed", "ShapeObservation"),
             ("Observation", "has_signature_source", "CognitionSignatureSource"),
             ("ShapeObservation", "has_signature_source", "CognitionSignatureSource"),
             ("Observation", "has_signature_verification_receipt", "CognitionSignatureVerificationReceipt"),
             ("ShapeObservation", "has_signature_verification_receipt", "CognitionSignatureVerificationReceipt"),
             ("CognitionSignatureVerificationReceipt", "verifies_signature", "CognitionSignatureDescriptor"),
             ("Observation", "has_similarity_recall_fallback", "SimilarityRecallFallback"),
             ("SimilarityRecallFallback", "hands_off_to_episode", "ExtendedThinkingEpisode")]
    return {"id": "similarity_recall", "version": "1.0.0", "self_load_only": True,
            "depends_on": ["cognition_signature"], "area": AREA,
            "description": "Bounded exhaustive record-level recall from typed Observation sources. Candidates settle only with a current exact-verification receipt; all other outcomes hand off to the existing funded ladder.",
            "nodes": [{"local_id": 0, "type": "SimilarityRecallPolicy",
                       "attrs": {"name": "similarity_recall_policy", "enabled": 0.0,
                                 "candidate_cap": 256, "k": 8}}],
            "edges": [{"src": {"role": "agent_root"}, "type": "has_similarity_recall_policy",
                       "tgt": {"local": 0}, "attrs": {}, "provenance": "similarity_recall:policy"}],
            "productions": [{"src": {"type": src, "var": "src"}, "edge_type": edge,
                             "tgt": {"type": tgt, "var": "tgt"}, "where": None,
                             "weight": L(1.0), "provenance": f"similarity_recall:{edge}:{src}:{tgt}"}
                            for src, edge, tgt in edges],
            "rules": [project_query_rule(), recall_rule(),
                      verified_shape_outcome_receipt_rule(), exact_verify_rule(),
                      fallback_rule(), fallback_handoff_rule()]}


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__": main()
