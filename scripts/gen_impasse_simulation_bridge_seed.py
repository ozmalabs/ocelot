#!/usr/bin/env python3
"""Author the impasse_simulation_bridge seed (P1.A4).

Bridges System-2 escalations on DualProcessContext to counterfactual rollouts
in generative_world_model and proposes the highest-expected-value root action
as an ImaginedCandidate.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from gen_capability_collapse_seed import (
    A,
    And,
    Count,
    Eq,
    Filter,
    Gt,
    Gte,
    L,
    Max,
    N,
    Not,
    ONE,
    Or,
    Plus,
    T,
    V,
    ZERO,
)

AREA = "impasse_simulation"

TRIGGER_REASONS = (
    "instinct_conflict",
    "near_conflict",
    "low_confidence",
    "no_grounded_default",
    "controller_arbitration",
    "prediction_error",
    "novelty",
    "uncertainty",
)


def Times(*items):
    return {"type": "Times", "items": list(items)}


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def Exists(source, var_name, predicate):
    return {
        "type": "Exists",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def IfThenElse(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def policy_cost():
    return IfThenElse(
        Eq(A("pol", "cost"), L(None)),
        L(1.0),
        A("pol", "cost"),
    )


def budget_enabled(var="budget"):
    return Gte(A(var, "enabled"), L(1.0))


def unbudgeted_or_disabled():
    return Not(
        Exists(
            N("agent", "has_thinking_budget"),
            "tb",
            budget_enabled("tb"),
        )
    )


def Argmax(source, var_name, value, default=None):
    return {
        "type": "Argmax",
        "source": source,
        "var_name": var_name,
        "value": value,
        "default": default if default is not None else L(None),
    }


def MaxOver(source, var_name, value, default=None):
    return {
        "type": "MaxOver",
        "source": source,
        "var_name": var_name,
        "value": value,
        "default": default if default is not None else L(0.0),
    }


def policy_enabled():
    return Eq(A("pol", "enabled"), L(1.0))


def trajectory_score(traj_var):
    return MaxOver(
        N(traj_var, "has_predicted_belief_state"),
        "s",
        MaxOver(
            N("s", "has_predicted_outcome"),
            "o",
            Times(A("o", "outcome_value"), A("o", "confidence")),
            default=L(0.0),
        ),
        default=L(0.0),
    )


def request_simulation_rule():
    current_perceived_beliefs = Filter(
        N("agent", "has_belief_state"),
        "candidate_belief",
        And(
            Eq(A("candidate_belief", "status"), L("current")),
            Eq(A("candidate_belief", "provenance_kind"), L("perceived")),
        ),
    )
    deadline_term = Plus(A("mode", "epoch"), A("pol", "deadline_window"))
    return {
        "name": "isb_request_simulation",
        "area": AREA,
        "order": 16,
        "latency_class": "hard_realtime",
        "comment": (
            "Open an impasse_counterfactual SimulationRequest and a SystemTwoEscalation "
            "recruiting world_model_simulation when a DualProcessContext escalates."
        ),
        "match": [
            ["agent", "has_impasse_simulation_policy", "pol"],
            ["agent", "has_dual_process_context", "ctx"],
            ["ctx", "has_system_two_escalation", "esc"],
            ["agent", "has_network_mode_state", "mode"],
            ["agent", "has_belief_state", "belief"],
            ["agent", "has_world_model_simulation_task_set", "wts"],
        ],
        "where": And(
            policy_enabled(),
            Eq(A("ctx", "status"), L("escalated")),
            Or(*(Eq(A("esc", "reason"), L(reason)) for reason in TRIGGER_REASONS)),
            Eq(Count(N("esc", "has_impasse_simulation")), ZERO),
            Not(Eq(A("esc", "isb_requested"), ONE)),
            Eq(A("belief", "status"), L("current")),
            Eq(A("belief", "provenance_kind"), L("perceived")),
            Eq(
                V("belief"),
                Argmax(
                    current_perceived_beliefs,
                    "ranked_belief",
                    A("ranked_belief", "epoch"),
                ),
            ),
            unbudgeted_or_disabled(),
        ),
        "effects": [
            ["add_node", "sim", "SimulationRequest", {
                "status": "collecting_actions",
                "request_kind": "impasse_counterfactual",
                "provenance_kind": "imagined",
                "observation_status": "not_observed",
                "input_epoch": T(A("mode", "epoch")),
                "deadline_epoch": T(deadline_term),
                "horizon": T(A("pol", "horizon")),
                "budget": T(A("pol", "budget")),
                "maximum_branching": T(A("pol", "maximum_branching")),
                "interruptible": 1.0,
            }],
            ["add_node", "req", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "impasse_simulation",
                "request_kind": "impasse",
                "input_epoch": T(A("mode", "epoch")),
                "deadline_epoch": T(deadline_term),
            }],
            ["set_attr", "esc", "isb_requested", 1],
            ["add_edge", "agent", "has_simulation_request", "sim", {}],
            ["add_edge", "esc", "has_impasse_simulation", "sim", {}],
            ["add_edge", "sim", "has_source_belief", "belief", {}],
            ["add_edge", "sim", "validated_by_clock", "mode", {}],
            ["add_edge", "req", "about_context", "mode", {}],
            ["add_edge", "req", "recruits_task_set", "wts", {}],
            ["add_edge", "sim", "driven_by_escalation", "req", {}],
        ],
    }


def request_simulation_budgeted_rule():
    current_perceived_beliefs = Filter(
        N("agent", "has_belief_state"),
        "candidate_belief",
        And(
            Eq(A("candidate_belief", "status"), L("current")),
            Eq(A("candidate_belief", "provenance_kind"), L("perceived")),
        ),
    )
    deadline_term = Plus(A("mode", "epoch"), A("pol", "deadline_window"))
    cost_term = policy_cost()
    return {
        "name": "isb_request_simulation_budgeted",
        "area": AREA,
        "order": 16,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": (
            "When ThinkingBudget is enabled and has `remaining >= pol.cost`, open an "
            "impasse_counterfactual SimulationRequest, link the escalation via "
            "`draws_on_thinking_budget`, and debit `ThinkingBudget.remaining`."
        ),
        "match": [
            ["agent", "has_impasse_simulation_policy", "pol"],
            ["agent", "has_thinking_budget", "budget"],
            ["agent", "has_dual_process_context", "ctx"],
            ["ctx", "has_system_two_escalation", "esc"],
            ["agent", "has_network_mode_state", "mode"],
            ["agent", "has_belief_state", "belief"],
            ["agent", "has_world_model_simulation_task_set", "wts"],
        ],
        "where": And(
            policy_enabled(),
            budget_enabled("budget"),
            Gte(A("budget", "remaining"), cost_term),
            Eq(A("ctx", "status"), L("escalated")),
            Or(*(Eq(A("esc", "reason"), L(reason)) for reason in TRIGGER_REASONS)),
            Eq(Count(N("esc", "has_impasse_simulation")), ZERO),
            Not(Eq(A("esc", "isb_requested"), ONE)),
            Eq(A("belief", "status"), L("current")),
            Eq(A("belief", "provenance_kind"), L("perceived")),
            Eq(
                V("belief"),
                Argmax(
                    current_perceived_beliefs,
                    "ranked_belief",
                    A("ranked_belief", "epoch"),
                ),
            ),
        ),
        "effects": [
            ["add_node", "sim", "SimulationRequest", {
                "status": "collecting_actions",
                "request_kind": "impasse_counterfactual",
                "provenance_kind": "imagined",
                "observation_status": "not_observed",
                "input_epoch": T(A("mode", "epoch")),
                "deadline_epoch": T(deadline_term),
                "horizon": T(A("pol", "horizon")),
                "budget": T(A("pol", "budget")),
                "maximum_branching": T(A("pol", "maximum_branching")),
                "interruptible": 1.0,
            }],
            ["add_node", "req", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "impasse_simulation",
                "request_kind": "impasse",
                "cost": T(cost_term),
                "input_epoch": T(A("mode", "epoch")),
                "deadline_epoch": T(deadline_term),
            }],
            ["set_attr", "esc", "isb_requested", 1],
            [
                "set_attr",
                "budget",
                "remaining",
                T(Max(ZERO, Minus(A("budget", "remaining"), cost_term))),
            ],
            ["add_edge", "agent", "has_simulation_request", "sim", {}],
            ["add_edge", "esc", "has_impasse_simulation", "sim", {}],
            ["add_edge", "sim", "has_source_belief", "belief", {}],
            ["add_edge", "sim", "validated_by_clock", "mode", {}],
            ["add_edge", "req", "about_context", "mode", {}],
            ["add_edge", "req", "recruits_task_set", "wts", {}],
            ["add_edge", "req", "draws_on_thinking_budget", "budget", {}],
            ["add_edge", "sim", "driven_by_escalation", "req", {}],
        ],
    }


def record_budget_exhaustion_rule():
    current_perceived_beliefs = Filter(
        N("agent", "has_belief_state"),
        "candidate_belief",
        And(
            Eq(A("candidate_belief", "status"), L("current")),
            Eq(A("candidate_belief", "provenance_kind"), L("perceived")),
        ),
    )
    cost_term = policy_cost()
    return {
        "name": "isb_record_budget_exhaustion",
        "area": AREA,
        "order": 16,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": (
            "When an impasse simulation request is blocked because "
            "`ThinkingBudget.remaining < pol.cost`, record at most one "
            "`ThinkingBudgetDenial` for `impasse_simulation` at `mode.epoch`."
        ),
        "match": [
            ["agent", "has_impasse_simulation_policy", "pol"],
            ["agent", "has_thinking_budget", "budget"],
            ["agent", "has_dual_process_context", "ctx"],
            ["ctx", "has_system_two_escalation", "esc"],
            ["agent", "has_network_mode_state", "mode"],
            ["agent", "has_belief_state", "belief"],
            ["agent", "has_world_model_simulation_task_set", "wts"],
        ],
        "where": And(
            policy_enabled(),
            budget_enabled("budget"),
            Lt(A("budget", "remaining"), cost_term),
            Eq(A("ctx", "status"), L("escalated")),
            Or(*(Eq(A("esc", "reason"), L(reason)) for reason in TRIGGER_REASONS)),
            Eq(Count(N("esc", "has_impasse_simulation")), ZERO),
            Not(Eq(A("esc", "isb_requested"), ONE)),
            Eq(A("belief", "status"), L("current")),
            Eq(A("belief", "provenance_kind"), L("perceived")),
            Eq(
                V("belief"),
                Argmax(
                    current_perceived_beliefs,
                    "ranked_belief",
                    A("ranked_belief", "epoch"),
                ),
            ),
            Not(
                Exists(
                    N("agent", "has_thinking_budget_denial"),
                    "d",
                    And(
                        Eq(A("d", "requester_kind"), L("impasse_simulation")),
                        Eq(A("d", "epoch"), A("mode", "epoch")),
                    ),
                )
            ),
        ),
        "effects": [
            ["add_node", "denial", "ThinkingBudgetDenial", {
                "reason": "budget_exhausted",
                "requester_kind": "impasse_simulation",
                "epoch": T(A("mode", "epoch")),
            }],
            ["add_edge", "agent", "has_thinking_budget_denial", "denial", {}],
        ],
    }


def offer_actions_rule():
    return {
        "name": "isb_offer_actions",
        "area": AREA,
        "order": 16,
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Offer all held WorldModelAction nodes to the collecting impasse simulation request.",
        "match": [
            ["agent", "has_impasse_simulation_policy", "pol"],
            ["ctx", "has_system_two_escalation", "esc"],
            ["esc", "has_impasse_simulation", "sim"],
            ["agent", "has_world_model_action", "action"],
        ],
        "where": And(
            policy_enabled(),
            Eq(A("ctx", "status"), L("escalated")),
            Eq(A("sim", "status"), L("collecting_actions")),
        ),
        "effects": [
            ["add_edge", "sim", "considers_action", "action", {}],
        ],
    }


def seal_rule():
    return {
        "name": "isb_seal",
        "area": AREA,
        "order": 17,
        "latency_class": "hard_realtime",
        "comment": "Seal the impasse simulation action snapshot so generative_world_model can expand branches.",
        "match": [
            ["agent", "has_impasse_simulation_policy", "pol"],
            ["ctx", "has_system_two_escalation", "esc"],
            ["esc", "has_impasse_simulation", "sim"],
            ["sim", "considers_action", "action"],
        ],
        "where": And(
            policy_enabled(),
            Eq(A("ctx", "status"), L("escalated")),
            Eq(A("sim", "status"), L("collecting_actions")),
        ),
        "effects": [
            ["set_attr", "sim", "status", "active"],
        ],
    }


def propose_imagined_candidate_rule():
    best_trajectory = Argmax(
        N("sim", "has_prediction_trajectory"),
        "tr",
        trajectory_score("tr"),
    )
    return {
        "name": "isb_propose_imagined_candidate",
        "area": AREA,
        "order": 18,
        "latency_class": "hard_realtime",
        "comment": "Select the highest-expected-value simulated trajectory and propose an ImaginedCandidate on the escalation.",
        "match": [
            ["agent", "has_impasse_simulation_policy", "pol"],
            ["ctx", "has_system_two_escalation", "esc"],
            ["esc", "has_impasse_simulation", "sim"],
            ["sim", "has_prediction_trajectory", "t"],
        ],
        "where": And(
            policy_enabled(),
            Eq(A("sim", "status"), L("completed")),
            Eq(Count(N("esc", "has_imagined_candidate")), ZERO),
            Eq(V("t"), best_trajectory),
        ),
        "effects": [
            ["add_node", "cand", "ImaginedCandidate", {
                "status": "proposal",
                "provenance_kind": "imagined",
                "observation_status": "not_observed",
                "root_action_kind": T(A("t", "root_action_kind")),
                "expected_value": T(trajectory_score("t")),
            }],
            ["add_edge", "esc", "has_imagined_candidate", "cand", {}],
            ["add_edge", "cand", "derived_from_trajectory", "t", {}],
        ],
    }


def cancel_on_terminal_rule():
    return {
        "name": "isb_cancel_on_terminal",
        "area": AREA,
        "order": 19,
        "latency_class": "hard_realtime",
        "comment": "Cancel the simulation and its driving SystemTwoEscalation when the context commits or the deadline passes.",
        "match": [
            ["agent", "has_impasse_simulation_policy", "pol"],
            ["agent", "has_network_mode_state", "mode"],
            ["ctx", "has_system_two_escalation", "esc"],
            ["esc", "has_impasse_simulation", "sim"],
            ["sim", "driven_by_escalation", "req"],
        ],
        "where": And(
            policy_enabled(),
            Or(
                Eq(A("ctx", "status"), L("committed")),
                Gt(A("mode", "epoch"), A("sim", "deadline_epoch")),
            ),
            Or(
                Eq(A("sim", "status"), L("collecting_actions")),
                Eq(A("sim", "status"), L("active")),
                Eq(A("sim", "status"), L("completed")),
            ),
        ),
        "effects": [
            ["set_attr", "sim", "status", "cancelled"],
            ["set_attr", "sim", "terminal_reason", "context_committed_or_deadline"],
            ["set_attr", "sim", "cleanup_after_epoch",
             T(Plus(A("mode", "epoch"), L(2.0)))],
            ["set_attr", "req", "status", "cancelled"],
        ],
    }


def productions():
    specs = [
        ("Agent", "has_impasse_simulation_policy", "ImpasseSimulationPolicy"),
        ("Agent", "has_simulation_request", "SimulationRequest"),
        ("SystemTwoEscalation", "has_impasse_simulation", "SimulationRequest"),
        ("SimulationRequest", "has_source_belief", "BeliefState"),
        ("SimulationRequest", "validated_by_clock", "NetworkModeState"),
        ("SystemTwoEscalation", "about_context", "NetworkModeState"),
        ("SystemTwoEscalation", "recruits_task_set", "SystemTwoTaskSet"),
        ("SimulationRequest", "driven_by_escalation", "SystemTwoEscalation"),
        ("SimulationRequest", "considers_action", "WorldModelAction"),
        ("SystemTwoEscalation", "has_imagined_candidate", "ImaginedCandidate"),
        ("ImaginedCandidate", "derived_from_trajectory", "PredictionTrajectory"),
        ("Agent", "has_thinking_budget", "ThinkingBudget"),
        ("Agent", "has_thinking_budget_denial", "ThinkingBudgetDenial"),
        ("SystemTwoEscalation", "draws_on_thinking_budget", "ThinkingBudget"),
    ]
    return [
        {
            "provenance": f"seed:impasse_simulation_bridge:{edge_type}:{src}:{tgt}",
            "src": {"type": src, "var": "src"},
            "edge_type": edge_type,
            "tgt": {"type": tgt, "var": "tgt"},
        }
        for src, edge_type, tgt in specs
    ]


def build():
    return {
        "id": "impasse_simulation_bridge",
        "version": "1.0.0",
        "depends_on": [
            "dual_process_core",
            "generative_world_model",
            "default_mode_core",
        ],
        "area": AREA,
        "description": (
            "Opt-in bridge that responds to a System-2 escalation on DualProcessContext "
            "by opening an action-conditioned SimulationRequest in generative_world_model "
            "and proposing the highest-expected-value branch as an ImaginedCandidate."
        ),
        "microtheory": {
            "name": "impasse_simulation_bridge",
            "description": (
                "System-2 escalations recruit bounded world-model counterfactual rollouts "
                "and surface the best branch as an explicit ImaginedCandidate."
            ),
        },
        "nodes": [
            {
                "local_id": 0,
                "type": "ImpasseSimulationPolicy",
                "attrs": {
                    "enabled": 0.0,
                    "cost": 1.0,
                    "horizon": 3.0,
                    "budget": 6.0,
                    "maximum_branching": 2.0,
                    "deadline_window": 4.0,
                },
            },
        ],
        "edges": [
            {
                "src": {"role": "agent_root"},
                "type": "has_impasse_simulation_policy",
                "tgt": {"local": 0},
                "attrs": {},
            },
        ],
        "productions": productions(),
        "rules": [
            request_simulation_rule(),
            request_simulation_budgeted_rule(),
            record_budget_exhaustion_rule(),
            offer_actions_rule(),
            seal_rule(),
            propose_imagined_candidate_rule(),
            cancel_on_terminal_rule(),
        ],
    }


def main():
    out = ROOT / "seeds" / "impasse_simulation_bridge.json"
    out.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
