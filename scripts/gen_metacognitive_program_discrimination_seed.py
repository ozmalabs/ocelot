#!/usr/bin/env python3
"""Generate graph-native execution of learned classifiers over policy tails.

The metacognitive learning faculty deliberately refuses to scalarise several
Pareto-incomparable learning routes.  This faculty answers that *request for a
discriminator* with an accepted graph Program.  The graph sweeps the learned
classifier's boundary from the identity value until a first admissible route
appears; only a unique first crossing may revise the plan.  A tied crossing is
retained as underdetermination, never broken by insertion order.

The host may restore an already learned Program and report raw receipts.  It
does not choose a boundary, candidate, revision, or outcome.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from domains.prog_synthesis import _FUEL as PROGRAM_EXECUTION_FUEL

from scripts.gen_humanoid_adaptation_seed import (
    A,
    And,
    Count,
    Eq,
    Filter,
    Gt,
    L,
    Neighbours,
    Not,
    PI0,
    Plus,
    T,
    V,
)


P0 = PI0


def classifier_fuel() -> int:
    """Use the synthesis evaluator's shared execution envelope."""
    return PROGRAM_EXECUTION_FUEL


def is_classifier(program: str = "program") -> dict:
    return Eq(A(program, "faculty_kind"), L("threshold_classifier"))


def held_classifiers(agent: str = "agent") -> dict:
    return Filter(
        Neighbours(agent, "holds_faculty"),
        "held_classifier",
        is_classifier("held_classifier"),
    )


def request_missing_classifier_faculty_rule() -> dict:
    """State the missing capability and evidence; never supply its program."""
    examples = (
        ({"processed": 100, "progress": 20, "micros": 300,
          "threshold": 10}, 0),
        ({"processed": 201, "progress": 20, "micros": 300,
          "threshold": 10}, 300),
        ({"processed": 61, "progress": 20, "micros": 7,
          "threshold": 3}, 7),
        ({"processed": 60, "progress": 20, "micros": 11,
          "threshold": 3}, 0),
    )
    effects = [
        ["add_node", "need", "FacultyNeed", {
            "status": "requested",
            "kind": "threshold_classifier",
            "program_name": "cost_excess",
            "request": (
                "write a function cost_excess that returns micros when "
                "processed is more than threshold times progress otherwise zero"
            ),
            "order_n": 1,
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "agent", "has_faculty_need", "need"],
    ]
    for ordinal, (inputs, expected) in enumerate(examples):
        node = f"example_{ordinal}"
        effects.extend((
            ["add_node", node, "FacultyExample", {
                "ordinal": ordinal,
                "inputs_json": json.dumps(
                    inputs, sort_keys=True, separators=(",", ":")
                ),
                "expected": expected,
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "need", "has_faculty_example", node],
        ))
    return {
        "name": "mpd_request_missing_discrimination_faculty",
        "area": "metacognitive_learning",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "A missing classifier becomes a general FacultyNeed. "
        "The graph supplies observed examples, not an implementation.",
        "match": [["agent", "has_embodied_development_episode", "episode"]],
        "where": And(
            Eq(Count(held_classifiers()), L(0)),
            Eq(Count(Filter(
                Neighbours("agent", "has_faculty_need"),
                "known_need",
                Eq(A("known_need", "kind"), L("threshold_classifier")),
            )), L(0)),
        ),
        "effects": effects,
    }


def mkdict(*items: dict) -> dict:
    return {"type": "MkDict", "items": list(items)}


def classifier_result(
    candidate: str = "candidate",
    request: str = "request",
    root: str = "root",
) -> dict:
    """Execute the held classifier on integer evidence in graph context."""
    return program_result(
        P0(candidate, "experiment_cost_units"),
        P0(candidate, "causal_yield_units"),
        L(1),
        P0(request, "classifier_threshold"),
        root,
    )


def program_result(
    processed: dict,
    progress: dict,
    micros: dict,
    threshold: dict,
    root: str = "root",
) -> dict:
    return {
        "type": "ProgEval",
        "prog": V(root),
        "env": mkdict(
            L("processed"), processed,
            L("progress"), progress,
            L("micros"), micros,
            L("threshold"), threshold,
        ),
        "oracles": None,
        "fuel": classifier_fuel(),
        "field": "result",
    }


def classify_active_learning_excess_rule() -> dict:
    result = program_result(
        P0("instance", "attempt_count"),
        P0("instance", "success_count"),
        L(1),
        P0("episode", "development_evidence_window"),
    )
    return {
        "name": "mpd_classify_active_learning_effort_excess",
        "area": "metacognitive_learning",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Apply the learned Program to live causal-learning "
        "receipts. The threshold is the situated body's own evidence window; "
        "the graph publishes an excess fact but grants no motor authority.",
        "match": [
            ["agent", "holds_faculty", "program"],
            ["program", "ir_subgraph", "root"],
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            is_classifier(),
            Eq(P0("instance", "classifier_effort_excess"), L(0)),
            Gt(P0("instance", "attempt_count"), L(0)),
            Gt(result, L(0)),
        ),
        "effects": [
            ["add_node", "assessment", "LearningPolicyClassifierAssessment", {
                "status": "excess",
                "kind": "effort_exceeds_causal_yield_window",
                "processed_units": T(P0("instance", "attempt_count")),
                "progress_units": T(P0("instance", "success_count")),
                "threshold_units": T(P0(
                    "episode", "development_evidence_window"
                )),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "step", "has_learning_classifier_assessment", "assessment"],
            ["add_edge", "assessment", "executed_classifier", "program"],
            ["set_attr", "instance", "classifier_effort_excess", 1],
        ],
    }


def clear_active_learning_excess_rule() -> dict:
    result = program_result(
        P0("instance", "attempt_count"),
        P0("instance", "success_count"),
        L(1),
        P0("episode", "development_evidence_window"),
    )
    return {
        "name": "mpd_clear_learning_effort_excess_after_causal_catchup",
        "area": "metacognitive_learning",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "holds_faculty", "program"],
            ["program", "ir_subgraph", "root"],
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            is_classifier(),
            Eq(P0("instance", "classifier_effort_excess"), L(1)),
            Eq(result, L(0)),
        ),
        "effects": [
            ["add_node", "assessment", "LearningPolicyClassifierAssessment", {
                "status": "recovered",
                "kind": "causal_yield_caught_up",
                "processed_units": T(P0("instance", "attempt_count")),
                "progress_units": T(P0("instance", "success_count")),
                "threshold_units": T(P0(
                    "episode", "development_evidence_window"
                )),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "step", "has_learning_classifier_assessment", "assessment"],
            ["add_edge", "assessment", "executed_classifier", "program"],
            ["set_attr", "instance", "classifier_effort_excess", 0],
        ],
    }


def frontier(incumbent: str = "incumbent") -> dict:
    return Filter(
        Neighbours(incumbent, "is_dominated_by_pareto_candidate"),
        "frontier_candidate",
        Eq(
            Count(Neighbours(
                "frontier_candidate", "is_dominated_by_pareto_candidate"
            )),
            L(0),
        ),
    )


def admissible_frontier() -> dict:
    return Filter(
        frontier(),
        "candidate",
        Eq(classifier_result(), L(0)),
    )


def initialise_request_rule() -> dict:
    return {
        "name": "mpd_begin_learned_classifier_boundary_sweep",
        "area": "metacognitive_learning",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "Zero is the multiplicative identity boundary, not a tuned "
        "constant. The graph moves it only while no route is admissible.",
        "match": [
            ["agent", "holds_faculty", "program"],
            ["program", "ir_subgraph", "root"],
            ["residual", "has_learning_policy_discrimination_request", "request"],
        ],
        "where": And(
            is_classifier(),
            Eq(A("request", "status"), L("requested")),
            Eq(P0("request", "classifier_sweep_started"), L(0)),
        ),
        "effects": [
            ["set_attr", "request", "classifier_threshold", 0],
            ["set_attr", "request", "classifier_sweep_count", 0],
            ["set_attr", "request", "classifier_sweep_started", 1],
            ["set_attr", "request", "status", "sweeping_classifier"],
            ["add_edge", "request", "uses_learned_classifier", "program"],
        ],
    }


def sweep_boundary_rule() -> dict:
    return {
        "name": "mpd_sweep_boundary_until_a_policy_first_crosses",
        "area": "metacognitive_learning",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "No fixed ratio and no host search: the held Program is "
        "re-executed after each graph-authored unit boundary change.",
        "match": [
            ["agent", "holds_faculty", "program"],
            ["program", "ir_subgraph", "root"],
            ["plan", "has_learning_policy_pareto_profile", "profile"],
            ["profile", "has_incumbent_pareto_candidate", "incumbent"],
            ["residual", "has_learning_policy_pareto_profile", "profile"],
            ["residual", "has_learning_policy_discrimination_request", "request"],
        ],
        "where": And(
            is_classifier(),
            Eq(A("request", "status"), L("sweeping_classifier")),
            Eq(Count(admissible_frontier()), L(0)),
        ),
        "effects": [
            ["set_attr", "request", "classifier_threshold", T(Plus(
                P0("request", "classifier_threshold"), L(1)
            ))],
            ["set_attr", "request", "classifier_sweep_count", T(Plus(
                P0("request", "classifier_sweep_count"), L(1)
            ))],
        ],
    }


def apply_unique_crossing_rule() -> dict:
    return {
        "name": "mpd_redirect_plan_at_unique_learned_classifier_crossing",
        "area": "metacognitive_learning",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "The single graph outcome controls the whole plan change; "
        "the program can inspect several dimensions, but only one candidate "
        "may cross first.",
        "match": [
            ["agent", "holds_faculty", "program"],
            ["program", "ir_subgraph", "root"],
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
            ["residual", "has_learning_policy_pareto_profile", "profile"],
            ["residual", "has_learning_policy_discrimination_request", "request"],
        ],
        "where": And(
            is_classifier(),
            Eq(A("request", "status"), L("sweeping_classifier")),
            Eq(classifier_result(), L(0)),
            Eq(Count(admissible_frontier()), L(1)),
        ),
        "effects": [
            ["add_node", "result", "LearningPolicyDiscriminationResult", {
                "status": "resolved",
                "kind": "unique_threshold_classifier_crossing",
                "threshold": T(P0("request", "classifier_threshold")),
                "sweep_count": T(P0("request", "classifier_sweep_count")),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_node", "revision", "LearningPlanRevision", {
                "kind": "redirect_to_classifier_admissible_frontier",
                "reason": "learned_classifier_unique_first_crossing",
                "status": "enacted",
                "order_n": T(P0("policy", "order_n")),
                "redirect_success_baseline": T(P0(
                    "next_instance", "success_count"
                )),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "request", "has_discrimination_result", "result"],
            ["add_edge", "result", "executed_classifier", "program"],
            ["add_edge", "result", "selected_policy_candidate", "candidate"],
            ["add_edge", "plan", "has_learning_plan_revision", "revision"],
            ["add_edge", "revision", "decided_by_discrimination_result", "result"],
            ["add_edge", "revision", "revises_learning_plan_step", "current_step"],
            ["add_edge", "revision", "redirects_to_learning_plan_step", "next_step"],
            ["add_edge", "revision", "resolves_learning_plan_residual", "residual"],
            ["add_edge", "current_instance", "reassess_after_learning_capability", "next_instance"],
            ["del_edge", "episode", "has_active_embodied_developmental_capability", "current_instance"],
            ["del_edge", "plan", "has_selected_learning_plan_step", "current_step"],
            ["set_attr", "current_step", "status", "meta_suspended"],
            ["set_attr", "current_instance", "status", "meta_suspended"],
            ["set_attr", "next_step", "status", "ready"],
            ["set_attr", "residual", "status", "resolved"],
            ["set_attr", "profile", "status", "classifier_revision_enacted"],
            ["set_attr", "request", "status", "resolved"],
            ["set_attr", "policy", "status", "active"],
            ["set_attr", "policy", "revision_count", T(Plus(
                P0("policy", "revision_count"), L(1)
            ))],
            ["set_attr", "plan", "replan_count", T(Plus(
                P0("plan", "replan_count"), L(1)
            ))],
        ],
    }


def retain_tied_crossing_rule() -> dict:
    return {
        "name": "mpd_retain_tied_classifier_crossing_as_underdetermined",
        "area": "metacognitive_learning",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["agent", "holds_faculty", "program"],
            ["program", "ir_subgraph", "root"],
            ["plan", "has_learning_policy_pareto_profile", "profile"],
            ["profile", "has_incumbent_pareto_candidate", "incumbent"],
            ["residual", "has_learning_policy_pareto_profile", "profile"],
            ["residual", "has_learning_policy_discrimination_request", "request"],
        ],
        "where": And(
            is_classifier(),
            Eq(A("request", "status"), L("sweeping_classifier")),
            Gt(Count(admissible_frontier()), L(1)),
        ),
        "effects": [
            ["add_node", "result", "LearningPolicyDiscriminationResult", {
                "status": "underdetermined",
                "kind": "tied_threshold_classifier_crossing",
                "threshold": T(P0("request", "classifier_threshold")),
                "candidate_count": T(Count(admissible_frontier())),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "request", "has_discrimination_result", "result"],
            ["add_edge", "result", "executed_classifier", "program"],
            ["set_attr", "request", "status", "needs_more_evidence"],
            ["set_attr", "policy", "status", "awaiting_discrimination"],
        ],
    }


def manifest() -> dict:
    productions = (
        ("holds_classifier", "Agent", "holds_faculty", "Program"),
        ("program_root", "Program", "ir_subgraph", "Node"),
        ("request_classifier", "LearningPolicyDiscriminationRequest", "uses_learned_classifier", "Program"),
        ("request_result", "LearningPolicyDiscriminationRequest", "has_discrimination_result", "LearningPolicyDiscriminationResult"),
        ("result_classifier", "LearningPolicyDiscriminationResult", "executed_classifier", "Program"),
        ("result_candidate", "LearningPolicyDiscriminationResult", "selected_policy_candidate", "ParetoCandidate"),
        ("revision_result", "LearningPlanRevision", "decided_by_discrimination_result", "LearningPolicyDiscriminationResult"),
        ("step_assessment", "LearningPlanStep", "has_learning_classifier_assessment", "LearningPolicyClassifierAssessment"),
        ("assessment_classifier", "LearningPolicyClassifierAssessment", "executed_classifier", "Program"),
    )
    return {
        "id": "metacognitive_program_discrimination",
        "version": "2.0.0",
        "depends_on": ["metacognitive_learning", "faculty_autogenesis"],
        "area": "metacognitive_learning",
        "latency_class": "soft_realtime",
        "description": "Executes a held integer classifier over unresolved "
        "Pareto learning-policy tails. The graph sweeps its own boundary, "
        "selects only a unique first crossing, and preserves ties.",
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": f"metacognitive_program_discrimination:{name}",
                "src": {"type": src, "var": "src"},
                "edge_type": edge,
                "tgt": {"type": tgt, "var": "tgt"},
            }
            for name, src, edge, tgt in productions
        ],
        "rules": [
            request_missing_classifier_faculty_rule(),
            classify_active_learning_excess_rule(),
            clear_active_learning_excess_rule(),
            initialise_request_rule(),
            sweep_boundary_rule(),
            apply_unique_crossing_rule(),
            retain_tied_crossing_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "metacognitive_program_discrimination.json"
    payload = manifest()
    output.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
