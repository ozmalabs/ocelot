#!/usr/bin/env python3
"""Generate P5.E4.3's opt-in imagined-plan arbitration handoff."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "imagined_candidate_arbitration.json"
AREA = "imagined_candidate_arbitration"


def V(n): return {"type": "Var", "name": n}
def L(x): return {"type": "Lit", "value": x}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def T(x): return {"__term__": x}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Exists(source, name, predicate):
    return {"type": "Exists", "source": source, "var_name": name, "predicate": predicate}


def projection(episode, policy, candidate, field):
    return {"type": "FutureManifoldProjection", "episode": V(episode),
            "policy": V(policy), "source": V(candidate), "field": field}


def request_identity():
    return {"type": "StringConcat", "parts": [
        L("imagined:"), A("planner_request", "request_id"),
        L(":"), A("candidate", "path_identity")
    ]}


def reopen_rule():
    native_feasible = And(
        Eq(projection("episode", "manifold_policy", "candidate", "support"), L(1.0)),
        Eq(projection("episode", "manifold_policy", "candidate", "resolved"), L(1.0)),
        Eq(projection("episode", "manifold_policy", "candidate", "loss"), L(0.0)),
        Eq(projection("episode", "manifold_policy", "candidate", "information_loss"), L(0.0)),
        Gte(projection("episode", "manifold_policy", "candidate", "horizon"),
            A("planner_request", "required_horizon")),
    )
    return {
        "name": "ica_reopen_current_feasible_imagined_candidate", "area": AREA,
        "order": 1, "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_imagined_arbitration_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "planner_request"],
                  ["planner_request", "has_imagined_plan_candidate", "candidate"],
                  ["planner_request", "has_dual_process_context", "context"],
                  ["context", "has_system_two_escalation", "escalation"],
                  ["agent", "has_cognition_manifold_policy", "manifold_policy"],
                  ["agent", "has_cognition_manifold_episode", "episode"],
                  ["candidate", "has_terminal_path_arrival", "terminal_arrival"]],
        "where": And(
            Eq(A("policy", "enabled"), L(1.0)),
            Eq(A("planner_request", "status"), L("solved")),
            Eq(A("candidate", "status"), L("proposal")),
            Eq(A("candidate", "provenance_kind"), L("imagined")),
            Eq(A("candidate", "grounding_status"), L("ungrounded")),
            Eq(A("candidate", "observation_status"), L("not_observed")),
            Eq(A("candidate", "arbitration_consumed"), L(0.0)),
            Eq(A("context", "status"), L("escalated")),
            Eq(A("escalation", "status"), L("requested")),
            Eq(A("context", "epoch"), A("planner_request", "source_epoch")),
            Eq(A("context", "active_goal_id"), A("planner_request", "goal_id")),
            Eq(A("context", "active_model_id"), A("planner_request", "model_id")),
            Eq(A("policy", "current_source_epoch"), A("planner_request", "source_epoch")),
            Eq(A("policy", "current_model_id"), A("planner_request", "model_id")),
            Eq(A("policy", "current_model_epoch"), A("planner_request", "model_epoch")),
            Eq(A("policy", "current_goal_id"), A("planner_request", "goal_id")),
            Eq(A("policy", "current_goal_epoch"), A("planner_request", "goal_epoch")),
            Eq(A("policy", "current_manifold_id"), A("planner_request", "manifold_id")),
            Eq(A("policy", "current_manifold_epoch"), A("planner_request", "manifold_epoch")),
            Eq(A("candidate", "model_epoch"), A("planner_request", "model_epoch")),
            Eq(A("candidate", "goal_epoch"), A("planner_request", "goal_epoch")),
            Eq(A("candidate", "manifold_epoch"), A("planner_request", "manifold_epoch")),
            Eq(A("candidate", "first_action_key"), A("terminal_arrival", "root_action_key")),
            native_feasible,
        ),
        "effects": [
            ["add_node", "revision", "SystemTwoDecisionRevision", {
                "status": "reopened", "decision_kind": "imagined_plan",
                "request_id": T(A("planner_request", "request_id")),
                "candidate_id": T(A("candidate", "path_identity")),
                "source_epoch": T(A("planner_request", "source_epoch")),
                "model_id": T(A("planner_request", "model_id")),
                "model_epoch": T(A("planner_request", "model_epoch")),
                "goal_id": T(A("planner_request", "goal_id")),
                "goal_epoch": T(A("planner_request", "goal_epoch")),
                "manifold_id": T(A("planner_request", "manifold_id")),
                "manifold_epoch": T(A("planner_request", "manifold_epoch")),
                "action_key": T(A("candidate", "first_action_key")),
                "path_identity": T(A("candidate", "path_identity")),
                "provenance_kind": "imagined", "grounding_status": "ungrounded",
            }],
            ["add_edge", "planner_request", "has_system_two_decision_revision", "revision", {}],
            ["add_edge", "context", "has_system_two_decision_revision", "revision", {}],
            ["add_edge", "candidate", "has_system_two_decision_revision", "revision", {}],
            ["add_node", "action_request", "ActionRequest", {
                "status": "selected", "request_id": T(request_identity()),
                "source_epoch": T(A("planner_request", "source_epoch")),
                "action_key": T(A("candidate", "first_action_key")),
                "expected_state_key": T(A("candidate", "first_successor_state_key")),
                "candidate_provenance": "imagined", "observation_status": "not_observed",
            }],
            ["add_edge", "agent", "has_action_request", "action_request", {}],
            ["add_edge", "revision", "has_action_request", "action_request", {}],
            ["set_attr", "candidate", "arbitration_consumed", 1.0],
        ],
    }


def cancel_stale_unopened_candidate_rule():
    stale = Or(
        Not(Eq(A("policy", "current_source_epoch"), A("planner_request", "source_epoch"))),
        Not(Eq(A("policy", "current_model_id"), A("planner_request", "model_id"))),
        Not(Eq(A("policy", "current_model_epoch"), A("planner_request", "model_epoch"))),
        Not(Eq(A("policy", "current_goal_id"), A("planner_request", "goal_id"))),
        Not(Eq(A("policy", "current_goal_epoch"), A("planner_request", "goal_epoch"))),
        Not(Eq(A("policy", "current_manifold_id"), A("planner_request", "manifold_id"))),
        Not(Eq(A("policy", "current_manifold_epoch"), A("planner_request", "manifold_epoch"))),
        Not(Eq(A("candidate", "model_epoch"), A("planner_request", "model_epoch"))),
        Not(Eq(A("candidate", "goal_epoch"), A("planner_request", "goal_epoch"))),
        Not(Eq(A("candidate", "manifold_epoch"), A("planner_request", "manifold_epoch"))),
    )
    return {
        "name": "ica_cancel_stale_unopened_candidate", "area": AREA,
        "order": 1, "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_imagined_arbitration_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "planner_request"],
                  ["planner_request", "has_imagined_plan_candidate", "candidate"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("planner_request", "status"), L("solved")),
                      Eq(A("candidate", "status"), L("proposal")),
                      Eq(A("candidate", "arbitration_consumed"), L(0.0)), stale),
        "effects": [["set_attr", "candidate", "status", "cancelled"],
                    ["set_attr", "candidate", "arbitration_consumed", 1.0],
                    ["set_attr", "candidate", "cancellation_reason", "snapshot_changed"]],
    }


def cancel_stale_authorization_rule():
    stale = Or(
        Not(Eq(A("policy", "current_model_epoch"), A("revision", "model_epoch"))),
        Not(Eq(A("policy", "current_goal_epoch"), A("revision", "goal_epoch"))),
        Not(Eq(A("policy", "current_manifold_epoch"), A("revision", "manifold_epoch"))),
        Not(Eq(A("policy", "current_source_epoch"), A("revision", "source_epoch"))),
        Not(Eq(A("policy", "current_model_id"), A("revision", "model_id"))),
        Not(Eq(A("policy", "current_goal_id"), A("revision", "goal_id"))),
        Not(Eq(A("policy", "current_manifold_id"), A("revision", "manifold_id"))),
    )
    return {
        "name": "ica_cancel_stale_action_and_revoke_authorization", "area": AREA,
        "order": 2, "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_imagined_arbitration_policy", "policy"],
                  ["planner_request", "has_system_two_decision_revision", "revision"],
                  ["revision", "has_action_request", "action_request"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("revision", "status"), L("reopened")),
                      Or(Eq(A("action_request", "status"), L("proposed")),
                         Eq(A("action_request", "status"), L("selected")),
                         Eq(A("action_request", "status"), L("authorized"))), stale),
        "effects": [["set_attr", "revision", "status", "cancelled"],
                    ["set_attr", "action_request", "status", "withheld"],
                    ["set_attr", "action_request", "terminal_reason", "snapshot_changed"]],
    }


def revoke_stale_authorization_rule():
    return {
        "name": "ica_revoke_authorization_after_snapshot_change", "area": AREA,
        "order": 3, "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_imagined_arbitration_policy", "policy"],
                  ["agent", "has_action_request", "action_request"],
                  ["action_request", "has_action_authorization", "authorization"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("action_request", "status"), L("withheld")),
                      Eq(A("action_request", "terminal_reason"), L("snapshot_changed")),
                      Eq(A("authorization", "status"), L("pending"))),
        "effects": [["set_attr", "authorization", "status", "revoked"]],
    }


def ground_only_after_observation_rule():
    return {
        "name": "ica_ground_after_matching_sink_receipt_and_observation", "area": AREA,
        "order": 3, "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_imagined_arbitration_policy", "policy"],
                  ["planner_request", "has_imagined_plan_candidate", "candidate"],
                  ["candidate", "has_system_two_decision_revision", "revision"],
                  ["revision", "has_action_request", "action_request"],
                  ["action_request", "has_action_authorization", "authorization"],
                  ["action_request", "has_action_observation", "observation"],
                  ["context", "has_system_two_decision_revision", "revision"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("action_request", "status"), L("emitted")),
                      Eq(A("action_request", "candidate_provenance"), L("imagined")),
                      Eq(A("authorization", "status"), L("consumed")),
                      Eq(A("authorization", "request_id"), A("action_request", "request_id")),
                      Eq(A("authorization", "action_key"), A("action_request", "action_key")),
                      Eq(A("authorization", "source_epoch"), A("action_request", "source_epoch")),
                      Eq(A("observation", "status"), L("verified")),
                      Eq(A("observation", "action_request_id"), A("action_request", "request_id")),
                      Eq(A("observation", "sink_receipt_id"), A("action_request", "sink_receipt_id")),
                      Eq(A("observation", "source_epoch"), A("action_request", "source_epoch")),
                      Eq(A("observation", "observed_state_key"), A("action_request", "expected_state_key")),
                      Eq(A("candidate", "grounding_status"), L("ungrounded"))),
        "effects": [["set_attr", "candidate", "grounding_status", "grounded"],
                    ["set_attr", "candidate", "observation_status", "observed"],
                    ["set_attr", "revision", "status", "observed"],
                    ["set_attr", "revision", "grounding_status", "grounded"],
                    ["set_attr", "context", "status", "committed"],
                    ["set_attr", "context", "route", "system_two"]],
    }


def Or(*xs): return {"type": "Or", "items": list(xs)}


def build_seed():
    return {
        "id": "imagined_candidate_arbitration", "version": "0.1.0",
        "self_load_only": True, "depends_on": [],
        "description": "P5.E4.3 opt-in System-2 reopen and G3 action-request handoff for imagined plans.",
        "microtheory": {"name": AREA, "description": "Current-snapshot arbitration of imagined planner candidates."},
        "nodes": [{"local_id": 0, "type": "ImaginedArbitrationPolicy", "attrs": {
            "enabled": 0.0, "current_source_epoch": -1.0,
            "current_model_id": "", "current_model_epoch": -1.0,
            "current_goal_id": "", "current_goal_epoch": -1.0,
            "current_manifold_id": "", "current_manifold_epoch": -1.0,
        }}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_imagined_arbitration_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": [{
            "provenance": f"{AREA}:{edge}:{src}:{tgt}",
            "src": {"type": src, "var": "src"}, "edge_type": edge,
            "tgt": {"type": tgt, "var": "tgt"},
        } for src, edge, tgt in [
            ("Agent", "has_imagined_arbitration_policy", "ImaginedArbitrationPolicy"),
            ("Agent", "has_action_request", "ActionRequest"),
            ("Agent", "has_cognition_plan_request", "CognitionPlanRequest"),
            ("CognitionPlanRequest", "has_imagined_plan_candidate", "ImaginedPlanCandidate"),
            ("CognitionPlanRequest", "has_dual_process_context", "DualProcessContext"),
            ("DualProcessContext", "has_system_two_escalation", "SystemTwoEscalation"),
            ("Agent", "has_cognition_manifold_policy", "CognitionManifoldPolicy"),
            ("Agent", "has_cognition_manifold_episode", "CognitionManifoldEpisode"),
            ("ImaginedPlanCandidate", "has_terminal_path_arrival", "CognitionPlanPathArrival"),
            ("CognitionPlanPathArrival", "parent_path_arrival", "CognitionPlanPathArrival"),
            ("CognitionPlanPathArrival", "via_transition", "CognitionPlanTransition"),
            ("CognitionPlanRequest", "has_system_two_decision_revision", "SystemTwoDecisionRevision"),
            ("DualProcessContext", "has_system_two_decision_revision", "SystemTwoDecisionRevision"),
            ("ImaginedPlanCandidate", "has_system_two_decision_revision", "SystemTwoDecisionRevision"),
            ("SystemTwoDecisionRevision", "has_action_request", "ActionRequest"),
            ("ActionRequest", "has_action_authorization", "ActionAuthorization"),
            ("ActionRequest", "has_action_observation", "ImaginedActionObservation"),
        ]],
        "rules": [cancel_stale_unopened_candidate_rule(), reopen_rule(),
                  cancel_stale_authorization_rule(),
                  revoke_stale_authorization_rule(), ground_only_after_observation_rule()],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
