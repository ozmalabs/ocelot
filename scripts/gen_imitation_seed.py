#!/usr/bin/env python3
"""Generate the guarded graph-native social demonstration seed (P12.02)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "imitation.json"
AREA = "imitation"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(v): return {"__term__": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Lte(a, b): return {"type": "Lte", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Concat(*xs): return {"type": "StringConcat", "parts": list(xs)}


def build_seed():
    productions = [
        ("Agent", "has_imitation_policy", "ImitationPolicy"),
        ("Agent", "has_social_episode", "SocialEpisode"),
        ("SocialEpisode", "uses_body_frame_map", "SocialBodyFrameMap"),
        ("Agent", "has_imitation_request", "ThinkingBudgetRequest"),
        ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("Agent", "has_demonstrated_candidate", "DemonstratedProcessCandidate"),
        ("DemonstratedProcessCandidate", "from_episode", "SocialEpisode"),
        ("DemonstratedProcessCandidate", "uses_body_frame_map", "SocialBodyFrameMap"),
        ("DemonstratedProcessCandidate", "funded_by", "ThinkingBudgetRequest"),
        ("DemonstratedProcessCandidate", "has_validation_request", "ThinkingBudgetRequest"),
        ("DemonstratedProcessCandidate", "has_own_model_verification", "DetachedOwnModelVerification"),
        ("Agent", "has_process_schema", "ProcessSchema"),
        ("ProcessSchema", "learned_from_demonstration", "DemonstratedProcessCandidate"),
        ("ProcessSchema", "has_own_trial_receipt", "OwnTrialReceipt"),
        ("OwnTrialReceipt", "binds_action_request", "ActionRequest"),
        ("ActionRequest", "has_action_authorization", "ActionAuthorization"),
        ("Agent", "has_demonstrated_process_family", "DemonstratedProcessFamily"),
        ("DemonstratedProcessFamily", "has_source_candidate", "DemonstratedProcessCandidate"),
        ("Agent", "has_binding_replay_request", "DemonstratedBindingReplay"),
        ("DemonstratedBindingReplay", "reuses_demonstrated_family", "DemonstratedProcessFamily"),
        ("DemonstratedBindingReplay", "has_fresh_verification", "DetachedOwnModelVerification"),
        ("DemonstratedBindingReplay", "funded_by", "ThinkingBudgetRequest"),
    ]
    mint = {
        "name": "im_mint_funded_observation_candidate", "area": AREA,
        "order": 1, "latency_class": "soft_realtime", "batch": False,
        "match": [["ag", "has_imitation_policy", "pol"],
                  ["ag", "has_social_episode", "ep"],
                  ["ep", "uses_body_frame_map", "map"],
                  ["ag", "has_imitation_request", "request"],
                  ["request", "draws_on_thinking_budget", "budget"]],
        "where": And(
            Eq(A("pol", "enabled"), L(1.0)),
            Lt({"type": "Count", "source": N("ag", "has_demonstrated_candidate")},
               A("pol", "max_candidates")),
            Eq(A("ep", "status"), L("observed")),
            Eq(A("ep", "observation_status"), L("complete")),
            Eq(A("ep", "source_kind"), L("directed_demonstration")),
            Not(Eq(A("ep", "actor_id"), A("ep", "owner_id"))),
            Not(Eq(A("ep", "action_sequence"), L(None))),
            Lte({"type": "Count", "source": A("ep", "action_sequence")},
                A("pol", "max_steps")),
            Eq(A("map", "status"), L("verified")),
            Eq(A("map", "source_body_id"), A("ep", "actor_body_id")),
            Eq(A("map", "target_body_id"), A("ep", "learner_body_id")),
            Eq(A("map", "source_epoch"), A("ep", "source_epoch")),
            Eq(A("map", "target_frame_epoch"), A("ep", "target_frame_epoch")),
            Eq(A("request", "requester_kind"), L("imitation")),
            Eq(A("request", "episode_id"), A("ep", "episode_id")),
            Eq(A("request", "status"), L("approved")),
            Eq(A("request", "source_epoch"), A("ep", "source_epoch")),
            Not(Eq(A("request", "debited_epoch"), L(None))),
            Not(Exists(N("ag", "has_demonstrated_candidate"), "old",
                        Eq(A("old", "episode_id"), A("ep", "episode_id"))))),
        "effects": [
            ["add_node", "candidate", "DemonstratedProcessCandidate", {
                "candidate_id": T(Concat(L("demo:"), A("ep", "episode_id"))),
                "episode_id": T(A("ep", "episode_id")),
                "owner_id": T(A("ep", "owner_id")),
                "actor_id": T(A("ep", "actor_id")),
                "source_epoch": T(A("ep", "source_epoch")),
                "model_epoch": T(A("ep", "model_epoch")),
                "target_frame_epoch": T(A("ep", "target_frame_epoch")),
                "source_binding_id": T(A("ep", "binding_id")),
                "template_key": T(A("ep", "template_key")),
                "action_sequence": T(A("ep", "action_sequence")),
                "status": "unverified_candidate",
                "provenance": "ordered_directed_observation",
                "effect_evaluation": "unverified_observed_sequence"}],
            ["add_edge", "ag", "has_demonstrated_candidate", "candidate", {}],
            ["add_edge", "candidate", "from_episode", "ep", {}],
            ["add_edge", "candidate", "uses_body_frame_map", "map", {}],
            ["add_edge", "candidate", "funded_by", "request", {}],
            ["set_attr", "request", "terminal_status", "completed"]],
    }
    reject = {
        "name": "im_reject_failed_own_model_rollout", "area": AREA,
        "order": 2, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_demonstrated_candidate", "candidate"],
                  ["candidate", "has_own_model_verification", "receipt"],
                  ["candidate", "has_validation_request", "request"],
                  ["request", "draws_on_thinking_budget", "budget"]],
        "where": And(Eq(A("candidate", "status"), L("unverified_candidate")),
                     Eq(A("receipt", "candidate_id"), A("candidate", "candidate_id")),
                     Eq(A("receipt", "verification_kind"), L("detached_own_model_rollout")),
                     Eq(A("receipt", "status"), L("failed")),
                     Eq(A("receipt", "source_epoch"), A("candidate", "source_epoch")),
                     Eq(A("request", "requester_kind"), L("imitation_validation")),
                     Eq(A("request", "candidate_id"), A("candidate", "candidate_id")),
                     Eq(A("request", "source_epoch"), A("candidate", "source_epoch")),
                     Eq(A("request", "status"), L("approved")),
                     Not(Eq(A("request", "debited_epoch"), L(None)))),
        "effects": [["set_attr", "candidate", "status", "rejected"],
                    ["set_attr", "candidate", "rejection_reason", "own_model_rollout_failed"],
                    ["set_attr", "request", "terminal_status", "completed"]],
    }
    adopt = {
        "name": "im_adopt_only_current_detached_verified_candidate", "area": AREA,
        "order": 3, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_imitation_policy", "pol"],
                  ["ag", "has_demonstrated_candidate", "candidate"],
                  ["candidate", "has_own_model_verification", "receipt"],
                  ["candidate", "uses_body_frame_map", "map"],
                  ["candidate", "has_validation_request", "request"],
                  ["request", "draws_on_thinking_budget", "budget"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("candidate", "status"), L("unverified_candidate")),
                     Eq(A("receipt", "candidate_id"), A("candidate", "candidate_id")),
                     Eq(A("receipt", "verification_kind"), L("detached_own_model_rollout")),
                     Eq(A("receipt", "status"), L("verified")),
                     Eq(A("receipt", "owner_id"), A("candidate", "owner_id")),
                     Eq(A("receipt", "source_epoch"), A("candidate", "source_epoch")),
                     Eq(A("receipt", "model_epoch"), A("candidate", "model_epoch")),
                     Eq(A("receipt", "frame_epoch"), A("candidate", "target_frame_epoch")),
                     Eq(A("request", "requester_kind"), L("imitation_validation")),
                     Eq(A("request", "candidate_id"), A("candidate", "candidate_id")),
                     Eq(A("request", "source_epoch"), A("candidate", "source_epoch")),
                     Eq(A("request", "status"), L("approved")),
                     Not(Eq(A("request", "debited_epoch"), L(None))),
                     Eq(A("map", "status"), L("verified")),
                     Eq(A("map", "source_epoch"), A("candidate", "source_epoch")),
                     Eq(A("map", "target_frame_epoch"), A("candidate", "target_frame_epoch"))),
        "effects": [["add_node", "schema", "ProcessSchema", {
            "name": T(Concat(L("demonstrated:"), A("candidate", "candidate_id"))),
            "kind": "sequence", "domain": T(A("candidate", "template_key")),
            "params": T(A("candidate", "action_sequence")),
            "status": "active", "provenance": "own_model_verified_demonstration",
            "effect_evaluation": "detached_own_model_rollout",
            "source_epoch": T(A("candidate", "source_epoch")),
            "model_epoch": T(A("candidate", "model_epoch")),
            "frame_epoch": T(A("candidate", "target_frame_epoch")),
            "grounding_status": "model_verified_not_own_trial",
            "verification_receipt": T(A("receipt", "receipt_id"))}],
                    ["add_edge", "ag", "has_process_schema", "schema", {}],
                    ["add_edge", "schema", "learned_from_demonstration", "candidate", {}],
                    ["set_attr", "candidate", "status", "adopted"],
                    ["set_attr", "request", "terminal_status", "completed"]],
    }
    ground = {
        "name": "im_ground_only_from_actual_current_own_trial", "area": AREA,
        "order": 4, "latency_class": "hard_realtime", "batch": False,
        "match": [["schema", "has_own_trial_receipt", "receipt"],
                  ["receipt", "binds_action_request", "action_request"],
                  ["ag", "has_action_request", "action_request"],
                  ["action_request", "has_action_authorization", "authorization"]],
        "where": And(Eq(A("schema", "provenance"), L("own_model_verified_demonstration")),
                     Eq(A("receipt", "status"), L("observed")),
                     Eq(A("receipt", "actual_own_trial"), L(True)),
                     Eq(A("action_request", "actor_id"), A("receipt", "owner_id")),
                     Eq(A("action_request", "status"), L("emitted")),
                     Eq(A("authorization", "status"), L("consumed")),
                     Eq(A("authorization", "request_id"), A("action_request", "request_id")),
                     Eq(A("authorization", "source_epoch"), A("receipt", "source_epoch")),
                     Eq(A("action_request", "source_epoch"), A("receipt", "source_epoch")),
                     Eq(A("action_request", "sink_receipt_id"), A("receipt", "sink_receipt_id")),
                     Not(Eq(A("receipt", "sink_receipt_id"), L(None))),
                     Eq(A("receipt", "owner_id"), A("receipt", "learner_body_owner_id")),
                     Eq(A("receipt", "source_epoch"), A("schema", "source_epoch")),
                     Eq(A("receipt", "model_epoch"), A("schema", "model_epoch")),
                     Eq(A("receipt", "frame_epoch"), A("schema", "frame_epoch"))),
        "effects": [["set_attr", "schema", "grounding_status", "own_trial_grounded"],
                    ["set_attr", "schema", "own_trial_receipt_id", T(A("receipt", "receipt_id"))]],
    }
    family = {
        "name": "im_retain_repeated_verified_template_family", "area": AREA,
        "order": 5, "latency_class": "soft_realtime", "batch": False,
        "match": [["ag", "has_demonstrated_candidate", "a"],
                  ["ag", "has_demonstrated_candidate", "b"]],
        "where": And(Lt(V("a"), V("b")),
                     Eq(A("a", "status"), L("adopted")),
                     Eq(A("b", "status"), L("adopted")),
                     Eq(A("a", "template_key"), A("b", "template_key")),
                     Not(Eq(A("a", "source_binding_id"), A("b", "source_binding_id"))),
                     Not(Exists(N("ag", "has_demonstrated_process_family"), "old",
                                Eq(A("old", "template_key"), A("a", "template_key"))))),
        "effects": [["add_node", "family", "DemonstratedProcessFamily", {
            "family_id": T(Concat(L("demo-family:"), A("a", "template_key"))),
            "template_key": T(A("a", "template_key")),
            "action_template": T(A("a", "action_sequence")),
            "source_binding_a": T(A("a", "source_binding_id")),
            "source_binding_b": T(A("b", "source_binding_id")),
            "status": "verified_family", "witness_count": 2}],
                    ["add_edge", "ag", "has_demonstrated_process_family", "family", {}],
                    ["add_edge", "family", "has_source_candidate", "a", {}],
                    ["add_edge", "family", "has_source_candidate", "b", {}]],
    }
    replay = {
        "name": "im_instantiate_verified_family_on_fresh_binding", "area": AREA,
        "order": 6, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_imitation_policy", "pol"],
                  ["ag", "has_binding_replay_request", "replay"],
                  ["replay", "reuses_demonstrated_family", "family"],
                  ["replay", "has_fresh_verification", "receipt"],
                  ["replay", "funded_by", "request"],
                  ["request", "draws_on_thinking_budget", "budget"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("family", "status"), L("verified_family")),
                     Eq(A("replay", "status"), L("requested")),
                     Eq(A("request", "requester_kind"), L("imitation_binding_replay")),
                     Eq(A("request", "replay_id"), A("replay", "replay_id")),
                     Eq(A("request", "source_epoch"), A("receipt", "source_epoch")),
                     Eq(A("request", "status"), L("approved")),
                     Not(Eq(A("request", "debited_epoch"), L(None))),
                     Eq(A("replay", "template_key"), A("family", "template_key")),
                     Not(Eq(A("replay", "binding_id"), A("family", "source_binding_a"))),
                     Not(Eq(A("replay", "binding_id"), A("family", "source_binding_b"))),
                     Eq(A("receipt", "status"), L("verified")),
                     Eq(A("receipt", "verification_kind"), L("detached_own_model_rollout")),
                     Eq(A("receipt", "candidate_id"), A("replay", "replay_id")),
                     Eq(A("receipt", "owner_id"), A("replay", "owner_id")),
                     Eq(A("receipt", "model_epoch"), A("replay", "model_epoch")),
                     Eq(A("receipt", "frame_epoch"), A("replay", "frame_epoch"))),
        "effects": [["add_node", "schema", "ProcessSchema", {
            "name": T(Concat(L("demonstrated-replay:"), A("replay", "replay_id"))),
            "kind": "sequence", "domain": T(A("replay", "template_key")),
            "params": T(A("family", "action_template")),
            "binding_id": T(A("replay", "binding_id")),
            "status": "active", "provenance": "verified_unseen_demo_binding",
            "effect_evaluation": "fresh_binding_detached_rollout",
            "source_epoch": T(A("receipt", "source_epoch")),
            "model_epoch": T(A("replay", "model_epoch")),
            "frame_epoch": T(A("replay", "frame_epoch")),
            "grounding_status": "model_verified_not_own_trial",
            "verification_receipt": T(A("receipt", "receipt_id"))}],
                    ["add_edge", "ag", "has_process_schema", "schema", {}],
                    ["set_attr", "replay", "status", "verified"],
                    ["set_attr", "request", "terminal_status", "completed"]],
    }
    nodes = [
        {"local_id": 0, "type": "ImitationPolicy", "attrs": {
            "name": "imitation_policy", "enabled": 0.0,
            "max_steps": 32.0, "max_candidates": 16.0}},
    ]
    return {"id": "imitation", "version": "1.0.0", "depends_on": ["process_schema", "response_inhibition"],
            "self_load_only": True, "area": AREA,
            "description": "Bounded social demonstration candidates; require own-model validation and keep own-trial grounding separate.",
            "microtheory": {"name": AREA, "description": "Attribute observed actions, verify in the learner model, and preserve own-trial evidence."},
            "nodes": nodes,
            "edges": [{"src": {"role": "agent_root"}, "type": "has_imitation_policy", "tgt": {"local": 0}, "attrs": {}}],
            "productions": [{"provenance": f"seed:{AREA}:{src}:{edge}:{tgt}", "src": {"type": src, "var": "src"},
                             "edge_type": edge, "tgt": {"type": tgt, "var": "tgt"}} for src, edge, tgt in productions],
            "rules": [mint, reject, adopt, ground, family, replay]}


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)
