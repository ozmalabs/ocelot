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
        ("Agent", "has_thinking_budget", "ThinkingBudget"),
        ("Agent", "has_network_mode_state", "NetworkModeState"),
        ("CognitionPlanRequest", "has_start_state", "CognitionPlanState"),
        ("CognitionPlanRequest", "has_goal_state", "CognitionPlanState"),
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


def terminalize_stale_request_rule():
    stale = Or(Eq(A("request", "source_epoch"), L(None)),
               Not(Eq(A("request", "source_epoch"), A("mode", "epoch"))),
               Not(Eq(A("request", "model_epoch"), A("policy", "current_model_epoch"))),
               Not(Eq(A("request", "goal_epoch"), A("policy", "current_goal_epoch"))),
               Not(Eq(A("request", "manifold_epoch"), A("policy", "current_manifold_epoch"))),
               Not(Eq(A("request", "model_epoch"), A("start", "model_epoch"))),
               Not(Eq(A("request", "goal_epoch"), A("goal", "goal_epoch"))))
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
                      stale),
        "effects": [["set_attr", "request", "status", "model_stale"],
                    ["set_attr", "request", "terminal_reason", "planning_epoch_changed"]],
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
                  ["transition", "has_successor_state", "successor"],
                  ["frontier", "expands_from_state", "source"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("budget_req", "status"), L("approved")),
                      Eq(V("frontier"), Argmin(ready_frontiers(), "ranked_frontier",
                                                A("ranked_frontier", "rank"), default=L(None))),
                      Eq(A("source", "state_key"), A("transition", "source_state_key")),
                      Eq(A("transition", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("successor", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("request", "model_epoch"), A("policy", "current_model_epoch")),
                      Eq(A("request", "goal_epoch"), A("policy", "current_goal_epoch")),
                      Eq(A("request", "manifold_epoch"), A("policy", "current_manifold_epoch")),
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
                      Eq(A("state", "projection_status"), L("feasible")),
                      Eq(A("state", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("state", "goal_epoch"), A("request", "goal_epoch")),
                      Eq(A("goal_state", "state_key"), A("request", "goal_state_key")),
                      Eq(A("goal_state", "projection_status"), L("feasible")),
                      Eq(A("goal_state", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("goal_state", "goal_epoch"), A("request", "goal_epoch"))),
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
                  ["frontier", "expands_from_state", "source"],
                  ["agent", "has_cognition_plan_transition", "transition"],
                  ["transition", "has_successor_state", "successor"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("budget_req", "status"), L("approved")),
                      Eq(A("source", "state_key"), A("transition", "source_state_key")),
                      Eq(A("transition", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("successor", "state_key"), A("frontier", "goal_state_key")),
                      Eq(A("successor", "projection_status"), L("feasible")),
                      Eq(A("successor", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("successor", "goal_epoch"), A("request", "goal_epoch")),
                      Eq(A("goal_state", "projection_status"), L("feasible")),
                      Eq(A("goal_state", "model_epoch"), A("request", "model_epoch")),
                      Eq(A("goal_state", "goal_epoch"), A("request", "goal_epoch")),
                      Eq(A("goal_state", "state_key"), A("request", "goal_state_key")),
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
    )
    transition_matches = And(
        Eq(A("transition", "source_state_key"), A("frontier", "state_key")),
        Eq(A("transition", "model_epoch"), A("request", "model_epoch")),
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
                  ["agent", "has_cognition_plan_transition", "transition"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                      Eq(A("request", "status"), L("searching")),
                      Eq(A("frontier", "status"), L("ready")),
                      Eq(A("budget_req", "status"), L("approved")),
                      Eq(A("transition", "source_state_key"), A("frontier", "state_key")),
                      Eq(A("transition", "model_epoch"), A("request", "model_epoch")),
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
                              Eq(A("transition", "model_epoch"), A("request", "model_epoch"))))}, ZERO)),
        "effects": [["set_attr", "frontier", "status", "terminal"],
                    ["set_attr", "frontier", "terminal_reason", "missing_transition"],
                    ["set_attr", "frontier", "expanded_epoch", T(A("budget_req", "debited_epoch"))],
                    ["set_attr", "frontier", "expanded_counted", 1.0],
                    ["set_attr", "request", "expanded_count", T(Plus(A("request", "expanded_count"), L(1.0))) ]],
    }


def build_seed():
    specs = production_specs()
    return {
        "id": "cognition_planner", "version": "1.0.0", "depends_on": ["thinking_budget", "generative_world_model", "default_mode_core"],
        "self_load_only": True,
        "area": AREA,
        "description": "Opt-in graph-resident bounded planning over explicit versioned model transitions; emits advisory imagined candidates only.",
        "microtheory": {"name": AREA, "description": "Bounded, funded frontier search with graph-resident path provenance."},
        "nodes": [{"local_id": 0, "type": "CognitionPlannerPolicy", "attrs": {
            "enabled": 0.0, "maximum_depth": 8.0, "maximum_expansions": 256.0,
            "expansion_cost": 1.0, "maximum_branching": 8.0,
            "current_model_epoch": -1.0, "current_goal_epoch": -1.0,
            "current_manifold_epoch": -1.0,
        }}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_cognition_planner_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(),
        "rules": [terminalize_stale_request_rule(), root_rule(), budget_request_rule(), expand_rule(), count_expansion_rule(), solve_rule(),
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
