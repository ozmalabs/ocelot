#!/usr/bin/env python3
"""Generate graph-native leases and check-ins for active cognition.

Each selected learning step becomes a CognitiveProcess with its own integer
clock policy and renewable continuation lease.  Approximate cognitive time or
an explicitly observed envelope departure withdraws the lease before review.
The completed window is compared with the previous window using integer
cross-products, so the graph evaluates marginal efficiency without division,
floating point, or scalarising its objectives.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(var, key): return {"type": "Attr", "node": V(var), "key": key}
def P0(var, key): return {"type": "Plus", "items": [A(var, key), L(0)]}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Or(*items): return {"type": "Or", "items": list(items)}
def Not(item): return {"type": "Not", "arg": item}
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Mul(a, b): return {"type": "Times", "items": [a, b]}
def Neg(item): return {"type": "Neg", "arg": item}
def Max(*items): return {"type": "Max", "items": list(items)}
def Count(source): return {"type": "Count", "source": source}
def Sum(source, var, value): return {
    "type": "Sum", "source": source, "var_name": var, "value": value,
}
def Neighbours(var, edge): return {
    "type": "Neighbours", "node": V(var), "edge_type": edge,
}
def Filter(source, var, predicate): return {
    "type": "Filter", "source": source, "var_name": var,
    "predicate": predicate,
}
def T(term): return {"__term__": term}


def production(name, src, edge, tgt):
    return {
        "provenance": f"cognitive_supervision:{name}",
        "src": {"type": src, "var": "src"},
        "edge_type": edge,
        "tgt": {"type": tgt, "var": "tgt"},
    }


def processes_for_step():
    return Filter(
        Neighbours("episode", "has_cognitive_process"),
        "known_process",
        Eq(Count(Filter(
            Neighbours("known_process", "supervises_learning_plan_step"),
            "known_step", Eq(V("known_step"), V("step")),
        )), L(1)),
    )


def attach_rule():
    span = Max(L(1), P0("episode", "development_evidence_window"))
    return {
        "name": "cs_attach_renewable_lease_to_selected_cognitive_process",
        "area": "cognitive_supervision",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The process owns a strict integer lease and clock. The "
        "situated evidence window supplies an initial check-in span, not a "
        "global timeout.",
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
            ["step", "pursues_goal", "goal"],
        ],
        "where": Eq(Count(processes_for_step()), L(0)),
        "effects": [
            ["add_node", "policy", "CognitiveSupervisionPolicy", {
                "enabled": 1,
                "cognitive_epoch": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_node", "process", "CognitiveProcess", {
                "status": "monitoring",
                "kind": "self_directed_learning",
                "order_n": 1,
                "continuation_authority": 1,
                "lease_generation": 0,
                "renew_before_epoch": T(span),
                "last_checkin_epoch": 0,
                "next_checkin_epoch": T(span),
                "checkin_span_units": T(span),
                "baseline_effort_units": T(P0("step", "evidence_spent_units")),
                "checkin_count": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_node", "reference", "CognitiveEfficiencyWindow", {
                "status": "reference",
                "causal_yield_units": 0,
                "information_gain_units": 0,
                "failure_burden_units": 0,
                "effort_units": 1,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "episode", "has_cognitive_process", "process"],
            ["add_edge", "process", "governed_by_cognitive_supervision_policy", "policy"],
            ["add_edge", "process", "has_reference_efficiency_window", "reference"],
            ["add_edge", "process", "supervises_learning_plan", "plan"],
            ["add_edge", "process", "supervises_learning_plan_step", "step"],
            ["add_edge", "process", "supervises_learning_capability", "instance"],
            ["add_edge", "process", "pursues_goal", "goal"],
            ["add_edge", "process", "supervises_goal", "goal"],
            ["set_attr", "episode", "cognitive_continuation_authority", 1],
        ],
    }


def adjust_daemon_cycle_budget_rule():
    """Project an existing supervisory lease into an asynchronous quantum.

    The daemon reads this node mechanically.  The graph owns both the current
    allowance and the reason it changed: a renewed process lease is the only
    source of a later quantum.  This is a scheduling boundary, never a
    cognition policy implemented in Python.
    """
    return {
        "name": "cs_adjust_async_daemon_cycle_quantum_from_supervisory_lease",
        "area": "cognitive_supervision",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The asynchronous host consumes a graph-authored rewrite quantum. A new supervisory lease publishes an immutable adjustment provenance node before changing the next quantum.",
        "match": [
            ["anchor", "has_async_daemon_cycle_budget", "budget"],
            ["episode", "has_cognitive_process", "process"],
            ["process", "governed_by_cognitive_supervision_policy", "policy"],
        ],
        "where": And(
            Eq(A("policy", "enabled"), L(1)),
            Gt(P0("process", "lease_generation"),
               A("budget", "observed_lease_generation")),
        ),
        "effects": [
            ["add_node", "adjustment", "DaemonCycleBudgetAdjustment", {
                "reason": "supervisory_lease_renewal",
                "from_lease_generation": T(P0("budget", "observed_lease_generation")),
                "to_lease_generation": T(P0("process", "lease_generation")),
                "quantum_units": T(Max(L(1), P0("process", "checkin_span_units"))),
                "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "budget", "has_daemon_cycle_budget_adjustment", "adjustment"],
            ["add_edge", "adjustment", "adjusts_for_cognitive_process", "process"],
            ["add_edge", "adjustment", "governed_by_cognitive_supervision_policy", "policy"],
            ["set_attr", "budget", "quantum_units", T(Max(
                L(1), P0("process", "checkin_span_units")
            ))],
            ["set_attr", "budget", "observed_lease_generation", T(P0(
                "process", "lease_generation"
            ))],
            ["set_attr", "budget", "adjustment_count", T(Plus(
                P0("budget", "adjustment_count"), L(1)
            ))],
        ],
    }


def expand_order_n_goal_tree_rule():
    return {
        "name": "cs_follow_existing_goal_tree_to_arbitrary_depth",
        "area": "cognitive_supervision",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A subgoal is a Goal. Repeated fixpoint application "
        "therefore exposes every reachable order without a depth limit.",
        "match": [
            ["process", "supervises_goal", "parent"],
            ["parent", "has_subgoal", "goal"],
        ],
        "where": Not(Exists(
            Neighbours("process", "supervises_goal"), "known_goal",
            Eq(V("known_goal"), V("goal")),
        )),
        "effects": [["add_edge", "process", "supervises_goal", "goal"]],
    }


def instantiate_goal_baseline_rule():
    return {
        "name": "cs_baseline_each_goal_dimension_without_scalarising_tree",
        "area": "cognitive_supervision",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [["process", "supervises_goal", "goal"]],
        "where": Eq(Count(baseline_for_goal()), L(0)),
        "effects": [
            ["add_node", "baseline", "CognitiveGoalBaseline", {
                "baseline_progress_units": T(P0("goal", "progress_units")),
                "observed_progress_units": T(P0("goal", "progress_units")),
                "previous_progress_units": 0,
                "previous_effort_units": 1,
                "baseline_generation": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "process", "has_cognitive_goal_baseline", "baseline"],
            ["add_edge", "baseline", "measures_goal", "goal"],
        ],
    }


def observe_goal_progress_rule():
    return {
        "name": "cs_observe_each_supervised_goal_progress",
        "area": "cognitive_supervision",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["process", "has_cognitive_goal_baseline", "baseline"],
            ["baseline", "measures_goal", "goal"],
        ],
        "where": Not(Eq(
            P0("baseline", "observed_progress_units"),
            P0("goal", "progress_units"),
        )),
        "effects": [["set_attr", "baseline", "observed_progress_units",
                     T(P0("goal", "progress_units"))]],
    }


def Exists(source, var, predicate): return {
    "type": "Exists", "source": source, "var_name": var,
    "predicate": predicate,
}


def supervised_goals():
    return Neighbours("process", "supervises_goal")


def goal_baselines():
    return Neighbours("process", "has_cognitive_goal_baseline")


def baseline_for_goal():
    return Filter(
        goal_baselines(), "known_baseline",
        Exists(
            Neighbours("known_baseline", "measures_goal"),
            "known_goal", Eq(V("known_goal"), V("goal")),
        ),
    )


def candidate_dominates_current():
    current_values = Neighbours("current", "has_pareto_value")
    alternative_values = Neighbours("alternative", "has_pareto_value")
    no_worse = Filter(
        current_values, "current_value",
        Exists(
            alternative_values, "alternative_value",
            And(
                Exists(
                    Neighbours("current_value", "measures_goal"),
                    "dimension_goal",
                    Exists(
                        Neighbours("alternative_value", "measures_goal"),
                        "alternative_goal",
                        Eq(V("dimension_goal"), V("alternative_goal")),
                    ),
                ),
                Not(Lt(P0("alternative_value", "signed_value"),
                       P0("current_value", "signed_value"))),
            ),
        ),
    )
    better = Filter(
        current_values, "current_value",
        Exists(
            alternative_values, "alternative_value",
            And(
                Exists(
                    Neighbours("current_value", "measures_goal"),
                    "dimension_goal",
                    Exists(
                        Neighbours("alternative_value", "measures_goal"),
                        "alternative_goal",
                        Eq(V("dimension_goal"), V("alternative_goal")),
                    ),
                ),
                Gt(P0("alternative_value", "signed_value"),
                   P0("current_value", "signed_value")),
            ),
        ),
    )
    return And(
        Not(Eq(V("alternative"), V("current"))),
        Eq(Count(no_worse), P0("profile", "dimension_count")),
        Gt(Count(better), L(0)),
    )


def checkin_effects(reason, *, signal=None):
    effort = Minus(P0("step", "evidence_spent_units"),
                   P0("process", "baseline_effort_units"))
    progress = Sum(
        goal_baselines(), "goal_baseline",
        Minus(
            P0("goal_baseline", "observed_progress_units"),
            P0("goal_baseline", "baseline_progress_units"),
        ),
    )
    effects = [
        ["add_node", "checkin", "CognitiveCheckIn", {
            "status": "open",
            "reason": reason,
            "epoch": T(P0("policy", "cognitive_epoch")),
            "goal_progress_units": T(progress),
            "causal_yield_units": T(progress),
            "information_gain_units": 0,
            "failure_burden_units": 0,
            "effort_units": T(effort),
            "lease_generation": T(P0("process", "lease_generation")),
            "integer_native": 1,
            "output_authority": 0,
        }],
        ["add_node", "window", "CognitiveEfficiencyWindow", {
            "status": "under_review",
            "causal_yield_units": T(progress),
            "information_gain_units": 0,
            "failure_burden_units": 0,
            "effort_units": T(Max(L(1), effort)),
            "integer_native": 1,
            "output_authority": 0,
        }],
        ["add_node", "profile", "ParetoProfile", {
            "kind": "marginal_cognitive_process_efficiency_checkin",
            "status": "comparing",
            "dimension_count": T(Count(supervised_goals())),
            "scalarized": 0,
            "integer_native": 1,
            "output_authority": 0,
        }],
        ["add_node", "current", "ParetoCandidate", {
            "kind": "continue_current_cognitive_process",
            "dominated": 0, "verified": 1,
            "integer_native": 1, "output_authority": 0,
        }],
        ["add_node", "prior", "ParetoCandidate", {
            "kind": "previous_cognitive_efficiency_window",
            "dominated": 0, "verified": 1,
            "integer_native": 1, "output_authority": 0,
        }],
        ["add_node", "pause", "ParetoCandidate", {
            "kind": "pause_and_replan",
            "dominated": 0, "verified": 1,
            "integer_native": 1, "output_authority": 0,
        }],
        ["add_node", "escalation", "SystemTwoEscalation", {
            "status": "requested",
            "reason": "cognitive_process_checkin",
            "input_epoch": T(P0("policy", "cognitive_epoch")),
            "lease_generation": T(P0("process", "lease_generation")),
            "parallel_contexts": 1,
            "integer_native": 1, "output_authority": 0,
        }],
        ["add_node", "task_supervision", "SystemTwoTaskSet", {
            "area": "cognitive_supervision", "enabled": 1,
            "integer_native": 1,
        }],
        ["add_node", "task_pareto", "SystemTwoTaskSet", {
            "area": "cognitive_pareto", "enabled": 1,
            "integer_native": 1,
        }],
        ["add_edge", "process", "has_cognitive_checkin", "checkin"],
        ["add_edge", "checkin", "reviews_efficiency_window", "window"],
        ["add_edge", "checkin", "compares_reference_efficiency_window", "reference"],
        ["add_edge", "checkin", "has_efficiency_pareto_profile", "profile"],
        ["add_edge", "profile", "audits_goal", "goal"],
        ["add_edge", "profile", "has_pareto_candidate", "current"],
        ["add_edge", "profile", "has_pareto_candidate", "prior"],
        ["add_edge", "profile", "has_pareto_candidate", "pause"],
        ["add_edge", "profile", "has_incumbent_pareto_candidate", "current"],
        ["add_edge", "current", "represents_cognitive_process", "process"],
        ["add_edge", "current", "represents_efficiency_window", "window"],
        ["add_edge", "prior", "represents_efficiency_window", "reference"],
        ["add_edge", "pause", "proposes_pausing_cognitive_process", "process"],
        ["add_edge", "escalation", "about_context", "checkin"],
        ["add_edge", "escalation", "checks_cognitive_process", "process"],
        ["add_edge", "escalation", "recruits_task_set", "task_supervision"],
        ["add_edge", "escalation", "recruits_task_set", "task_pareto"],
        ["set_attr", "process", "status", "checking_in"],
        ["set_attr", "process", "continuation_authority", 0],
        ["set_attr", "episode", "cognitive_continuation_authority", 0],
    ]
    if signal is not None:
        effects.extend((
            ["add_edge", "checkin", "triggered_by_process_signal", signal],
            ["set_attr", signal, "supervision_processed", 1],
        ))
    return effects


def scheduled_checkin_rule():
    return {
        "name": "cs_open_checkin_when_independent_cognitive_lease_is_due",
        "area": "cognitive_supervision",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
            ["episode", "has_cognitive_process", "process"],
            ["process", "supervises_learning_plan_step", "step"],
            ["process", "pursues_goal", "goal"],
            ["process", "governed_by_cognitive_supervision_policy", "policy"],
            ["process", "has_reference_efficiency_window", "reference"],
        ],
        "where": And(
            Eq(A("process", "status"), L("monitoring")),
            Not(Lt(P0("policy", "cognitive_epoch"),
                   P0("process", "renew_before_epoch"))),
        ),
        "effects": checkin_effects("approximate_time"),
    }


def surprise_checkin_rule():
    outside = Or(
        Lt(P0("signal", "observed_units"),
           P0("signal", "expected_lower_units")),
        Gt(P0("signal", "observed_units"),
           P0("signal", "expected_upper_units")),
    )
    return {
        "name": "cs_open_checkin_on_explicit_expected_envelope_departure",
        "area": "cognitive_supervision",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
            ["episode", "has_cognitive_process", "process"],
            ["process", "supervises_learning_plan_step", "step"],
            ["process", "pursues_goal", "goal"],
            ["process", "governed_by_cognitive_supervision_policy", "policy"],
            ["process", "has_reference_efficiency_window", "reference"],
            ["process", "observes_process_signal", "signal"],
        ],
        "where": And(
            Eq(A("process", "status"), L("monitoring")),
            Eq(P0("signal", "supervision_processed"), L(0)),
            outside,
        ),
        "effects": checkin_effects(
            "outside_expected_bounds", signal="signal"
        ),
    }


def mark_checkin_parallel_contexts_rule():
    """Backfill the scheduler capability on retained pre-upgrade check-ins."""
    return {
        "name": "cs_mark_checkin_escalation_parallel_contexts",
        "area": "cognitive_supervision",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["escalation", "checks_cognitive_process", "process"],
            ["escalation", "about_context", "checkin"],
        ],
        "where": And(
            Eq(A("escalation", "reason"), L("cognitive_process_checkin")),
            Eq(P0("escalation", "parallel_contexts"), L(0)),
        ),
        "effects": [
            ["set_attr", "escalation", "parallel_contexts", 1],
        ],
    }


def mint_goal_dimension_values_rule():
    current_delta = Minus(
        P0("baseline", "observed_progress_units"),
        P0("baseline", "baseline_progress_units"),
    )
    current_effort = Max(L(1), P0("checkin", "effort_units"))
    previous_effort = Max(L(1), P0("baseline", "previous_effort_units"))
    current_rate = Mul(current_delta, previous_effort)
    previous_rate = Mul(
        P0("baseline", "previous_progress_units"), current_effort
    )
    known = Filter(
        Neighbours("current", "has_pareto_value"), "known_value",
        Exists(
            Neighbours("known_value", "measures_goal"), "known_goal",
            Eq(V("known_goal"), V("goal")),
        ),
    )
    effects = []
    for candidate, raw in (
        ("current", current_rate), ("prior", previous_rate),
        ("pause", L(0)),
    ):
        value = f"{candidate}_goal_value"
        effects.extend((
            ["add_node", value, "ParetoValue", {
                "dimension_ordinal": 0,
                "raw_value": T(raw),
                "signed_value": T(raw),
                "verified": 1,
                "integer_native": 1,
            }],
            ["add_edge", candidate, "has_pareto_value", value],
            ["add_edge", value, "measures_goal", "goal"],
        ))
    return {
        "name": "cs_mint_one_pareto_dimension_per_reachable_goal",
        "area": "cognitive_supervision",
        "latency_class": "soft_realtime",
        "order": -10,
        "batch": True,
        "comment": "Every reachable Goal remains an independent Pareto "
        "dimension; effort changes its marginal rate but never weights or "
        "sums it with another goal.",
        "match": [
            ["process", "has_cognitive_checkin", "checkin"],
            ["checkin", "has_efficiency_pareto_profile", "profile"],
            ["profile", "has_incumbent_pareto_candidate", "current"],
            ["profile", "has_pareto_candidate", "prior"],
            ["profile", "has_pareto_candidate", "pause"],
            ["process", "has_cognitive_goal_baseline", "baseline"],
            ["baseline", "measures_goal", "goal"],
        ],
        "where": And(
            Eq(A("checkin", "status"), L("open")),
            Eq(A("prior", "kind"), L("previous_cognitive_efficiency_window")),
            Eq(A("pause", "kind"), L("pause_and_replan")),
            Eq(Count(known), L(0)),
        ),
        "effects": effects,
    }


def continue_rule():
    span = Max(L(1), P0("episode", "development_evidence_window"))
    return {
        "name": "cs_renew_lease_only_after_nondominated_productive_checkin",
        "area": "cognitive_supervision",
        "latency_class": "soft_realtime",
        "order": 10,
        "batch": False,
        "match": [
            ["episode", "has_cognitive_process", "process"],
            ["process", "governed_by_cognitive_supervision_policy", "policy"],
            ["process", "has_reference_efficiency_window", "reference"],
            ["process", "has_cognitive_checkin", "checkin"],
            ["checkin", "reviews_efficiency_window", "window"],
            ["checkin", "has_efficiency_pareto_profile", "profile"],
            ["profile", "has_incumbent_pareto_candidate", "current"],
            ["process", "supervises_learning_plan_step", "step"],
            ["process", "supervises_learning_capability", "instance"],
        ],
        "where": And(
            Eq(A("checkin", "status"), L("open")),
            Eq(P0("current", "dominated"), L(0)),
            Eq(Count(Neighbours("current", "has_pareto_value")),
               P0("profile", "dimension_count")),
            Not(Exists(
                Neighbours("profile", "has_pareto_candidate"),
                "alternative", candidate_dominates_current(),
            )),
            Gt(P0("checkin", "goal_progress_units"), L(0)),
        ),
        "effects": [
            ["del_edge", "process", "has_reference_efficiency_window", "reference"],
            ["add_edge", "process", "has_reference_efficiency_window", "window"],
            ["set_attr", "reference", "status", "superseded"],
            ["set_attr", "window", "status", "reference"],
            ["set_attr", "checkin", "status", "continued"],
            ["set_attr", "process", "status", "monitoring"],
            ["set_attr", "process", "continuation_authority", 1],
            ["set_attr", "process", "lease_generation", T(Plus(
                P0("process", "lease_generation"), L(1)
            ))],
            ["set_attr", "process", "last_checkin_epoch", T(P0(
                "policy", "cognitive_epoch"
            ))],
            ["set_attr", "process", "renew_before_epoch", T(Plus(
                P0("policy", "cognitive_epoch"), span
            ))],
            ["set_attr", "process", "next_checkin_epoch", T(Plus(
                P0("policy", "cognitive_epoch"), span
            ))],
            ["set_attr", "process", "checkin_span_units", T(span)],
            ["set_attr", "process", "baseline_effort_units", T(P0(
                "step", "evidence_spent_units"
            ))],
            ["set_attr", "process", "checkin_count", T(Plus(
                P0("process", "checkin_count"), L(1)
            ))],
            ["set_attr", "episode", "cognitive_continuation_authority", 1],
            ["set_attr", "episode", "cognitive_checkin_terminal", 0],
            ["set_attr", "profile", "status", "continued"],
        ],
    }


def advance_goal_baseline_after_continuation_rule():
    delta = Minus(
        P0("baseline", "observed_progress_units"),
        P0("baseline", "baseline_progress_units"),
    )
    return {
        "name": "cs_advance_each_goal_baseline_after_lease_renewal",
        "area": "cognitive_supervision",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["process", "has_cognitive_checkin", "checkin"],
            ["process", "has_cognitive_goal_baseline", "baseline"],
        ],
        "where": And(
            Eq(A("checkin", "status"), L("continued")),
            Eq(P0("baseline", "baseline_generation"),
               P0("checkin", "lease_generation")),
        ),
        "effects": [
            ["set_attr", "baseline", "previous_progress_units", T(delta)],
            ["set_attr", "baseline", "previous_effort_units", T(Max(
                L(1), P0("checkin", "effort_units")
            ))],
            ["set_attr", "baseline", "baseline_progress_units", T(P0(
                "baseline", "observed_progress_units"
            ))],
            ["set_attr", "baseline", "baseline_generation", T(P0(
                "process", "lease_generation"
            ))],
        ],
    }


def replan_effects():
    return [
        ["add_node", "residual", "LearningPlanResidual", {
            "status": "open",
            "kind": "inefficient_cognitive_process_window",
            "order_n": T(Plus(P0("process", "order_n"), L(1))),
            "evidence_spent_units": T(P0("checkin", "effort_units")),
            "causal_yield_units": T(P0("checkin", "causal_yield_units")),
            "integer_native": 1, "output_authority": 0,
        }],
        ["add_edge", "plan", "has_learning_plan_residual", "residual"],
        ["add_edge", "step", "has_learning_plan_residual", "residual"],
        ["add_edge", "residual", "about_learning_plan_step", "step"],
        ["add_edge", "residual", "raised_by_cognitive_checkin", "checkin"],
        ["set_attr", "checkin", "status", "replan_required"],
        ["set_attr", "process", "status", "replan_required"],
        ["set_attr", "process", "continuation_authority", 0],
        ["set_attr", "policy", "enabled", 0],
        ["set_attr", "episode", "cognitive_checkin_terminal", 1],
        ["set_attr", "episode", "cognitive_continuation_authority", 0],
        ["set_attr", "profile", "status", "replan_required"],
    ]


def dominated_replan_rule():
    return {
        "name": "cs_hold_marginally_dominated_process_for_replanning",
        "area": "cognitive_supervision",
        "latency_class": "soft_realtime",
        "order": 10,
        "batch": False,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["episode", "has_cognitive_process", "process"],
            ["process", "governed_by_cognitive_supervision_policy", "policy"],
            ["process", "has_cognitive_checkin", "checkin"],
            ["checkin", "has_efficiency_pareto_profile", "profile"],
            ["profile", "has_incumbent_pareto_candidate", "current"],
            ["current", "is_dominated_by_pareto_candidate", "alternative"],
            ["process", "supervises_learning_plan_step", "step"],
        ],
        "where": And(
            Eq(A("checkin", "status"), L("open")),
            Gt(P0("checkin", "goal_progress_units"), L(0)),
        ),
        "effects": replan_effects(),
    }


def unproductive_replan_rule():
    return {
        "name": "cs_hold_zero_yield_process_for_replanning",
        "area": "cognitive_supervision",
        "latency_class": "soft_realtime",
        "order": 10,
        "batch": False,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["episode", "has_cognitive_process", "process"],
            ["process", "governed_by_cognitive_supervision_policy", "policy"],
            ["process", "has_cognitive_checkin", "checkin"],
            ["checkin", "has_efficiency_pareto_profile", "profile"],
            ["profile", "has_incumbent_pareto_candidate", "current"],
            ["process", "supervises_learning_plan_step", "step"],
        ],
        "where": And(
            Eq(A("checkin", "status"), L("open")),
            Eq(Count(Neighbours("current", "has_pareto_value")),
               P0("profile", "dimension_count")),
            Not(Gt(P0("checkin", "goal_progress_units"), L(0))),
        ),
        "effects": replan_effects(),
    }


def manifest():
    productions = (
        ("episode_process", "Node", "has_cognitive_process", "CognitiveProcess"),
        ("process_policy", "CognitiveProcess", "governed_by_cognitive_supervision_policy", "CognitiveSupervisionPolicy"),
        ("process_plan", "CognitiveProcess", "supervises_learning_plan", "LearningPlan"),
        ("process_step", "CognitiveProcess", "supervises_learning_plan_step", "LearningPlanStep"),
        ("process_capability", "CognitiveProcess", "supervises_learning_capability", "Node"),
        ("process_goal", "CognitiveProcess", "pursues_goal", "Goal"),
        ("supervised_goal", "CognitiveProcess", "supervises_goal", "Goal"),
        ("goal_subgoal", "Goal", "has_subgoal", "Goal"),
        ("process_goal_baseline", "CognitiveProcess", "has_cognitive_goal_baseline", "CognitiveGoalBaseline"),
        ("baseline_goal", "CognitiveGoalBaseline", "measures_goal", "Goal"),
        ("process_reference", "CognitiveProcess", "has_reference_efficiency_window", "CognitiveEfficiencyWindow"),
        ("process_signal", "CognitiveProcess", "observes_process_signal", "CognitiveProcessSignal"),
        ("process_checkin", "CognitiveProcess", "has_cognitive_checkin", "CognitiveCheckIn"),
        ("checkin_profile", "CognitiveCheckIn", "has_efficiency_pareto_profile", "ParetoProfile"),
        ("checkin_signal", "CognitiveCheckIn", "triggered_by_process_signal", "CognitiveProcessSignal"),
        ("continuation_process", "SystemTwoEscalation", "continues_cognitive_process", "CognitiveProcess"),
        ("checkin_process", "SystemTwoEscalation", "checks_cognitive_process", "CognitiveProcess"),
        ("residual_checkin", "LearningPlanResidual", "raised_by_cognitive_checkin", "CognitiveCheckIn"),
    )
    return {
        "id": "cognitive_supervision",
        "version": "3.0.0",
        "depends_on": ["dual_process_core", "cognitive_pareto"],
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "description": "Every active process pursues the existing generic "
        "order-N Goal tree under a renewable integer lease. Approximate "
        "time and prediction-envelope departures trigger a graph-native, "
        "per-goal marginal-efficiency check-in without scalarisation.",
        "nodes": [
            {"local_id": 1, "type": "AsyncDaemonCycleBudget", "attrs": {
                # The existing supervision seed already uses a unit lease as
                # its least admissible temporal extent. This is graph data,
                # not a Python ``max_steps`` default.
                "status": "active", "quantum_units": 1,
                "observed_lease_generation": -1, "adjustment_count": 0,
                "integer_native": 1, "output_authority": 0,
            }},
            {"local_id": 2, "type": "CognitiveSupervisionAnchor", "attrs": {
                "kind": "asynchronous_default_mode", "integer_native": 1,
                "output_authority": 0,
            }},
        ],
        "edges": [
            {"src": {"local": 2}, "type": "has_async_daemon_cycle_budget",
             "tgt": {"local": 1}, "attrs": {}},
        ],
        "productions": [production(*row) for row in productions],
        "rules": [
            attach_rule(), expand_order_n_goal_tree_rule(),
            instantiate_goal_baseline_rule(), observe_goal_progress_rule(),
            scheduled_checkin_rule(), surprise_checkin_rule(),
            mark_checkin_parallel_contexts_rule(),
            mint_goal_dimension_values_rule(), continue_rule(),
            advance_goal_baseline_after_continuation_rule(),
            dominated_replan_rule(), unproductive_replan_rule(),
            adjust_daemon_cycle_budget_rule(),
        ],
    }


def main():
    output = ROOT / "seeds" / "cognitive_supervision.json"
    output.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output} ({len(manifest()['rules'])} rules)")


if __name__ == "__main__":
    main()
