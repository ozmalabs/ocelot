"""Generate the graph-native bridge from program gaps to self-modification.

Program synthesis already files honest ``SelfConcern`` nodes.  This faculty
turns those residuals into self-directed learning plans and, once measurements
arrive at the body/interface boundary, into the existing proof-carrying
``SelfChange`` pipeline.  The host records evidence; graph rules decide every
transition.  All cognitive quantities are integers.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name):
    return {"type": "Var", "name": name}


def L(value):
    return {"type": "Lit", "value": value}


def A(var, key):
    return {"type": "Attr", "node": V(var), "key": key}


def P0(var, key):
    return {"type": "Plus", "items": [A(var, key), L(0)]}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def And(*items):
    return {"type": "And", "items": list(items)}


def Or(*items):
    return {"type": "Or", "items": list(items)}


def Count(source):
    return {"type": "Count", "source": source}


def Neighbours(var, edge_type):
    return {"type": "Neighbours", "node": V(var), "edge_type": edge_type}


def T(term):
    return {"__term__": term}


def production(name, src, edge, tgt):
    return {
        "provenance": f"program_self_modification:{name}",
        "src": {"type": src, "var": "src"},
        "edge_type": edge,
        "tgt": {"type": tgt, "var": "tgt"},
    }


def open_plan_rule():
    return {
        "name": "psm_open_self_directed_program_learning_plan",
        "area": "program_self_modification",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "An honest programming gap becomes an executable, "
        "metacognitively revisable learning plan without host promotion.",
        "match": [["agent", "has_self_concern", "concern"]],
        "where": And(
            Eq(A("concern", "status"), L("noted")),
            Or(Eq(A("concern", "kind"), L("code_write")),
               Eq(A("concern", "kind"), L("prog_read"))),
            Eq(Count(Neighbours("concern", "has_program_self_change_plan")), L(0)),
        ),
        "effects": [
            ["add_node", "episode", "SelfDirectedLearningEpisode", {
                "status": "active", "kind": "program_self_modification",
                "output_authority": 0, "integer_native": 1,
            }],
            ["add_node", "plan", "LearningPlan", {
                "status": "active", "goal": T(A("concern", "content")),
                "order_n": 1, "output_authority": 0, "integer_native": 1,
            }],
            ["add_node", "step", "LearningPlanStep", {
                "status": "ready", "goal": T(A("concern", "content")),
                "evidence_spent_units": 0, "evidence_budget_units": 1,
                "budget_success_baseline": 0, "context_evidence_units": 0,
                "output_authority": 0, "integer_native": 1,
            }],
            ["add_node", "capability", "ProgramCapabilityInstance", {
                "status": "learning", "kind": T(A("concern", "kind")),
                "success_count": 0, "failure_count": 0,
                "output_authority": 0, "integer_native": 1,
            }],
            ["add_node", "residual", "LearningPlanResidual", {
                "status": "open", "kind": "published_program_gap",
                "order_n": 1, "evidence_spent_units": 0,
                "causal_yield_units": 0, "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_node", "request", "SelfChangeProbeRequest", {
                "status": "requested", "kind": T(A("concern", "kind")),
                "measurement_count": 0, "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_node", "task_program", "SystemTwoTaskSet", {
                "area": "program_synthesis", "enabled": 1, "integer_native": 1,
            }],
            ["add_node", "task_change", "SystemTwoTaskSet", {
                "area": "self_change_reasoning", "enabled": 1, "integer_native": 1,
            }],
            ["add_node", "escalation", "SystemTwoEscalation", {
                "status": "requested", "reason": "program_capability_residual",
                "output_authority": 0, "integer_native": 1,
            }],
            ["add_edge", "agent", "has_self_directed_learning_episode", "episode"],
            ["add_edge", "episode", "has_self_directed_learning_plan", "plan"],
            ["add_edge", "plan", "has_learning_plan_step", "step"],
            ["add_edge", "plan", "has_selected_learning_plan_step", "step"],
            ["add_edge", "step", "plans_learning_capability", "capability"],
            ["add_edge", "plan", "has_learning_plan_residual", "residual"],
            ["add_edge", "step", "has_learning_plan_residual", "residual"],
            ["add_edge", "residual", "about_learning_plan_step", "step"],
            ["add_edge", "concern", "has_program_self_change_plan", "plan"],
            ["add_edge", "concern", "requests_program_self_change_probe", "request"],
            ["add_edge", "request", "addresses_learning_plan_residual", "residual"],
            ["add_edge", "escalation", "about_context", "residual"],
            ["add_edge", "escalation", "recruits_task_set", "task_program"],
            ["add_edge", "escalation", "recruits_task_set", "task_change"],
            ["set_attr", "concern", "self_change_status", "investigating"],
        ],
    }


def materialize_probe_rule():
    copied = (
        "case_id", "target_uid", "expected_revision", "baseline_hash",
        "live_clause", "false_negative", "false_positive",
        "threshold_sensitivity", "context_sensitivity",
        "relation_counterfactual", "outcome_mismatch", "effect_counterfactual",
        "cost_excess", "repeated_noop_firings",
        "threshold_adjustment_clause", "guard_strengthening_clause",
        "relation_addition_clause", "effect_substitution_clause",
        "firing_budget_guard_clause",
    )
    attrs = {key: T(A("measurement", key)) for key in copied}
    attrs.update({"change_opened": 0, "integer_native": 1})
    return {
        "name": "psm_materialize_measured_program_fault_probe",
        "area": "program_self_modification",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "The interface may report measurements, but this rule alone "
        "admits them to the proof-carrying self-change faculty.",
        "match": [
            ["agent", "has_self_concern", "concern"],
            ["concern", "requests_program_self_change_probe", "request"],
            ["request", "has_program_gap_measurement", "measurement"],
        ],
        "where": And(
            Eq(A("request", "status"), L("requested")),
            Eq(A("measurement", "status"), L("observed")),
            Eq(P0("measurement", "materialized"), L(0)),
        ),
        "effects": [
            ["add_node", "probe", "FaultProbe", attrs],
            ["add_edge", "request", "materialized_as_fault_probe", "probe"],
            ["add_edge", "agent", "observes_fault_probe", "probe"],
            ["set_attr", "measurement", "materialized", 1],
            ["set_attr", "request", "status", "measuring"],
            ["set_attr", "request", "measurement_count", T({
                "type": "Plus", "items": [P0("request", "measurement_count"), L(1)]
            })],
        ],
    }


def bind_diagnosis_rule():
    return {
        "name": "psm_bind_self_change_diagnosis_to_learning_plan",
        "area": "program_self_modification",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["concern", "requests_program_self_change_probe", "request"],
            ["request", "materialized_as_fault_probe", "probe"],
            ["change", "observed_as", "gap"],
            ["gap", "from_probe", "probe"],
            ["concern", "has_program_self_change_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
        ],
        "where": Eq(Count(Neighbours("plan", "has_program_self_change")), L(0)),
        "effects": [
            ["add_edge", "plan", "has_program_self_change", "change"],
            ["set_attr", "request", "status", "diagnosing"],
            ["set_attr", "step", "status", "active"],
        ],
    }


def revision_rule():
    return {
        "name": "psm_publish_proven_program_change_as_plan_revision",
        "area": "program_self_modification",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["plan", "has_program_self_change", "change"],
            ["change", "selected_patch", "patch"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["plan", "has_learning_plan_residual", "residual"],
        ],
        "where": And(
            Eq(A("residual", "status"), L("open")),
            Eq(Count(Neighbours("plan", "has_learning_plan_revision")), L(0)),
        ),
        "effects": [
            ["add_node", "revision", "LearningPlanRevision", {
                "status": "canarying", "kind": "proof_carrying_program_change",
                "order_n": 1, "output_authority": 0, "integer_native": 1,
            }],
            ["add_edge", "plan", "has_learning_plan_revision", "revision"],
            ["add_edge", "revision", "revises_learning_plan_step", "step"],
            ["add_edge", "revision", "resolves_learning_plan_residual", "residual"],
            ["add_edge", "revision", "proposes_rule_patch", "patch"],
            ["set_attr", "residual", "status", "under_repair"],
            ["set_attr", "plan", "status", "revising"],
        ],
    }


def consolidate_rule():
    return {
        "name": "psm_consolidate_successful_program_self_change",
        "area": "program_self_modification",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["concern", "has_program_self_change_plan", "plan"],
            ["plan", "has_program_self_change", "change"],
            ["change", "has_consolidation", "consolidation"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "capability"],
            ["plan", "has_learning_plan_residual", "residual"],
        ],
        "where": Eq(A("residual", "status"), L("under_repair")),
        "effects": [
            ["set_attr", "residual", "status", "resolved"],
            ["set_attr", "step", "status", "complete"],
            ["set_attr", "plan", "status", "complete"],
            ["set_attr", "capability", "status", "learned"],
            ["set_attr", "capability", "success_count", T({
                "type": "Plus", "items": [P0("capability", "success_count"), L(1)]
            })],
            ["set_attr", "concern", "status", "resolved"],
            ["set_attr", "concern", "self_change_status", "consolidated"],
        ],
    }


def manifest():
    productions = (
        ("agent_episode", "Agent", "has_self_directed_learning_episode", "SelfDirectedLearningEpisode"),
        ("episode_plan", "SelfDirectedLearningEpisode", "has_self_directed_learning_plan", "LearningPlan"),
        ("plan_step", "LearningPlan", "has_learning_plan_step", "LearningPlanStep"),
        ("plan_selected_step", "LearningPlan", "has_selected_learning_plan_step", "LearningPlanStep"),
        ("step_capability", "LearningPlanStep", "plans_learning_capability", "ProgramCapabilityInstance"),
        ("plan_residual", "LearningPlan", "has_learning_plan_residual", "LearningPlanResidual"),
        ("step_residual", "LearningPlanStep", "has_learning_plan_residual", "LearningPlanResidual"),
        ("residual_step", "LearningPlanResidual", "about_learning_plan_step", "LearningPlanStep"),
        ("concern_plan", "SelfConcern", "has_program_self_change_plan", "LearningPlan"),
        ("concern_request", "SelfConcern", "requests_program_self_change_probe", "SelfChangeProbeRequest"),
        ("request_residual", "SelfChangeProbeRequest", "addresses_learning_plan_residual", "LearningPlanResidual"),
        ("request_measurement", "SelfChangeProbeRequest", "has_program_gap_measurement", "ProgramGapMeasurement"),
        ("request_probe", "SelfChangeProbeRequest", "materialized_as_fault_probe", "FaultProbe"),
        ("plan_change", "LearningPlan", "has_program_self_change", "SelfChange"),
        ("revision_patch", "LearningPlanRevision", "proposes_rule_patch", "RulePatch"),
    )
    return {
        "id": "program_self_modification",
        "version": "1.0.0",
        "depends_on": [
            "program_synthesis", "metacognitive_learning",
            "self_change_reasoning", "cognitive_pareto", "dual_process_core",
        ],
        "area": "program_self_modification",
        "latency_class": "soft_realtime",
        "description": "Unifies programming gaps, order-N metacognitive learning "
        "plans, and proof-carrying self-change. Measurements enter at the "
        "interface; all diagnosis, planning, revision, and consolidation are "
        "graph-native and integer-only.",
        "nodes": [], "edges": [],
        "productions": [production(*row) for row in productions],
        "rules": [
            open_plan_rule(), materialize_probe_rule(), bind_diagnosis_rule(),
            revision_rule(), consolidate_rule(),
        ],
    }


def main():
    output = ROOT / "seeds" / "program_self_modification.json"
    output.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output} ({len(manifest()['rules'])} rules)")


if __name__ == "__main__":
    main()
