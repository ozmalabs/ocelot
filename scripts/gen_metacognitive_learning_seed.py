#!/usr/bin/env python3
"""Generate the domain-neutral metacognitive learning-policy faculty.

A first-order LearningPlan chooses experiments.  This seed treats that plan as
an executable program whose own predictions can fail.  Exhausted effort with
no causal yield mints a LearningPlanResidual; complete integer Pareto points
then compare the current policy with every productive alternative.  A unique
frontier counterexample may revise the plan.  Several incomparable
counterexamples request a discriminating experiment instead of using insertion
order or a scalar score.

The faculty is intentionally ignorant of bodies, joints, games and tasks.  It
uses only the general LearningPlan/LearningPlanStep receipt contract.  Domain
seeds publish those facts and enact the resulting typed revision edges.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gen_humanoid_adaptation_seed import (
    A,
    And,
    Count,
    Eq,
    Exists,
    Filter,
    Gt,
    If,
    L,
    Lt,
    Minus,
    Neg,
    Neighbours,
    Not,
    Or,
    PI0,
    Plus,
    T,
    V,
)


P0 = PI0


def learning_policies(plan: str = "plan"):
    return Neighbours(plan, "has_active_metacognitive_learning_policy")


def alternatives(plan: str = "plan"):
    return Neighbours(plan, "has_learning_policy_alternative")


def productive_alternatives(plan: str = "plan"):
    return Filter(
        alternatives(plan),
        "productive_alternative",
        And(
            Gt(P0("productive_alternative", "causal_yield_units"), L(0)),
            Eq(P0("productive_alternative", "eligible"), L(1)),
        ),
    )


def productive_steps(plan: str = "plan"):
    return Filter(
        Neighbours(plan, "has_learning_plan_step"),
        "productive_step",
        And(
            Gt(
                Minus(
                    P0("productive_step", "successful_evidence_units"),
                    P0("productive_step", "budget_success_baseline"),
                ),
                L(0),
            ),
            Or(
                Eq(A("productive_step", "status"), L("ready")),
                Eq(A("productive_step", "status"), L("active")),
            ),
            Eq(Count(active_counterexample_holds("productive_step")), L(0)),
        ),
    )


def active_counterexample_holds(step: str = "step"):
    return Filter(
        Neighbours(step, "has_learning_policy_counterexample_hold"),
        "counterexample_hold",
        Eq(A("counterexample_hold", "status"), L("active")),
    )


def open_residuals_for_step(step: str = "step"):
    return Filter(
        Neighbours(step, "has_learning_plan_residual"),
        "known_residual",
        Not(Eq(A("known_residual", "status"), L("resolved"))),
    )


def candidate_for_alternative(profile: str = "profile", alternative: str = "alternative"):
    return Filter(
        Neighbours(profile, "has_pareto_candidate"),
        "known_candidate",
        Exists(
            Neighbours("known_candidate", "represents_learning_policy_alternative"),
            "known_alternative",
            Eq(V("known_alternative"), V(alternative)),
        ),
    )


def published_alternatives(profile: str = "profile"):
    return Filter(
        Neighbours(profile, "has_pareto_candidate"),
        "published_candidate",
        Eq(A("published_candidate", "kind"), L("learning_policy_alternative")),
    )


def frontier_dominators(incumbent: str = "incumbent"):
    return Filter(
        Neighbours(incumbent, "is_dominated_by_pareto_candidate"),
        "dominator",
        Eq(
            Count(Neighbours("dominator", "is_dominated_by_pareto_candidate")),
            L(0),
        ),
    )


def pareto_values(candidate: str, raw_values: tuple[dict, ...]) -> list[list]:
    effects: list[list] = []
    for ordinal, (raw, signed) in enumerate((
        (raw_values[0], raw_values[0]),
        (raw_values[1], raw_values[1]),
        (raw_values[2], Neg(raw_values[2])),
        (raw_values[3], Neg(raw_values[3])),
    )):
        value = f"{candidate}_value_{ordinal}"
        effects.extend((
            ["add_node", value, "ParetoValue", {
                "dimension_ordinal": ordinal,
                "raw_value": T(raw),
                "signed_value": T(signed),
                "verified": 1,
                "integer_native": 1,
            }],
            ["add_edge", candidate, "has_pareto_value", value],
        ))
    return effects


def attach_policy_rule() -> dict:
    return {
        "name": "ml_attach_metacognitive_policy_to_learning_plan",
        "area": "metacognitive_learning",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A learning plan is itself a revisable program. The first "
        "meta-level is materialized lazily when a plan exists.",
        "match": [["episode", "has_self_directed_learning_plan", "plan"]],
        "where": Eq(Count(learning_policies()), L(0)),
        "effects": [
            ["add_node", "policy", "MetacognitiveLearningPolicy", {
                "status": "active",
                "order_n": 1,
                "residual_count": 0,
                "revision_count": 0,
                "discrimination_count": 0,
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "plan", "has_metacognitive_learning_policy", "policy"],
            ["add_edge", "plan", "has_active_metacognitive_learning_policy", "policy"],
        ],
    }


def publish_step_alternative_rule() -> dict:
    existing = Filter(
        alternatives(),
        "known_alternative",
        Exists(
            Neighbours("known_alternative", "proposes_learning_plan_step"),
            "known_step",
            Eq(V("known_step"), V("step")),
        ),
    )
    eligible = If(
        And(
            Or(Eq(A("step", "status"), L("ready")),
               Eq(A("step", "status"), L("active"))),
            Eq(Count(active_counterexample_holds()), L(0)),
        ),
        L(1), L(0),
    )
    return {
        "name": "ml_publish_learning_step_as_policy_alternative",
        "area": "metacognitive_learning",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_active_metacognitive_learning_policy", "policy"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            Eq(A("policy", "status"), L("deliberating")),
            Eq(Count(existing), L(0)),
        ),
        "effects": [
            ["add_node", "alternative", "LearningPolicyAlternative", {
                "kind": "continue_learning_step",
                "goal": T(A("step", "goal")),
                "causal_yield_units": T(Minus(
                    P0("instance", "success_count"),
                    P0("step", "budget_success_baseline"),
                )),
                "context_units": T(P0("step", "context_evidence_units")),
                "failure_burden_units": T(P0("instance", "failure_count")),
                "experiment_cost_units": T(P0("step", "evidence_spent_units")),
                "last_success_count": T(P0("instance", "success_count")),
                "last_failure_count": T(P0("instance", "failure_count")),
                "eligible": T(eligible),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "plan", "has_learning_policy_alternative", "alternative"],
            ["add_edge", "alternative", "proposes_learning_plan_step", "step"],
            ["add_edge", "alternative", "predicts_learning_capability", "instance"],
        ],
    }


def refresh_step_alternative_rule() -> dict:
    eligible = If(
        And(
            Or(Eq(A("step", "status"), L("ready")),
               Eq(A("step", "status"), L("active"))),
            Eq(Count(active_counterexample_holds()), L(0)),
        ),
        L(1), L(0),
    )
    changed = Or(
        Not(Eq(P0("alternative", "last_success_count"),
               P0("instance", "success_count"))),
        Not(Eq(P0("alternative", "last_failure_count"),
               P0("instance", "failure_count"))),
        Not(Eq(P0("alternative", "context_units"),
               P0("step", "context_evidence_units"))),
        Not(Eq(P0("alternative", "eligible"), eligible)),
    )
    return {
        "name": "ml_refresh_learning_policy_alternative_from_receipts",
        "area": "metacognitive_learning",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["plan", "has_active_metacognitive_learning_policy", "policy"],
            ["plan", "has_learning_policy_alternative", "alternative"],
            ["alternative", "proposes_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            Eq(A("policy", "status"), L("deliberating")),
            changed,
        ),
        "effects": [
            ["set_attr", "alternative", "causal_yield_units", T(Minus(
                P0("instance", "success_count"),
                P0("step", "budget_success_baseline"),
            ))],
            ["set_attr", "alternative", "context_units",
             T(P0("step", "context_evidence_units"))],
            ["set_attr", "alternative", "failure_burden_units",
             T(P0("instance", "failure_count"))],
            ["set_attr", "alternative", "experiment_cost_units",
             T(P0("step", "evidence_spent_units"))],
            ["set_attr", "alternative", "last_success_count",
             T(P0("instance", "success_count"))],
            ["set_attr", "alternative", "last_failure_count",
             T(P0("instance", "failure_count"))],
            ["set_attr", "alternative", "eligible", T(eligible)],
        ],
    }


def detect_plan_residual_rule() -> dict:
    incumbent_raw = (
        Minus(P0("instance", "success_count"),
              P0("step", "budget_success_baseline")),
        P0("step", "context_evidence_units"),
        P0("instance", "failure_count"),
        P0("step", "evidence_spent_units"),
    )
    effects: list[list] = [
        ["add_node", "residual", "LearningPlanResidual", {
            "kind": "effort_without_causal_learning_payoff",
            "status": "open",
            "order_n": T(P0("policy", "order_n")),
            "evidence_spent_units": T(P0("step", "evidence_spent_units")),
            "causal_yield_units": 0,
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "plan", "has_learning_plan_residual", "residual"],
        ["add_edge", "step", "has_learning_plan_residual", "residual"],
        ["add_edge", "residual", "about_learning_plan_step", "step"],
        ["add_edge", "residual", "raised_under_metacognitive_policy", "policy"],
        ["add_node", "profile", "ParetoProfile", {
            "kind": "metacognitive_learning_policy_revision",
            "status": "collecting_candidates",
            "dimension_count": 4,
            "scalarized": 0,
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "residual", "has_learning_policy_pareto_profile", "profile"],
        ["add_edge", "plan", "has_learning_policy_pareto_profile", "profile"],
        ["add_node", "incumbent", "ParetoCandidate", {
            "kind": "incumbent_learning_policy",
            "dominated": 0,
            "verified": 1,
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "profile", "has_pareto_candidate", "incumbent"],
        ["add_edge", "profile", "has_incumbent_pareto_candidate", "incumbent"],
        ["add_edge", "incumbent", "represents_learning_plan_step", "step"],
        ["add_node", "task_set_meta", "SystemTwoTaskSet", {
            "area": "metacognitive_learning", "enabled": 1,
            "integer_native": 1,
        }],
        ["add_node", "task_set_pareto", "SystemTwoTaskSet", {
            "area": "cognitive_pareto", "enabled": 1,
            "integer_native": 1,
        }],
        ["add_node", "escalation", "SystemTwoEscalation", {
            "status": "requested",
            "reason": "learning_plan_prediction_error",
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "escalation", "about_context", "residual"],
        ["add_edge", "escalation", "recruits_task_set", "task_set_meta"],
        ["add_edge", "escalation", "recruits_task_set", "task_set_pareto"],
        ["set_attr", "policy", "status", "deliberating"],
        ["set_attr", "policy", "residual_count", T(Plus(
            P0("policy", "residual_count"), L(1)
        ))],
    ]
    effects.extend(pareto_values("incumbent", incumbent_raw))
    return {
        "name": "ml_detect_exhausted_zero_yield_learning_policy",
        "area": "metacognitive_learning",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "An exhausted body-derived budget with no new causal "
        "success falsifies the current learning-policy prediction when a "
        "productive frontier alternative exists.",
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_active_metacognitive_learning_policy", "policy"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            Not(Lt(P0("step", "evidence_spent_units"),
                   P0("step", "evidence_budget_units"))),
            Eq(P0("instance", "success_count"),
               P0("step", "budget_success_baseline")),
            Gt(Count(productive_steps()), L(0)),
            Eq(Count(open_residuals_for_step()), L(0)),
        ),
        "effects": effects,
    }


def publish_policy_candidate_rule() -> dict:
    raw = (
        P0("alternative", "causal_yield_units"),
        P0("alternative", "context_units"),
        P0("alternative", "failure_burden_units"),
        P0("alternative", "experiment_cost_units"),
    )
    effects: list[list] = [
        ["add_node", "candidate", "ParetoCandidate", {
            "kind": "learning_policy_alternative",
            # Keep the causal/cost coordinates on the candidate as well as in
            # its ParetoValue children.  This is not a scalarisation: it is a
            # lossless local projection that lets a learned graph Program
            # interrogate an otherwise-incomparable frontier without a host
            # joining the candidate back to its evidence rows.
            "causal_yield_units": T(P0(
                "alternative", "causal_yield_units"
            )),
            "experiment_cost_units": T(P0(
                "alternative", "experiment_cost_units"
            )),
            "dominated": 0,
            "verified": 1,
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "profile", "has_pareto_candidate", "candidate"],
        ["add_edge", "candidate", "represents_learning_policy_alternative", "alternative"],
    ]
    effects.extend(pareto_values("candidate", raw))
    return {
        "name": "ml_publish_productive_policy_counterexample",
        "area": "metacognitive_learning",
        "latency_class": "soft_realtime",
        "batch": True,
        "match": [
            ["plan", "has_learning_policy_pareto_profile", "profile"],
            ["profile", "has_incumbent_pareto_candidate", "incumbent"],
            ["incumbent", "represents_learning_plan_step", "current_step"],
            ["plan", "has_learning_policy_alternative", "alternative"],
            ["alternative", "proposes_learning_plan_step", "step"],
        ],
        "where": And(
            Eq(A("profile", "status"), L("collecting_candidates")),
            Gt(P0("alternative", "causal_yield_units"), L(0)),
            Eq(P0("alternative", "eligible"), L(1)),
            Not(Eq(V("step"), V("current_step"))),
            Eq(Count(candidate_for_alternative()), L(0)),
        ),
        "effects": effects,
    }


def apply_unique_revision_rule() -> dict:
    frontier = frontier_dominators()
    return {
        "name": "ml_apply_unique_dominating_learning_policy_revision",
        "area": "metacognitive_learning",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "Only one verified non-dominated counterexample may enact "
        "a revision. Incomparable alternatives require discrimination.",
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_active_metacognitive_learning_policy", "policy"],
            ["plan", "has_learning_policy_pareto_profile", "profile"],
            ["profile", "has_incumbent_pareto_candidate", "incumbent"],
            ["incumbent", "represents_learning_plan_step", "current_step"],
            ["current_step", "plans_learning_capability", "current_instance"],
            ["incumbent", "is_dominated_by_pareto_candidate", "candidate"],
            ["candidate", "represents_learning_policy_alternative", "alternative"],
            ["alternative", "proposes_learning_plan_step", "next_step"],
            ["next_step", "plans_learning_capability", "next_instance"],
            ["current_step", "has_learning_plan_residual", "residual"],
        ],
        "where": And(
            Eq(A("residual", "status"), L("open")),
            Not(Eq(A("next_instance", "status"), L("mastered"))),
            Eq(Count(published_alternatives()), Count(productive_alternatives())),
            Eq(Count(frontier), L(1)),
            Exists(frontier, "frontier_candidate",
                   Eq(V("frontier_candidate"), V("candidate"))),
        ),
        "effects": [
            ["add_node", "revision", "LearningPlanRevision", {
                "kind": "redirect_to_productive_learning_frontier",
                "reason": "verified_pareto_counterexample",
                "status": "enacted",
                "order_n": T(P0("policy", "order_n")),
                "redirect_success_baseline": T(P0(
                    "next_instance", "success_count"
                )),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "plan", "has_learning_plan_revision", "revision"],
            ["add_edge", "revision", "revises_learning_plan_step", "current_step"],
            ["add_edge", "revision", "redirects_to_learning_plan_step", "next_step"],
            ["add_edge", "revision", "resolves_learning_plan_residual", "residual"],
            ["add_edge", "current_instance",
             "reassess_after_learning_capability", "next_instance"],
            ["del_edge", "episode", "has_active_embodied_developmental_capability",
             "current_instance"],
            ["del_edge", "plan", "has_selected_learning_plan_step", "current_step"],
            ["set_attr", "current_step", "status", "meta_suspended"],
            ["set_attr", "current_instance", "status", "meta_suspended"],
            ["set_attr", "next_step", "status", "ready"],
            ["set_attr", "residual", "status", "resolved"],
            ["set_attr", "profile", "status", "revision_enacted"],
            ["set_attr", "policy", "status", "active"],
            ["set_attr", "policy", "revision_count", T(Plus(
                P0("policy", "revision_count"), L(1)
            ))],
            ["set_attr", "plan", "replan_count", T(Plus(
                P0("plan", "replan_count"), L(1)
            ))],
        ],
    }


def request_discrimination_rule() -> dict:
    frontier = frontier_dominators()
    existing = Neighbours("residual", "has_learning_policy_discrimination_request")
    return {
        "name": "ml_request_discrimination_between_incomparable_policy_revisions",
        "area": "metacognitive_learning",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["plan", "has_active_metacognitive_learning_policy", "policy"],
            ["plan", "has_learning_policy_pareto_profile", "profile"],
            ["profile", "has_incumbent_pareto_candidate", "incumbent"],
            ["residual", "has_learning_policy_pareto_profile", "profile"],
        ],
        "where": And(
            Eq(A("residual", "status"), L("open")),
            Eq(Count(published_alternatives()), Count(productive_alternatives())),
            Gt(Count(frontier), L(1)),
            Eq(Count(existing), L(0)),
        ),
        "effects": [
            ["add_node", "request", "LearningPolicyDiscriminationRequest", {
                "status": "requested",
                "kind": "distinguish_incomparable_learning_policies",
                "candidate_count": T(Count(frontier)),
                "order_n": T(P0("policy", "order_n")),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "residual", "has_learning_policy_discrimination_request",
             "request"],
            ["set_attr", "policy", "status", "awaiting_discrimination"],
            ["set_attr", "policy", "discrimination_count", T(Plus(
                P0("policy", "discrimination_count"), L(1)
            ))],
        ],
    }


def reopen_after_revision_condition_rule() -> dict:
    return {
        "name": "ml_reopen_suspended_step_after_revision_condition_changes",
        "area": "metacognitive_learning",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
            ["instance", "reassess_after_learning_capability", "condition"],
            ["plan", "has_learning_plan_revision", "revision"],
            ["revision", "revises_learning_plan_step", "step"],
            ["revision", "redirects_to_learning_plan_step", "condition_step"],
            ["condition_step", "plans_learning_capability", "condition"],
        ],
        "where": And(
            Eq(A("instance", "status"), L("meta_suspended")),
            Eq(A("condition", "status"), L("mastered")),
            Gt(P0("condition", "success_count"),
               P0("revision", "redirect_success_baseline")),
        ),
        "effects": [
            ["del_edge", "instance",
             "reassess_after_learning_capability", "condition"],
            ["set_attr", "instance", "status", "available"],
            ["set_attr", "step", "status", "ready"],
        ],
    }


def escalate_failed_revision_order_rule() -> dict:
    children = Neighbours("policy", "has_higher_order_metacognitive_policy")
    return {
        "name": "ml_materialize_next_meta_order_after_revision_fails",
        "area": "metacognitive_learning",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The reflective tower is order-N and lazy. A failed "
        "revision materializes exactly one higher order; ordinary learning "
        "does not pay for unused meta-levels.",
        "match": [
            ["plan", "has_active_metacognitive_learning_policy", "policy"],
            ["plan", "has_learning_plan_revision", "revision"],
            ["revision", "redirects_to_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            Eq(A("revision", "status"), L("enacted")),
            Not(Lt(P0("step", "evidence_spent_units"),
                   P0("step", "evidence_budget_units"))),
            Eq(P0("instance", "success_count"),
               P0("step", "budget_success_baseline")),
            Eq(Count(children), L(0)),
        ),
        "effects": [
            ["add_node", "higher", "MetacognitiveLearningPolicy", {
                "status": "active",
                "order_n": T(Plus(P0("policy", "order_n"), L(1))),
                "residual_count": 0,
                "revision_count": 0,
                "discrimination_count": 0,
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "policy", "has_higher_order_metacognitive_policy", "higher"],
            ["del_edge", "plan", "has_active_metacognitive_learning_policy", "policy"],
            ["add_edge", "plan", "has_active_metacognitive_learning_policy", "higher"],
            ["set_attr", "policy", "status", "superseded_by_higher_order"],
            ["set_attr", "revision", "status", "counterexample_observed"],
        ],
    }


def manifest() -> dict:
    productions = (
        ("episode_plan", "Node", "has_self_directed_learning_plan", "LearningPlan"),
        ("plan_step", "LearningPlan", "has_learning_plan_step", "LearningPlanStep"),
        ("step_capability", "LearningPlanStep", "plans_learning_capability", "Node"),
        ("selected_step", "LearningPlan", "has_selected_learning_plan_step", "LearningPlanStep"),
        ("active_capability", "Node", "has_active_embodied_developmental_capability", "Node"),
        ("plan_policy", "LearningPlan", "has_metacognitive_learning_policy", "MetacognitiveLearningPolicy"),
        ("plan_active_policy", "LearningPlan", "has_active_metacognitive_learning_policy", "MetacognitiveLearningPolicy"),
        ("higher_policy", "MetacognitiveLearningPolicy", "has_higher_order_metacognitive_policy", "MetacognitiveLearningPolicy"),
        ("plan_alternative", "LearningPlan", "has_learning_policy_alternative", "LearningPolicyAlternative"),
        ("alternative_step", "LearningPolicyAlternative", "proposes_learning_plan_step", "LearningPlanStep"),
        ("alternative_capability", "LearningPolicyAlternative", "predicts_learning_capability", "Node"),
        ("plan_residual", "LearningPlan", "has_learning_plan_residual", "LearningPlanResidual"),
        ("step_residual", "LearningPlanStep", "has_learning_plan_residual", "LearningPlanResidual"),
        ("residual_step", "LearningPlanResidual", "about_learning_plan_step", "LearningPlanStep"),
        ("residual_policy", "LearningPlanResidual", "raised_under_metacognitive_policy", "MetacognitiveLearningPolicy"),
        ("residual_profile", "LearningPlanResidual", "has_learning_policy_pareto_profile", "ParetoProfile"),
        ("plan_profile", "LearningPlan", "has_learning_policy_pareto_profile", "ParetoProfile"),
        ("candidate_step", "ParetoCandidate", "represents_learning_plan_step", "LearningPlanStep"),
        ("candidate_alternative", "ParetoCandidate", "represents_learning_policy_alternative", "LearningPolicyAlternative"),
        ("plan_revision", "LearningPlan", "has_learning_plan_revision", "LearningPlanRevision"),
        ("revision_step", "LearningPlanRevision", "revises_learning_plan_step", "LearningPlanStep"),
        ("revision_redirect", "LearningPlanRevision", "redirects_to_learning_plan_step", "LearningPlanStep"),
        ("revision_residual", "LearningPlanRevision", "resolves_learning_plan_residual", "LearningPlanResidual"),
        ("reassessment_condition", "Node", "reassess_after_learning_capability", "Node"),
        ("counterexample_hold", "LearningPlanStep", "has_learning_policy_counterexample_hold", "LearningPolicyCounterexampleHold"),
        ("residual_discrimination", "LearningPlanResidual", "has_learning_policy_discrimination_request", "LearningPolicyDiscriminationRequest"),
    )
    return {
        "id": "metacognitive_learning",
        "version": "1.1.0",
        "depends_on": ["cognitive_pareto", "dual_process_core"],
        "area": "metacognitive_learning",
        "latency_class": "soft_realtime",
        "description": "Order-N graph-native metacognition over executable "
        "learning plans: prediction-error residuals, non-scalar policy "
        "counterexamples, typed plan revision, discrimination requests, and "
        "conditional reopening. All cognitive quantities are integer.",
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": f"metacognitive_learning:{name}",
                "src": {"type": src, "var": "src"},
                "edge_type": edge,
                "tgt": {"type": tgt, "var": "tgt"},
            }
            for name, src, edge, tgt in productions
        ],
        "rules": [
            attach_policy_rule(),
            publish_step_alternative_rule(),
            refresh_step_alternative_rule(),
            detect_plan_residual_rule(),
            publish_policy_candidate_rule(),
            apply_unique_revision_rule(),
            request_discrimination_rule(),
            reopen_after_revision_condition_rule(),
            escalate_failed_revision_order_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "metacognitive_learning.json"
    payload = manifest()
    output.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
