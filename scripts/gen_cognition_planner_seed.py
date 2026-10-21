#!/usr/bin/env python3
"""Generate the opt-in graph-resident P5 bounded planner seed (E4.2)."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from gen_capability_collapse_seed import A, And, Eq, Filter, Gte, Gt, L, N, Not, Plus, T, V, ZERO

OUT = ROOT / "seeds" / "cognition_planner.json"
AREA = "cognition_planner"


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def Exists(source, var_name, predicate):
    return {"type": "Exists", "source": source, "var_name": var_name, "predicate": predicate}


def Or(*items):
    return {"type": "Or", "items": list(items)}


def Min(*items):
    return {"type": "Min", "items": list(items)}


def Argmin(source, var_name, value, default=None):
    return {"type": "Argmin", "source": source, "var_name": var_name,
            "value": value, "default": default if default is not None else L(None)}


def ready_frontiers():
    return Filter(N("request", "has_frontier"), "ready_frontier",
                  Eq(A("ready_frontier", "status"), L("ready")))


def Or(*items):
    return {"type": "Or", "items": list(items)}


def production_specs():
    return [
        ("Agent", "has_cognition_planner_policy", "CognitionPlannerPolicy"),
        ("Agent", "has_cognition_plan_request", "CognitionPlanRequest"),
        ("Agent", "has_cognition_plan_transition", "CognitionPlanTransition"),
        ("Agent", "has_cognition_manifold_episode", "CognitionManifoldEpisode"),
        ("Agent", "has_transition_hypothesis", "TransitionHypothesis"),
        ("Agent", "has_thinking_budget", "ThinkingBudget"),
        ("Agent", "has_network_mode_state", "NetworkModeState"),
        ("CognitionPlanRequest", "has_start_state", "CognitionPlanState"),
        ("CognitionPlanRequest", "has_goal_state", "CognitionPlanState"),
        ("CognitionPlanRequest", "has_model_start_state", "BeliefState"),
        ("CognitionPlanRequest", "has_model_start_state", "PredictedBeliefState"),
        ("CognitionPlanRequest", "has_model_goal_state", "PredictedBeliefState"),
        ("CognitionPlanState", "represents_model_state", "BeliefState"),
        ("CognitionPlanState", "represents_model_state", "PredictedBeliefState"),
        ("PredictedBeliefState", "predicted_from_belief", "BeliefState"),
        ("PredictedBeliefState", "predicted_from_belief", "PredictedBeliefState"),
        ("PredictedBeliefState", "generated_by_transition", "TransitionHypothesis"),
        ("CognitionManifoldEpisode", "has_cognition_manifold_candidate", "CognitionManifoldCandidate"),
        ("CognitionManifoldCandidate", "projects_transition", "TransitionHypothesis"),
        ("CognitionManifoldCandidate", "projects_predicted_state", "PredictedBeliefState"),
        ("CognitionManifoldCandidate", "has_feasibility_receipt", "CognitionManifoldFeasibilityReceipt"),
        ("CognitionPlanState", "has_feasibility_receipt", "CognitionManifoldFeasibilityReceipt"),
        ("CognitionPlanTransition", "has_feasibility_receipt", "CognitionManifoldFeasibilityReceipt"),
        ("CognitionPlanRequest", "has_frontier", "CognitionPlanFrontier"),
        ("CognitionPlanFrontier", "has_parent_frontier", "CognitionPlanFrontier"),
        ("CognitionPlanFrontier", "uses_transition", "CognitionPlanTransition"),
        ("CognitionPlanFrontier", "has_expansion_budget_request", "ThinkingBudgetRequest"),
        ("CognitionPlanFrontier", "expands_from_state", "CognitionPlanState"),
        ("CognitionPlanFrontier", "reaches_state", "CognitionPlanState"),
        ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("CognitionPlanRequest", "has_imagined_plan_candidate", "ImaginedPlanCandidate"),
        ("ImaginedPlanCandidate", "derived_from_frontier", "CognitionPlanFrontier"),
        ("ImaginedPlanCandidate", "via_transition", "CognitionPlanTransition"),
    ]


def productions():
    return [{"provenance": f"seed:cognition_planner:{edge}:{src}:{tgt}",
             "src": {"type": src, "var": "src"}, "edge_type": edge,
             "tgt": {"type": tgt, "var": "tgt"}}
            for src, edge, tgt in production_specs()]


def verified_receipt(receipt, request, transition=None, state=None):
    checks = [
        Eq(A(receipt, "status"), L("verified")),
        Eq(A(receipt, "verifier_kind"), L("native_future_manifold_projection")),
        Eq(A(receipt, "model_id"), A(request, "model_id")),
        Eq(A(receipt, "model_epoch"), A(request, "model_epoch")),
        Gte(A(receipt, "horizon"), A(request, "required_horizon")),
        Eq(A(receipt, "projection_loss"), ZERO),
        Eq(A(receipt, "projection_information_loss"), ZERO),
    ]
    if transition:
        checks.extend([
            Eq(A(receipt, "transition_id"), A(transition, "transition_id")),
            Eq(A(transition, "model_id"), A(request, "model_id")),
        ])
    if state:
        checks.extend([
            Eq(A(receipt, "projection_version"), A(state, "projection_version")),
            Eq(A(state, "model_id"), A(request, "model_id")),
        ])
    return And(*checks)


def state_has_verified_projection(state, request):
    return Exists(N(state, "has_feasibility_receipt"), "projection_receipt",
                  verified_receipt("projection_receipt", request, state=state))




def terminalize_prebind_stale_request_rule():
    stale = Or(
        Not(Eq(A("request", "source_epoch"), A("mode", "epoch"))),
        Not(Eq(A("request", "model_epoch"), A("policy", "current_model_epoch"))),
        Not(Eq(A("request", "goal_epoch"), A("policy", "current_goal_epoch"))),
        Not(Eq(A("request", "manifold_epoch"), A("policy", "current_manifold_epoch"))),
        Not(Eq(A("request", "model_id"), A("policy", "current_model_id"))),
        Not(Eq(A("request", "goal_id"), A("policy", "current_goal_id"))),
        Not(Eq(A("request", "manifold_id"), A("policy", "current_manifold_id"))),
    )
    return {
        "name": "cp_cancel_prebind_stale_request", "area": AREA, "order": 16,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["agent", "has_network_mode_state", "mode"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("pending")),
                      Not(Gt(A("mode", "epoch"), A("request", "deadline_epoch"))),
                      stale),
        "effects": [["set_attr", "request", "status", "model_stale"],
                    ["set_attr", "request", "terminal_reason", "planning_epoch_changed"]],
    }


def bind_model_start_state_rule():
    return {
        "name": "cp_bind_model_start_state", "area": AREA, "order": 17,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["agent", "has_network_mode_state", "mode"],
                  ["request", "has_model_start_state", "model_start"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("pending")),
                      Eq(A("request", "source_epoch"), A("mode", "epoch")),
                      Eq(A("request", "model_epoch"), A("policy", "current_model_epoch")),
                      Eq(A("request", "goal_epoch"), A("policy", "current_goal_epoch")),
                      Eq(A("request", "manifold_epoch"), A("policy", "current_manifold_epoch")),
                      Eq(A("request", "model_id"), A("policy", "current_model_id")),
                      Eq(A("request", "goal_id"), A("policy", "current_goal_id")),
                      Eq(A("request", "manifold_id"), A("policy", "current_manifold_id")),
                      Eq({"type": "Count", "source": N("request", "has_start_state")}, ZERO)),
        "effects": [
            ["add_node", "start", "CognitionPlanState", {
                "state_key": T(V("model_start")),
                "owner_id": T(A("request", "owner_id")),
                "model_id": T(A("request", "model_id")),
                "model_epoch": T(A("request", "model_epoch")),
                "goal_epoch": T(A("request", "goal_epoch")),
                "uncertainty": T(A("model_start", "uncertainty")),
            }],
            ["add_edge", "request", "has_start_state", "start", {}],
            ["add_edge", "start", "represents_model_state", "model_start", {}],
            ["set_attr", "request", "start_state_id", T(V("model_start"))],
        ],
    }


def bind_model_goal_state_rule():
    return {
        "name": "cp_bind_model_goal_state", "area": AREA, "order": 18,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["agent", "has_cognition_manifold_episode", "episode"],
                  ["request", "has_model_goal_state", "model_goal"],
                  ["episode", "has_cognition_manifold_candidate", "candidate"],
                  ["candidate", "projects_predicted_state", "model_goal"],
                  ["candidate", "projects_transition", "model_transition"],
                  ["candidate", "has_feasibility_receipt", "receipt"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("pending")),
                      Eq(A("candidate", "status"), L("audited")),
                      Eq(A("request", "model_epoch"), A("policy", "current_model_epoch")),
                      Eq(A("request", "goal_epoch"), A("policy", "current_goal_epoch")),
                      Eq(A("request", "manifold_epoch"), A("policy", "current_manifold_epoch")),
                      Eq(A("request", "model_id"), A("policy", "current_model_id")),
                      Eq(A("request", "goal_id"), A("policy", "current_goal_id")),
                      Eq(A("request", "manifold_id"), A("policy", "current_manifold_id")),
                      verified_receipt("receipt", "request", "model_transition", "candidate"),
                      Eq({"type": "Count", "source": N("request", "has_goal_state")}, ZERO)),
        "effects": [
            ["add_node", "goal", "CognitionPlanState", {
                "state_key": T(V("model_goal")),
                "owner_id": T(A("request", "owner_id")),
                "model_id": T(A("request", "model_id")),
                "model_epoch": T(A("request", "model_epoch")),
                "goal_id": T(A("request", "goal_id")),
                "goal_epoch": T(A("request", "goal_epoch")),
                "projection_version": T(A("candidate", "projection_version")),
                "uncertainty": T(A("model_goal", "uncertainty")),
            }],
            ["add_edge", "request", "has_goal_state", "goal", {}],
            ["add_edge", "goal", "represents_model_state", "model_goal", {}],
            ["add_edge", "goal", "has_feasibility_receipt", "receipt", {}],
        ],
    }


def adapt_native_model_transition_rule():
    known = Exists(
        N("agent", "has_cognition_plan_transition"), "known_transition",
        And(Eq(A("known_transition", "transition_id"), A("model_transition", "transition_id")),
            Eq(A("known_transition", "source_state_key"), V("model_source")),
            Eq(A("known_transition", "model_id"), A("request", "model_id")),
            Eq(A("known_transition", "model_epoch"), A("request", "model_epoch")),
            Eq(A("known_transition", "owner_id"), A("request", "owner_id")),
            Eq(A("known_transition", "goal_id"), A("request", "goal_id")),
            Eq(A("known_transition", "goal_epoch"), A("request", "goal_epoch")),
            Eq(A("known_transition", "manifold_id"), A("request", "manifold_id")),
            Eq(A("known_transition", "manifold_epoch"), A("request", "manifold_epoch"))),
    )
    return {
        "name": "cp_adapt_verified_native_model_transition", "area": AREA, "order": 21,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["agent", "has_cognition_manifold_episode", "episode"],
                  ["request", "has_frontier", "frontier"],
                  ["frontier", "expands_from_state", "source_plan_state"],
                  ["source_plan_state", "represents_model_state", "model_source"],
                  ["episode", "has_cognition_manifold_candidate", "candidate"],
                  ["candidate", "projects_transition", "model_transition"],
                  ["candidate", "projects_predicted_state", "model_successor"],
                  ["candidate", "has_feasibility_receipt", "receipt"],
                  ["model_successor", "predicted_from_belief", "model_source"],
                  ["model_successor", "generated_by_transition", "model_transition"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("candidate", "status"), L("audited")),
                      Eq(A("request", "model_id"), A("policy", "current_model_id")),
                      Eq(A("request", "model_epoch"), A("policy", "current_model_epoch")),
                      Eq(A("request", "goal_id"), A("policy", "current_goal_id")),
                      Eq(A("request", "goal_epoch"), A("policy", "current_goal_epoch")),
                      Eq(A("request", "manifold_id"), A("policy", "current_manifold_id")),
                      Eq(A("request", "manifold_epoch"), A("policy", "current_manifold_epoch")),
                      Eq(A("model_transition", "model_id"), A("request", "model_id")),
                      Eq(A("model_transition", "model_epoch"), A("request", "model_epoch")),
                      verified_receipt("receipt", "request", "model_transition", "candidate"),
                      Not(known)),
        "effects": [
            ["add_node", "successor", "CognitionPlanState", {
                "state_key": T(V("model_successor")),
                "owner_id": T(A("request", "owner_id")),
                "model_id": T(A("request", "model_id")),
                "model_epoch": T(A("request", "model_epoch")),
                "goal_epoch": T(A("request", "goal_epoch")),
                "projection_version": T(A("candidate", "projection_version")),
                "uncertainty": T(A("model_successor", "uncertainty")),
            }],
            ["add_edge", "successor", "represents_model_state", "model_successor", {}],
            ["add_edge", "successor", "has_feasibility_receipt", "receipt", {}],
            ["add_node", "planner_transition", "CognitionPlanTransition", {
                "transition_id": T(A("model_transition", "transition_id")),
                "source_state_key": T(V("model_source")),
                "action_key": T(A("model_transition", "action_kind")),
                "model_id": T(A("request", "model_id")),
                "model_epoch": T(A("request", "model_epoch")),
                "owner_id": T(A("request", "owner_id")),
                "goal_id": T(A("request", "goal_id")),
                "goal_epoch": T(A("request", "goal_epoch")),
                "manifold_id": T(A("request", "manifold_id")),
                "manifold_epoch": T(A("request", "manifold_epoch")),
                "uncertainty": T(A("model_successor", "uncertainty")),
            }],
            ["add_edge", "agent", "has_cognition_plan_transition", "planner_transition", {}],
            ["add_edge", "planner_transition", "has_feasibility_receipt", "receipt", {}],
            ["add_edge", "planner_transition", "has_successor_state", "successor", {}],
        ],
    }



def terminalize_unbound_model_request_rule():
    missing = Or(Eq({"type": "Count", "source": N("request", "has_start_state")}, ZERO),
                 Eq({"type": "Count", "source": N("request", "has_goal_state")}, ZERO))
    return {
        "name": "cp_close_unbound_model_request", "area": AREA, "order": 19,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["agent", "has_network_mode_state", "mode"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("pending")),
                      Eq(A("request", "source_epoch"), A("mode", "epoch")),
                      Eq(A("request", "model_epoch"), A("policy", "current_model_epoch")),
                      Eq(A("request", "goal_epoch"), A("policy", "current_goal_epoch")),
                      Eq(A("request", "manifold_epoch"), A("policy", "current_manifold_epoch")),
                      missing),
        "effects": [["set_attr", "request", "status", "unknown"],
                    ["set_attr", "request", "terminal_reason", "missing_model_state_or_goal_projection"]],
    }


def terminalize_stale_request_rule():
    stale = Or(Eq(A("request", "source_epoch"), L(None)),
               Not(Eq(A("request", "source_epoch"), A("mode", "epoch"))),
               Not(Eq(A("request", "model_epoch"), A("policy", "current_model_epoch"))),
               Not(Eq(A("request", "goal_epoch"), A("policy", "current_goal_epoch"))),
               Not(Eq(A("request", "manifold_epoch"), A("policy", "current_manifold_epoch"))),
               Not(Eq(A("request", "model_epoch"), A("start", "model_epoch"))),
               Not(Eq(A("request", "goal_epoch"), A("goal", "goal_epoch"))),
               Not(Eq(A("request", "model_id"), A("policy", "current_model_id"))),
               Not(Eq(A("request", "goal_id"), A("policy", "current_goal_id"))),
               Not(Eq(A("request", "manifold_id"), A("policy", "current_manifold_id"))),
               Not(Eq(A("request", "owner_id"), A("start", "owner_id"))),
               Not(Eq(A("request", "owner_id"), A("goal", "owner_id"))),
               Not(Eq(A("request", "start_state_id"), A("start", "state_key"))))
    return {
        "name": "cp_cancel_stale_request", "area": AREA, "order": 19,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_start_state", "start"],
                  ["request", "has_goal_state", "goal"],
                  ["agent", "has_network_mode_state", "mode"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Or(Eq(A("request", "status"), L("pending")),
                         Eq(A("request", "status"), L("searching"))),
                      Not(Gt(A("mode", "epoch"), A("request", "deadline_epoch"))),
                      stale),
        "effects": [["set_attr", "request", "status", "model_stale"],
                    ["set_attr", "request", "terminal_reason", "planning_epoch_changed"]],
    }


def terminalize_deadline_rule():
    return {
        "name": "cp_cancel_expired_request", "area": AREA, "order": 9,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["agent", "has_network_mode_state", "mode"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Or(Eq(A("request", "status"), L("pending")),
                         Eq(A("request", "status"), L("searching"))),
                      Gt(A("mode", "epoch"), A("request", "deadline_epoch"))),
        "effects": [["set_attr", "request", "status", "exhausted"],
                    ["set_attr", "request", "terminal_reason", "deadline_exceeded"]],
    }



def root_rule():
    return {
        "name": "cp_materialize_root_frontier", "area": AREA, "order": 20,
        "latency_class": "soft_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_start_state", "start"],
                  ["request", "has_goal_state", "goal"],
                  ["agent", "has_network_mode_state", "mode"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("pending")),
                      Eq(A("request", "source_epoch"), A("mode", "epoch")),
                      Eq(A("request", "model_epoch"), A("start", "model_epoch")),
                      Eq(A("request", "goal_epoch"), A("goal", "goal_epoch")),
                      Eq(A("request", "model_epoch"), A("policy", "current_model_epoch")),
                      Eq(A("request", "goal_epoch"), A("policy", "current_goal_epoch")),
                      Eq(A("request", "manifold_epoch"), A("policy", "current_manifold_epoch")),
                      Eq(A("request", "model_id"), A("policy", "current_model_id")),
                      Eq(A("request", "goal_id"), A("policy", "current_goal_id")),
                      Eq(A("request", "manifold_id"), A("policy", "current_manifold_id")),
                      Eq(A("request", "goal_id"), A("goal", "goal_id")),
                      Eq(A("request", "owner_id"), A("start", "owner_id")),
                      Eq(A("request", "owner_id"), A("goal", "owner_id")),
                      Eq(A("request", "start_state_id"), A("start", "state_key")),
                      Eq({"type": "Count", "source": N("request", "has_frontier")}, ZERO)),
        "effects": [
            ["add_node", "frontier", "CognitionPlanFrontier", {
                "status": "ready", "expanded_counted": 0.0,
                "candidate_emitted": 0.0, "depth": 0.0, "rank": 0.0,
                "state_key": T(A("start", "state_key")),
                "model_epoch": T(A("request", "model_epoch")),
                "goal_epoch": T(A("request", "goal_epoch")),
                "manifold_epoch": T(A("request", "manifold_epoch")),
                "source_epoch": T(A("request", "source_epoch")),
                "goal_state_key": T(A("goal", "state_key")),
                "uncertainty": T(A("start", "uncertainty")),
            }],
            ["add_edge", "request", "has_frontier", "frontier", {}],
            ["add_edge", "frontier", "expands_from_state", "start", {}],
            ["set_attr", "request", "status", "searching"],
            ["set_attr", "request", "goal_state_key", T(A("goal", "state_key"))],
            ["set_attr", "request", "expanded_count", 0.0],
        ],
    }


def budget_request_rule():
    return {
        "name": "cp_request_expansion_budget", "area": AREA, "order": 21,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_frontier", "frontier"],
                  ["agent", "has_thinking_budget", "budget"],
                  ["agent", "has_network_mode_state", "mode"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("frontier", "source_epoch"), A("mode", "epoch")),
                      Lt(A("frontier", "depth"), Min(A("request", "depth_limit"), A("policy", "maximum_depth"))),
                      Lt(A("request", "expanded_count"), Min(A("request", "expansion_limit"), A("policy", "maximum_expansions"))),
                      Eq(V("frontier"), Argmin(ready_frontiers(), "ranked_frontier",
                                                A("ranked_frontier", "rank"), default=L(None))),
                      Eq({"type": "Count", "source": N("frontier", "has_expansion_budget_request")}, ZERO)),
        "effects": [
            ["add_node", "budget_req", "ThinkingBudgetRequest", {
                "status": "pending", "requester_kind": "cognition_planner",
                "cost": T(A("policy", "expansion_cost")),
                "source_epoch": T(A("mode", "epoch")),
                "deadline_epoch": T(A("request", "deadline_epoch")),
                "request_id": T(A("frontier", "state_key")),
            }],
            ["add_edge", "frontier", "has_expansion_budget_request", "budget_req", {}],
            ["add_edge", "budget_req", "draws_on_thinking_budget", "budget", {}],
        ],
    }


def expand_rule():
    duplicate_state = Exists(
        N("request", "has_frontier"), "seen",
        And(Eq(A("seen", "state_key"), A("successor", "state_key")),
            Eq(A("seen", "model_epoch"), A("request", "model_epoch")),
            Eq(A("seen", "goal_epoch"), A("request", "goal_epoch"))),
    )
    return {
        "name": "cp_expand_funded_frontier", "area": AREA, "order": 22,
        "latency_class": "soft_realtime", "batch": True,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_frontier", "frontier"],
                  ["frontier", "has_expansion_budget_request", "budget_req"],
                  ["agent", "has_cognition_plan_transition", "transition"],
                  ["transition", "has_feasibility_receipt", "receipt"],
                  ["transition", "has_successor_state", "successor"],
                  ["successor", "has_feasibility_receipt", "receipt"],
                  ["frontier", "expands_from_state", "source"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("budget_req", "status"), L("approved")),
                      Eq(V("frontier"), Argmin(ready_frontiers(), "ranked_frontier",
                                                A("ranked_frontier", "rank"), default=L(None))),
                      Eq(A("source", "state_key"), A("transition", "source_state_key")),
                      Eq(A("transition", "model_epoch"), A("request", "model_epoch")),
                      verified_receipt("receipt", "request", "transition", "successor"),
                      Eq(A("successor", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("request", "model_epoch"), A("policy", "current_model_epoch")),
                      Eq(A("request", "goal_epoch"), A("policy", "current_goal_epoch")),
                      Eq(A("request", "manifold_epoch"), A("policy", "current_manifold_epoch")),
                      Eq(A("request", "model_id"), A("policy", "current_model_id")),
                      Eq(A("request", "goal_id"), A("policy", "current_goal_id")),
                      Eq(A("request", "manifold_id"), A("policy", "current_manifold_id")),
                      Lt(A("frontier", "depth"), Min(A("request", "depth_limit"), A("policy", "maximum_depth"))),
                      Lt(A("request", "expanded_count"), Min(A("request", "expansion_limit"), A("policy", "maximum_expansions"))),
                      Not(duplicate_state)),
        "effects": [
            ["add_node", "child", "CognitionPlanFrontier", {
                "status": "ready", "expanded_counted": 0.0,
                "candidate_emitted": 0.0,
                "depth": T(Plus(A("frontier", "depth"), L(1.0))),
                "rank": T(Plus(A("request", "expanded_count"), L(1.0))),
                "state_key": T(A("successor", "state_key")),
                "model_epoch": T(A("request", "model_epoch")),
                "goal_epoch": T(A("request", "goal_epoch")),
                "manifold_epoch": T(A("request", "manifold_epoch")),
                "source_epoch": T(A("request", "source_epoch")),
                "goal_state_key": T(A("frontier", "goal_state_key")),
                "uncertainty": T(A("successor", "uncertainty")),
            }],
            ["add_edge", "request", "has_frontier", "child", {}],
            ["add_edge", "child", "has_parent_frontier", "frontier", {}],
            ["add_edge", "child", "uses_transition", "transition", {}],
            ["add_edge", "child", "expands_from_state", "successor", {}],
            ["set_attr", "frontier", "status", "expanded"],
            ["set_attr", "frontier", "expanded_epoch", T(A("budget_req", "debited_epoch"))],
        ],
    }


def preserve_duplicate_state_path_rule():
    known_arrival = Exists(
        N("existing", "has_parent_frontier"), "known_parent",
        And(Eq(V("known_parent"), V("frontier")),
            Exists(N("existing", "uses_transition"), "known_transition",
                   Eq(V("known_transition"), V("transition")))),
    )
    return {
        "name": "cp_preserve_duplicate_state_path", "area": AREA, "order": 22,
        "latency_class": "soft_realtime", "batch": True,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_frontier", "frontier"],
                  ["request", "has_frontier", "existing"],
                  ["frontier", "has_expansion_budget_request", "budget_req"],
                  ["frontier", "expands_from_state", "source"],
                  ["agent", "has_cognition_plan_transition", "transition"],
                  ["transition", "has_feasibility_receipt", "receipt"],
                  ["transition", "has_successor_state", "successor"],
                  ["successor", "has_feasibility_receipt", "receipt"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("budget_req", "status"), L("approved")),
                      Eq(A("source", "state_key"), A("transition", "source_state_key")),
                      Eq(A("transition", "model_epoch"), A("request", "model_epoch")),
                      verified_receipt("receipt", "request", "transition", "successor"),
                      Eq(A("successor", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("existing", "state_key"), A("successor", "state_key")),
                      Eq(A("existing", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("existing", "goal_epoch"), A("request", "goal_epoch")),
                      Not(Eq(V("existing"), V("frontier"))),
                      Not(known_arrival)),
        "effects": [
            ["add_edge", "existing", "has_parent_frontier", "frontier", {}],
            ["add_edge", "existing", "uses_transition", "transition", {}],
        ],
    }


def count_expansion_rule():
    return {
        "name": "cp_count_unique_expansion", "area": AREA, "order": 23,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_frontier", "frontier"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("expanded")),
                      Eq(A("frontier", "expanded_counted"), ZERO)),
        "effects": [["set_attr", "frontier", "expanded_counted", 1.0],
                    ["set_attr", "request", "expanded_count", T(Plus(A("request", "expanded_count"), L(1.0))) ]],
    }


def solve_rule():
    return {
        "name": "cp_emit_imagined_plan_candidate", "area": AREA, "order": 24,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_goal_state", "goal_state"],
                  ["request", "has_frontier", "frontier"],
                  ["frontier", "expands_from_state", "state"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "state_key"), A("frontier", "goal_state_key")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("frontier", "candidate_emitted"), ZERO),
                      Eq(A("state", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("state", "goal_epoch"), A("request", "goal_epoch")),
                      state_has_verified_projection("state", "request"),
                      Eq(A("goal_state", "state_key"), A("request", "goal_state_key")),
                      Eq(A("goal_state", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("goal_state", "goal_epoch"), A("request", "goal_epoch")),
                      state_has_verified_projection("goal_state", "request")),
        "effects": [
            ["add_node", "candidate", "ImaginedPlanCandidate", {
                "status": "proposal", "provenance_kind": "imagined",
                "observation_status": "not_observed", "grounding_status": "ungrounded",
                "model_epoch": T(A("request", "model_epoch")),
                "source_epoch": T(A("request", "source_epoch")),
                "goal_epoch": T(A("request", "goal_epoch")),
                "manifold_epoch": T(A("request", "manifold_epoch")),
            }],
            ["add_edge", "request", "has_imagined_plan_candidate", "candidate", {}],
            ["add_edge", "candidate", "derived_from_frontier", "frontier", {}],
            ["set_attr", "frontier", "candidate_emitted", 1.0],
            ["set_attr", "frontier", "status", "candidate"],
        ],
    }


def emit_duplicate_goal_path_rule():
    seen_goal = Exists(N("request", "has_frontier"), "seen",
                       And(Eq(A("seen", "state_key"), A("successor", "state_key")),
                           Eq(A("seen", "model_epoch"), A("request", "model_epoch")),
                           Eq(A("seen", "goal_epoch"), A("request", "goal_epoch"))))
    return {
        "name": "cp_emit_duplicate_goal_path", "area": AREA, "order": 24,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_frontier", "frontier"],
                  ["request", "has_goal_state", "goal_state"],
                  ["frontier", "has_expansion_budget_request", "budget_req"],
                  ["transition", "has_feasibility_receipt", "receipt"],
                  ["frontier", "expands_from_state", "source"],
                  ["agent", "has_cognition_plan_transition", "transition"],
                  ["transition", "has_successor_state", "successor"],
                  ["successor", "has_feasibility_receipt", "receipt"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("budget_req", "status"), L("approved")),
                      Eq(A("source", "state_key"), A("transition", "source_state_key")),
                      Eq(A("transition", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("successor", "state_key"), A("frontier", "goal_state_key")),
                      verified_receipt("receipt", "request", "transition", "successor"),
                      Eq(A("successor", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("successor", "goal_epoch"), A("request", "goal_epoch")),
                      Eq(A("goal_state", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("goal_state", "goal_epoch"), A("request", "goal_epoch")),
                      Eq(A("goal_state", "state_key"), A("request", "goal_state_key")),
                      state_has_verified_projection("goal_state", "request"),
                      Not(Eq(A("transition", "goal_candidate_emitted"), L(1.0))),
                      seen_goal),
        "effects": [
            ["add_node", "candidate", "ImaginedPlanCandidate", {
                "status": "proposal", "provenance_kind": "imagined",
                "observation_status": "not_observed", "grounding_status": "ungrounded",
                "model_epoch": T(A("request", "model_epoch")),
                "source_epoch": T(A("request", "source_epoch")),
                "goal_epoch": T(A("request", "goal_epoch")),
                "manifold_epoch": T(A("request", "manifold_epoch")),
                "path_kind": "alternate_goal_arrival",
            }],
            ["add_edge", "request", "has_imagined_plan_candidate", "candidate", {}],
            ["add_edge", "candidate", "derived_from_frontier", "frontier", {}],
            ["add_edge", "candidate", "via_transition", "transition", {}],
            ["set_attr", "transition", "goal_candidate_emitted", 1.0],
        ],
    }


def close_solved_request_rule():
    ready = Exists(N("request", "has_frontier"), "frontier",
                   Eq(A("frontier", "status"), L("ready")))
    candidate = Exists(N("request", "has_imagined_plan_candidate"), "candidate",
                       Eq(A("candidate", "status"), L("proposal")))
    return {
        "name": "cp_close_solved_request", "area": AREA, "order": 26,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")), Not(ready), candidate),
        "effects": [["set_attr", "request", "status", "solved"]],
    }


def terminalize_depth_rule():
    return {
        "name": "cp_terminalize_depth_bound", "area": AREA, "order": 24,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_frontier", "frontier"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Gte(A("frontier", "depth"), Min(A("request", "depth_limit"), A("policy", "maximum_depth")))),
        "effects": [["set_attr", "frontier", "status", "terminal"],
                    ["set_attr", "frontier", "terminal_reason", "depth_limit"]],
    }


def terminalize_expansion_bound_rule():
    return {
        "name": "cp_terminalize_expansion_bound", "area": AREA, "order": 25,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_frontier", "frontier"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Gte(A("request", "expanded_count"),
                          Min(A("request", "expansion_limit"), A("policy", "maximum_expansions")))),
        "effects": [["set_attr", "frontier", "status", "terminal"],
                    ["set_attr", "frontier", "terminal_reason", "expansion_limit"]],
    }


def terminalize_unfunded_rule():
    return {
        "name": "cp_terminalize_unfunded_frontier", "area": AREA, "order": 24,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_frontier", "frontier"],
                  ["frontier", "has_expansion_budget_request", "budget_req"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("budget_req", "status"), L("denied"))),
        "effects": [["set_attr", "frontier", "status", "terminal"],
                    ["set_attr", "frontier", "terminal_reason", "budget_denied"]],
    }


def _unseen_successor_exists():
    same_key = And(
        Eq(A("seen", "state_key"), A("successor", "state_key")),
        Eq(A("seen", "model_epoch"), A("request", "model_epoch")),
        Eq(A("seen", "goal_epoch"), A("request", "goal_epoch")),
    )
    unseen_key = Not(Exists(N("request", "has_frontier"), "seen", same_key))
    successor_matches = And(
        Eq(A("successor", "model_epoch"), A("request", "model_epoch")),
        unseen_key,
        state_has_verified_projection("successor", "request"),
    )
    transition_matches = And(
        Eq(A("transition", "source_state_key"), A("frontier", "state_key")),
        Eq(A("transition", "model_epoch"), A("request", "model_epoch")),
        Exists(N("transition", "has_feasibility_receipt"), "receipt",
               verified_receipt("receipt", "request", "transition")),
        Exists(N("transition", "has_successor_state"), "successor", successor_matches),
    )
    return Exists(N("agent", "has_cognition_plan_transition"), "transition", transition_matches)


def terminalize_model_dead_end_rule():
    return {
        "name": "cp_terminalize_model_dead_end", "area": AREA, "order": 24,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_frontier", "frontier"],
                  ["frontier", "has_expansion_budget_request", "budget_req"],
                  ["agent", "has_cognition_plan_transition", "transition"],
                  ["transition", "has_feasibility_receipt", "receipt"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("budget_req", "status"), L("approved")),
                      Eq(A("transition", "source_state_key"), A("frontier", "state_key")),
                      Eq(A("transition", "model_epoch"), A("request", "model_epoch")),
                      verified_receipt("receipt", "request", "transition"),
                      Exists(N("transition", "has_successor_state"), "successor",
                             state_has_verified_projection("successor", "request")),
                      Not(_unseen_successor_exists())),
        "effects": [["set_attr", "frontier", "status", "terminal"],
                    ["set_attr", "frontier", "terminal_reason", "duplicate_or_cycle"],
                    ["set_attr", "frontier", "expanded_epoch", T(A("budget_req", "debited_epoch"))],
                    ["set_attr", "frontier", "expanded_counted", 1.0],
                    ["set_attr", "request", "expanded_count", T(Plus(A("request", "expanded_count"), L(1.0))) ]],
    }


def close_request_rule(reason, request_status, order):
    missing = Exists(N("request", "has_frontier"), "frontier",
                     Eq(A("frontier", "terminal_reason"), L("missing_transition")))
    ready = Exists(N("request", "has_frontier"), "frontier",
                   Eq(A("frontier", "status"), L("ready")))
    candidate = Exists(N("request", "has_imagined_plan_candidate"), "candidate",
                       Eq(A("candidate", "status"), L("proposal")))
    return {
        "name": f"cp_close_request_{reason}", "area": AREA, "order": order,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Not(ready), Not(candidate),
                      missing if request_status == "unknown" else Not(missing)),
        "effects": [["set_attr", "request", "status", request_status],
                    ["set_attr", "request", "terminal_reason", reason]],
    }


def terminalize_missing_transition_rule():
    return {
        "name": "cp_terminalize_missing_transition", "area": AREA, "order": 24,
        "latency_class": "hard_realtime", "batch": False,
        "match": [["agent", "has_cognition_planner_policy", "policy"],
                  ["agent", "has_cognition_plan_request", "request"],
                  ["request", "has_frontier", "frontier"],
                  ["frontier", "has_expansion_budget_request", "budget_req"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("budget_req", "status"), L("approved")),
                      Eq({"type": "Count", "source": Filter(
                          N("agent", "has_cognition_plan_transition"), "transition",
                          And(Eq(A("transition", "source_state_key"), A("frontier", "state_key")),
                              Eq(A("transition", "model_epoch"), A("request", "model_epoch")),
                              Exists(N("transition", "has_feasibility_receipt"), "receipt",
                                     verified_receipt("receipt", "request", "transition"))))}, ZERO)),
        "effects": [["set_attr", "frontier", "status", "terminal"],
                    ["set_attr", "frontier", "terminal_reason", "missing_transition"],
                    ["set_attr", "frontier", "expanded_epoch", T(A("budget_req", "debited_epoch"))],
                    ["set_attr", "frontier", "expanded_counted", 1.0],
                    ["set_attr", "request", "expanded_count", T(Plus(A("request", "expanded_count"), L(1.0))) ]],
    }


def build_seed():
    specs = production_specs()
    return {
        "id": "cognition_planner", "version": "1.1.0", "depends_on": ["thinking_budget", "generative_world_model", "cognition_manifold", "default_mode_core"],
        "self_load_only": True,
        "area": AREA,
        "description": "Opt-in graph-resident bounded planning over explicit versioned model transitions; emits advisory imagined candidates only.",
        "microtheory": {"name": AREA, "description": "Bounded, funded frontier search with graph-resident path provenance."},
        "nodes": [{"local_id": 0, "type": "CognitionPlannerPolicy", "attrs": {
            "enabled": 0.0, "maximum_depth": 8.0, "maximum_expansions": 256.0,
            "expansion_cost": 1.0, "maximum_branching": 8.0,
            "current_model_epoch": -1.0, "current_goal_epoch": -1.0,
            "current_manifold_epoch": -1.0,
            "current_model_id": "", "current_goal_id": "",
            "current_manifold_id": "",
        }}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_cognition_planner_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(),
        "rules": [terminalize_deadline_rule(), terminalize_prebind_stale_request_rule(), bind_model_start_state_rule(), bind_model_goal_state_rule(), terminalize_unbound_model_request_rule(), terminalize_stale_request_rule(), root_rule(), budget_request_rule(), adapt_native_model_transition_rule(), expand_rule(), preserve_duplicate_state_path_rule(), count_expansion_rule(), solve_rule(),
                  emit_duplicate_goal_path_rule(), close_solved_request_rule(),
                  terminalize_depth_rule(), terminalize_expansion_bound_rule(), terminalize_unfunded_rule(),
                  terminalize_missing_transition_rule(), terminalize_model_dead_end_rule(),
                  close_request_rule("missing_transition", "unknown", 27),
                  close_request_rule("frontier_closed", "exhausted", 28)],
    }


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
