#!/usr/bin/env python3
"""Generate generic P22 proposal qualification from native training trials."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "independent_improvement.json"
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import A, And, Count, Eq, Exists, L, N, Not, T, policy_on, productions


def build():
    base = {"nodes": [], "edges": [], "productions": [], "rules": []}
    base.update({"id": "independent_improvement", "version": "1.0.0",
        "depends_on": ["open_process_search", "recursive_process_improvement"],
        "self_load_only": True, "area": "memory_consolidation",
        "description": "P22 generic proposals and qualification receipts from native training trials; no named successor operators."})
    local_id = 0
    base["nodes"].append({"local_id": local_id, "type": "IndependentImprovementPolicy", "attrs": {
        "name": "independent_improvement_policy", "enabled": 0.0,
        "minimum_native_trials": 2.0, "max_proposals": 128.0,
        "required_split": "training", "criteria_digest": "p22-independent-improvement-v1"}})
    base["edges"].append({"src": {"role": "agent_root"},
        "type": "has_independent_improvement_policy", "tgt": {"local": local_id}, "attrs": {}})
    local_id += 1
    base["nodes"].append({"local_id": local_id,
        "type": "IndependentImprovementCurriculumBridgePolicy", "attrs": {
            "name": "p22_curriculum_search_bridge", "enabled": 0.0,
            "required_split": "training"}})
    base["edges"].append({"src": {"role": "agent_root"},
        "type": "has_independent_improvement_curriculum_bridge_policy",
        "tgt": {"local": local_id}, "attrs": {}})
    rels = [
        ("Agent", "has_independent_improvement_policy", "IndependentImprovementPolicy"),
        ("Agent", "has_independent_improvement_curriculum_bridge_policy",
         "IndependentImprovementCurriculumBridgePolicy"),
        ("Agent", "has_independent_improvement_proposal", "IndependentImprovementProposal"),
        ("Agent", "has_independent_improvement_qualification", "IndependentImprovementQualification"),
        ("Agent", "has_open_process_search_request", "OpenProcessSearchRequest"),
        ("OpenProcessSearchRequest", "has_search_attempt", "OpenProcessSearchAttempt"),
        ("OpenProcessSearchRequest", "searches_task", "SolveTask"),
        ("IndependentImprovementProposal", "proposes_native_candidate", "OpenProcessCandidate"),
        ("IndependentImprovementProposal", "derived_from_trial", "OpenProcessSearchAttempt"),
        ("IndependentImprovementProposal", "has_native_qualification", "IndependentImprovementQualification"),
        ("IndependentImprovementQualification", "qualifies_proposal", "IndependentImprovementProposal"),
        ("IndependentImprovementQualification", "counts_native_trial", "OpenProcessSearchAttempt"),
    ]
    base["productions"] += [{"provenance": f"seed:p22:{edge}:{src}:{dst}",
        "src": {"type": src, "var": "src"}, "edge_type": edge,
        "tgt": {"type": dst, "var": "tgt"}} for src, edge, dst in rels]
    policy = ["agent", "has_independent_improvement_policy", "policy"]
    # The native P21 curriculum selector can dispatch an answer-free selected
    # task into the same graph's P19 learner. The world adapter supplies the
    # training task pool as ProcessCurriculumEvidence; native rules select and
    # release one task, and this rule constructs only its graph-side SolveTask.
    bridge = ["agent", "has_independent_improvement_curriculum_bridge_policy", "bridge"]
    base["rules"].append({"name": "iicb_release_selected_training_task_to_search",
        "area": "memory_consolidation", "order": 10,
        "latency_class": "background", "batch": False,
        "comment": "Release only the native-selected training curriculum task to the same graph's open-process learner.",
        "match": [bridge,
            ["agent", "has_process_curriculum_policy", "curriculum_policy"],
            ["agent", "has_process_curriculum_task", "curriculum_task"],
            ["curriculum_task", "from_evidence", "evidence"],
            ["agent", "has_process_domain", "domain"]],
        "where": And(policy_on("bridge"), policy_on("curriculum_policy"),
            Eq(A("bridge", "required_split"), L("training")),
            Eq(A("curriculum_task", "split"), A("bridge", "required_split")),
            Eq(A("curriculum_task", "status"), L("awaiting_experience")),
            Eq(A("evidence", "status"), L("scheduled")),
            Eq(A("domain", "name"), A("curriculum_task", "domain")),
            Not(Exists(N("agent", "has_solve_task"), "prior_task",
                Eq(A("prior_task", "task_key"), A("curriculum_task", "task_key"))))),
        "effects": [
            ["add_node", "solve_task", "SolveTask", {
                "task_key": T(A("curriculum_task", "task_key")),
                "training_trial_key": T(A("curriculum_task", "task_key")),
                "domain": T(A("curriculum_task", "domain")),
                "initial_state": T(A("curriculum_task", "initial_state")),
                "state": T(A("curriculum_task", "initial_state")),
                "object_count": T(A("domain", "object_count")),
                "goal": T(A("curriculum_task", "goal")),
                "status": "stuck", "trace": [], "steps": 0,
                "moves": 0.0, "stuck_count": 1, "split": "training"}],
            ["add_edge", "agent", "has_solve_task", "solve_task", {}],
            ["add_edge", "solve_task", "about_domain", "domain", {}],
            ["set_attr", "curriculum_task", "status", "delivered_to_native_search"]]})
    # A proposal is a reference to a generic P19 expression, never a named recipe.
    base["rules"].append({"name": "iip_propose_native_training_candidate",
        "area": "memory_consolidation", "order": 12,
        "latency_class": "background", "batch": False,
        "comment": "Track a generic native-search expression only when its source task is explicitly training data.",
        "match": [policy, ["agent", "has_open_process_candidate", "candidate"],
                  ["candidate", "derived_from_attempt", "attempt"],
                  ["agent", "has_open_process_search_request", "source_request"],
                  ["source_request", "has_search_attempt", "attempt"],
                  ["attempt", "about_task", "task"]],
        "where": And(policy_on("policy"),
            {"type": "Lt", "a": Count(N("agent", "has_independent_improvement_proposal")),
             "b": A("policy", "max_proposals")},
            Eq(A("task", "split"), A("policy", "required_split")),
            Eq(A("attempt", "status"), L("verified")),
            Eq(A("candidate", "status"), L("unapproved_candidate")),
            Eq(A("candidate", "expression_digest_status"), L("verified")),
            Not(Exists(N("agent", "has_independent_improvement_proposal"), "old",
                Eq(A("old", "expression_digest"), A("candidate", "expression_digest")))),
            # One shared budget is required; the proposal itself is not actionable.
            Exists(N("agent", "has_thinking_budget"), "budget",
                   Eq(A("budget", "enabled"), L(1.0)))),
        "effects": [["add_node", "proposal", "IndependentImprovementProposal", {
            "expression_digest": T(A("candidate", "expression_digest")),
            "expression_tree": T(A("candidate", "expression_tree")),
            "criteria_digest": T(A("policy", "criteria_digest")),
            "source_split": T(A("task", "split")),
            "status": "awaiting_native_qualification", "actionable": False,
            "qualified_trial_count": 0.0}],
            ["add_edge", "agent", "has_independent_improvement_proposal", "proposal", {}],
            ["add_edge", "proposal", "proposes_native_candidate", "candidate", {}],
            ["add_edge", "proposal", "derived_from_trial", "attempt", {}],
            ["set_attr", "source_request", "status", "proposal_recorded"]]})
    base["rules"].append({"name": "iip_qualify_after_independent_native_trials",
        "area": "memory_consolidation", "order": 14,
        "latency_class": "background", "batch": False,
        "comment": "Require a second distinct native-verified expression trial from the training split before a proposal may seek exact candidate approval.",
        "match": [policy,
            ["agent", "has_independent_improvement_proposal", "proposal"],
            ["proposal", "derived_from_trial", "source"],
            ["source", "about_task", "source_task"],
            ["agent", "has_open_process_search_request", "source_request"],
            ["source_request", "has_search_attempt", "source"],
            ["agent", "has_open_process_search_request", "trial_request"],
            ["trial_request", "has_search_attempt", "trial"],
            ["agent", "has_open_process_search_attempt", "trial"],
            ["trial", "about_task", "task"]],
        "where": And(policy_on("policy"),
            Eq(A("policy", "minimum_native_trials"), L(2.0)),
            Eq(A("source_task", "split"), A("policy", "required_split")),
            Eq(A("task", "split"), A("policy", "required_split")),
            Eq(A("trial", "status"), L("verified")),
            Eq(A("trial", "expression_tree"), A("proposal", "expression_tree")),
            {"type": "Not", "arg": Eq({"type": "Var", "name": "source_task"},
                                         {"type": "Var", "name": "task"})},
            Eq(A("proposal", "status"), L("awaiting_native_qualification"))),
        "effects": [["add_node", "qualification", "IndependentImprovementQualification", {
            "status": "qualified_for_candidate_specific_approval",
            "trial_count": 2.0, "split": T(A("policy", "required_split")),
            "expression_digest": T(A("proposal", "expression_digest")),
            "criteria_digest": T(A("proposal", "criteria_digest"))}],
            ["add_edge", "proposal", "has_native_qualification", "qualification", {}],
            ["add_edge", "qualification", "qualifies_proposal", "proposal", {}],
            ["add_edge", "qualification", "counts_native_trial", "source", {}],
            ["add_edge", "qualification", "counts_native_trial", "trial", {}],
            ["set_attr", "source_request", "status", "qualified_terminal"],
            ["set_attr", "trial_request", "status", "qualified_terminal"],
            ["set_attr", "proposal", "qualified_trial_count", 2.0],
            ["set_attr", "proposal", "status", "qualified_for_candidate_specific_approval"]]})
    return base


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
