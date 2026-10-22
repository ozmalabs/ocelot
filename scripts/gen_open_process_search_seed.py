#!/usr/bin/env python3
"""Generate bounded source-driven open expression search rules (P19)."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import (  # noqa: E402
    A, And, Count, Eq, Exists, Gt, IfThenElse, L, Lt, N, Not, OFFLINE_AREA,
    ONLINE_AREA, PApply, PCompose, PFingerprint, PInverse, PPower, Plus, T, Times,
    StringConcat, Vec, is_none, not_none, policy_on, productions, rule,
)

SEED_ID = "open_process_search"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def _tree(name):
    return IfThenElse(is_none(A(name, "expr_tree")), A(name, "name"), A(name, "expr_tree"))


def _expression_rule(operator, order):
    if operator == "compose":
        params = PCompose(A("a", "params"), A("b", "params"))
        inner = Vec(L("compose"), _tree("a"), _tree("b"))
        subgoal = PApply(A("a", "params"), A("task", "initial_state"))
        tree = Vec(L("guard"), A("task", "initial_state"),
                   Vec(L("subgoal"), subgoal, inner))
        parents = [["d", "has_held_process", "a"], ["d", "has_held_process", "b"]]
        # Composition is non-commutative. Use source-content identity for the
        # first bounded frontier; human-readable labels never choose a recipe.
        pair_guard = Lt(A("a", "source_digest"), A("b", "source_digest"))
        expr_key = {"type": "StringConcat", "parts": [
            L("compose:"), A("a", "name"), L(":"), A("b", "name")]}
        work = Plus(A("a", "cost"), A("b", "cost"))
        parent_effects = [["add_edge", "attempt", "uses_parent_process", "a", {}],
                          ["add_edge", "attempt", "uses_parent_process", "b", {}]]
    else:
        parents = [["d", "has_held_process", "a"]]
        pair_guard = L(True)
        expr_key = {"type": "StringConcat", "parts": [L(operator + ":"), A("a", "name")]}
        if operator == "inverse":
            params = PInverse(A("a", "params"))
            inner = Vec(L("inverse"), _tree("a"))
            work = A("a", "cost")
        else:
            power = 2 if operator == "power2" else 3
            params = PPower(A("a", "params"), power)
            inner = Vec(L("power"), L(power), _tree("a"))
            work = Times(L(float(power)), A("a", "cost"))
        subgoal = L(None)
        tree = Vec(L("guard"), A("task", "initial_state"), inner)
        parent_effects = [["add_edge", "attempt", "uses_parent_process", "a", {}]]
    applied = PApply(params, A("task", "initial_state"))
    attempt_match = [["agent", "has_open_process_search_policy", "pol"],
        ["agent", "has_open_process_search_request", "request"],
        ["request", "searches_task", "task"], ["task", "about_domain", "d"]] + parents
    attempt = rule(
        f"ops_record_{operator}_attempt", ONLINE_AREA, 20 + order,
        "Count every bounded grammar expression attempt, including unsupported effects; recipe selection never reads a candidate name.",
        attempt_match,
        And(policy_on(), Eq(A("request", "status"), L("funded")),
            Eq(A("task", "status"), L("stuck")), pair_guard,
            Lt(Count(N("agent", "has_open_process_search_attempt")), A("pol", "max_attempts")),
            Not(Exists(N("request", "has_search_attempt"), "old",
                       Eq(A("old", "expression_key"), expr_key)))),
        [["add_node", "attempt", "OpenProcessSearchAttempt", {
            "expression_key": T(expr_key), "operator_kind": operator,
            "expression_tree": T(tree), "params": T(params),
            "predicted_state": T(applied), "goal_state": T(A("task", "goal")),
            "guard_state": T(A("task", "initial_state")), "subgoal_state": T(subgoal),
            "effect_digest": T(PFingerprint(params, A("d", "probes"))),
            "expression_digest": "pending_native_expression_attestation",
            "expression_digest_status": "pending",
            "domain": T(A("d", "name")), "kind": T(A("d", "kind")),
            "source_epoch": T(A("d", "source_epoch")),
            "model_epoch": T(A("d", "model_epoch")),
            "frame_epoch": T(A("d", "frame_epoch")),
            "work_cost": T(work), "status": T(IfThenElse(is_none(params), L("unknown"),
                IfThenElse(is_none(applied), L("unknown"),
                    IfThenElse(Eq(applied, A("task", "goal")), L("verified"), L("residual"))))) }],
         ["add_edge", "request", "has_search_attempt", "attempt", {}],
         ["add_edge", "agent", "has_open_process_search_attempt", "attempt", {}],
         ["add_edge", "attempt", "about_task", "task", {}]] + parent_effects,
        batch=False)
    mint = rule(
        f"ops_mint_verified_{operator}_candidate", ONLINE_AREA, 30 + order,
        "Retain an exact candidate only when its native effect reaches the observed goal; preserve expression, guard, subgoal and source witnesses.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_open_process_search_attempt", "attempt"],
         ["attempt", "about_task", "task"], ["task", "about_domain", "d"]],
        And(policy_on(), Eq(A("attempt", "operator_kind"), L(operator)),
            Eq(A("attempt", "status"), L("verified")),
            Eq(A("attempt", "domain"), A("d", "name")),
            Eq(A("attempt", "source_epoch"), A("d", "source_epoch")),
            Eq(A("attempt", "model_epoch"), A("d", "model_epoch")),
            Eq(A("attempt", "frame_epoch"), A("d", "frame_epoch")),
            Lt(Count(N("agent", "has_open_process_candidate")), A("pol", "max_candidates")),
            Not(Exists(N("agent", "has_open_process_candidate"), "old",
                       Eq(A("old", "expression_key"), A("attempt", "expression_key"))))),
        [["add_node", "candidate", "OpenProcessCandidate", {
            "expression_key": T(A("attempt", "expression_key")),
            "expression_digest": T(A("attempt", "expression_digest")),
            "expression_tree": T(A("attempt", "expression_tree")),
            "params": T(A("attempt", "params")),
            "effect_digest": T(A("attempt", "effect_digest")),
            "domain": T(A("attempt", "domain")), "kind": T(A("attempt", "kind")),
            "source_epoch": T(A("attempt", "source_epoch")),
            "model_epoch": T(A("attempt", "model_epoch")),
            "frame_epoch": T(A("attempt", "frame_epoch")),
            "precondition_kind": "native_apply_defined",
            "guard_state": T(A("attempt", "guard_state")),
            "subgoal_state": T(A("attempt", "subgoal_state")),
            "work_cost": T(A("attempt", "work_cost")),
            "verification": "native_process_apply_on_observed_source_state",
            "approval_required": 1.0, "status": "unapproved_candidate"}],
         ["add_edge", "agent", "has_open_process_candidate", "candidate", {}],
         ["add_edge", "candidate", "derived_from_attempt", "attempt", {}]],
        batch=False)
    return [attempt, mint]


def build():
    specs = [
        ("Agent", "has_open_process_search_policy", "OpenProcessSearchPolicy"),
        ("Agent", "has_open_process_search_request", "OpenProcessSearchRequest"),
        ("OpenProcessSearchRequest", "searches_task", "SolveTask"),
        ("OpenProcessSearchRequest", "has_search_attempt", "OpenProcessSearchAttempt"),
        ("Agent", "has_open_process_search_attempt", "OpenProcessSearchAttempt"),
        ("OpenProcessSearchAttempt", "about_task", "SolveTask"),
        ("OpenProcessSearchAttempt", "uses_parent_process", "ProcessSchema"),
        ("Agent", "has_open_process_candidate", "OpenProcessCandidate"),
        ("OpenProcessCandidate", "derived_from_attempt", "OpenProcessSearchAttempt"),
        ("ProcessDomain", "has_held_process", "ProcessSchema"),
        ("Agent", "has_thinking_budget", "ThinkingBudget"),
        ("Agent", "has_thinking_budget_request", "ThinkingBudgetRequest"),
        ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("OpenProcessSearchRequest", "has_budget_request", "ThinkingBudgetRequest"),
    ]
    request = rule("ops_request_bounded_search", ONLINE_AREA, 9,
        "Fund one bounded expression-search frontier from an observed stuck task.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_solve_task", "task"], ["task", "about_domain", "d"],
         ["agent", "has_thinking_budget", "budget"], ["agent", "has_network_mode_state", "mode"]],
        And(policy_on(), Eq(A("task", "status"), L("stuck")),
            Eq(A("budget", "enabled"), L(1.0)),
            Not(Exists(N("agent", "has_open_process_search_request"), "old",
                       Eq(A("old", "task_key"), A("task", "goal"))))),
        [["add_node", "request", "OpenProcessSearchRequest", {
            "task_key": T(A("task", "goal")), "domain": T(A("d", "name")),
            "source_epoch": T(A("d", "source_epoch")),
            "model_epoch": T(A("d", "model_epoch")),
            "frame_epoch": T(A("d", "frame_epoch")), "status": "awaiting_budget"}],
         ["add_edge", "agent", "has_open_process_search_request", "request", {}],
         ["add_edge", "request", "searches_task", "task", {}],
         ["add_node", "budget_request", "ThinkingBudgetRequest", {
            "requester_kind": "open_process_search", "status": "pending",
            "cost": T(A("pol", "search_cost")),
            "source_key": T(A("task", "goal")),
            "deadline_epoch": T(Plus(A("mode", "epoch"), L(1.0)))}],
         ["add_edge", "request", "has_budget_request", "budget_request", {}],
         ["add_edge", "agent", "has_thinking_budget_request", "budget_request", {}],
         ["add_edge", "budget_request", "draws_on_thinking_budget", "budget", {}]])
    funded = rule("ops_enable_only_funded_search", ONLINE_AREA, 10,
        "Open expression enumeration only after shared ThinkingBudget approval.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_open_process_search_request", "request"],
         ["request", "has_budget_request", "budget_request"]],
        And(policy_on(), Eq(A("request", "status"), L("awaiting_budget")),
            Eq(A("budget_request", "status"), L("approved"))),
        [["set_attr", "request", "status", "funded"]])
    rules = [request, funded]
    for index, operator in enumerate(("compose", "inverse", "power2", "power3")):
        rules.extend(_expression_rule(operator, index))
    return {"id": SEED_ID, "version": "1.0.0",
        "depends_on": ["process_solving", "thinking_budget"],
        "self_load_only": True, "area": OFFLINE_AREA,
        "description": "P19 bounded source-driven expression search. Candidate remains unapproved until existing adoption gates pass.",
        "microtheory": {"name": SEED_ID,
            "description": "Enumerate typed process expressions from residual task effects and held process evidence."},
        "nodes": [{"local_id": 0, "type": "OpenProcessSearchPolicy", "attrs": {
            "name": "open_process_search_policy", "enabled": 0.0,
            "max_attempts": 64.0, "max_candidates": 16.0,
            "search_cost": 2.0, "max_depth": 4.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_open_process_search_policy",
            "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, specs), "rules": rules}


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
