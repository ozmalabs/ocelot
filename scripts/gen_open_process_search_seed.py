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
    A, And, Append, Argmin, Count, Eq, Exists, Filter, Gt, IfThenElse, In, L, Lt, N, Not, OFFLINE_AREA,
    ONLINE_AREA, PApply, PCompose, PFingerprint, PInverse, PPower, Plus, T, Times,
    StringConcat, V, Vec, Or, is_none, not_none, policy_on, productions, rule,
)

SEED_ID = "open_process_search"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def _tree(name):
    return IfThenElse(is_none(A(name, "expr_tree")), A(name, "name"), A(name, "expr_tree"))


def _task_identity():
    """Permit repeated same-goal training worlds only with explicit IDs."""
    return IfThenElse(is_none(A("task", "training_trial_key")),
                      A("task", "goal"), A("task", "training_trial_key"))


def _known_failed_subgoal(task, domain, subgoal):
    known = A(task, "known_failed_subgoals")
    return IfThenElse(is_none(known), L(False), In(subgoal, known))


def _unminted_attempts():
    return Filter(N("request", "has_search_attempt"), "eligible",
        Not(Exists(N("agent", "has_open_process_candidate"), "old",
            Eq(A("old", "expression_key"), A("eligible", "expression_key")))))


def _link_failure_evidence_rule():
    binding = And(Eq(A("failure", "initial_state"), A("task", "initial_state")),
        Eq(A("failure", "goal_state"), A("task", "goal")),
        Eq(A("failure", "object_count"), A("task", "object_count")),
        Eq(A("failure", "kind"), A("d", "kind")),
        Eq(A("failure", "source_epoch"), A("d", "source_epoch")),
        Eq(A("failure", "model_epoch"), A("d", "model_epoch")),
        Eq(A("failure", "frame_epoch"), A("d", "frame_epoch")),
        Eq(A("failure", "probe_epoch"), A("d", "probe_epoch")))
    return rule("ops_link_exact_strategy_failure_to_task", ONLINE_AREA, 8,
        "Attach matching failed-strategy evidence once per task before enumerating candidate expressions.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_solve_task", "task"], ["task", "about_domain", "d"],
         ["agent", "has_discovered_strategy", "strategy"],
         ["strategy", "has_strategy_failure_constraint", "failure"]],
        And(policy_on(), Eq(A("task", "status"), L("stuck")), binding,
            Not(Exists(N("task", "has_relevant_strategy_failure"), "old",
                        Eq(V("old"), V("failure"))))),
        [["add_edge", "task", "has_relevant_strategy_failure", "failure", {}],
         ["set_attr", "task", "known_failed_subgoals", T(IfThenElse(
             is_none(A("task", "known_failed_subgoals")),
             Vec(A("failure", "failed_state")),
             Append(A("task", "known_failed_subgoals"), A("failure", "failed_state"))))]],
        batch=False)


def _attempt_status(params, applied, task, domain, subgoal):
    return IfThenElse(_known_failed_subgoal(task, domain, subgoal), L("constraint_failed"),
        IfThenElse(is_none(params), L("unknown"),
            IfThenElse(is_none(applied), L("unknown"),
                IfThenElse(Eq(applied, A(task, "goal")), L("verified"), L("residual")))))


def _attempt_rank(params, applied, task, domain, subgoal, work):
    return IfThenElse(_known_failed_subgoal(task, domain, subgoal), Plus(L(3000000.0), work),
        IfThenElse(is_none(params), Plus(L(2000000.0), work),
            IfThenElse(is_none(applied), Plus(L(2000000.0), work),
                IfThenElse(Eq(applied, A(task, "goal")), work,
                    Plus(L(1000000.0), work)))))


def _expression_rule(operator, order, *, reverse=False):
    if operator == "compose":
        params = PCompose(A("a", "params"), A("b", "params"))
        inner = Vec(L("compose"), _tree("a"), _tree("b"))
        subgoal = PApply(A("a", "params"), A("task", "initial_state"))
        tree = Vec(L("guard"), A("task", "initial_state"),
                   Vec(L("subgoal"), subgoal, inner))
        parents = [["d", "has_held_process", "a"], ["d", "has_held_process", "b"]]
        # Composition is non-commutative. Use source-content identity for the
        # first bounded frontier; human-readable labels never choose a recipe.
        pair_guard = (Gt(A("a", "source_digest"), A("b", "source_digest"))
                      if reverse else Lt(A("a", "source_digest"), A("b", "source_digest")))
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
        f"ops_record_{operator}{'_reverse' if reverse else ''}_attempt", ONLINE_AREA, 20 + order,
        "Count every bounded grammar expression attempt, including unsupported effects; recipe selection never reads a candidate name.",
        attempt_match,
        And(policy_on(), Eq(A("request", "status"), L("funded")),
            Eq(A("task", "status"), L("stuck")), pair_guard,
            Lt(Count(N("agent", "has_open_process_search_attempt")), A("pol", "max_attempts")),
            Lt(Count(N("request", "has_search_attempt")), A("request", "max_attempts")),
            Not(Exists(N("request", "has_search_attempt"), "old",
                       Eq(A("old", "expression_key"), expr_key)))),
        [["add_node_with_counters", "attempt", "OpenProcessSearchAttempt", {
            "expression_key": T(expr_key), "operator_kind": operator,
            "expression_tree": T(tree), "params": T(params),
            "predicted_state": T(applied), "goal_state": T(A("task", "goal")),
            "guard_state": T(A("task", "initial_state")), "subgoal_state": T(subgoal),
            "depth": 1.0,
            "effect_digest": T(PFingerprint(params, A("d", "probes"))),
            "expression_digest": "pending_native_expression_attestation",
            "expression_digest_status": "pending",
            "domain": T(A("d", "name")), "kind": T(A("d", "kind")),
            "source_epoch": T(A("d", "source_epoch")),
            "model_epoch": T(A("d", "model_epoch")),
            "frame_epoch": T(A("d", "frame_epoch")),
            "work_cost": T(work),
            "status": T(_attempt_status(params, applied, "task", "d", subgoal)),
            "rank_score": T(_attempt_rank(params, applied, "task", "d", subgoal, work))},
          "pol", "attempts_reserved", T(A("pol", "max_attempts")),
          "request", "attempts_reserved", T(A("request", "max_attempts"))],
         ["add_edge", "request", "has_search_attempt", "attempt", {}],
         ["add_edge", "agent", "has_open_process_search_attempt", "attempt", {}],
         ["add_edge", "attempt", "about_task", "task", {}]] + parent_effects,
        batch=False)
    mint = rule(
        f"ops_mint_verified_{operator}_candidate", ONLINE_AREA, 30 + order,
        "Retain an exact candidate only when its native effect reaches the observed goal; preserve expression, guard, subgoal and source witnesses.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_open_process_search_attempt", "attempt"],
         ["agent", "has_open_process_search_request", "request"],
         ["request", "has_search_attempt", "attempt"],
         ["attempt", "about_task", "task"], ["task", "about_domain", "d"]],
        And(policy_on(), Eq(A("attempt", "operator_kind"), L(operator)),
            Eq(A("attempt", "status"), L("verified")),
            Eq(A("attempt", "domain"), A("d", "name")),
            Eq(A("attempt", "source_epoch"), A("d", "source_epoch")),
            Eq(A("attempt", "model_epoch"), A("d", "model_epoch")),
            Eq(A("attempt", "frame_epoch"), A("d", "frame_epoch")),
            Eq(V("attempt"), Argmin(_unminted_attempts(),
                                    "best", A("best", "rank_score"))),
            Lt(Count(N("agent", "has_open_process_candidate")), A("pol", "max_candidates")),
            Not(Exists(N("request", "has_candidate"), "old", L(True)))),
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
         ["add_edge", "request", "has_candidate", "candidate", {}],
         ["add_edge", "candidate", "derived_from_attempt", "attempt", {}]],
        batch=False)
    return [attempt] if reverse else [attempt, mint]


def _recursive_compose_rule(*, reverse=False):
    """Expand a residual expression with one held operand.

    The previous expression remains graph-authored data. Each expansion is a
    new, budgeted attempt; it is never reconstructed by the host or selected
    from a candidate label.
    """
    if reverse:
        params = PCompose(A("a", "params"), A("prior", "params"))
        inner = Vec(L("compose"), _tree("a"), _tree("prior"))
        key = {"type": "StringConcat", "parts": [L("compose["),
            A("a", "name"), L("|"), A("prior", "expression_key"), L("]")]}
        prior_state = PApply(A("prior", "params"), A("task", "initial_state"))
        work = Plus(A("a", "cost"), A("prior", "work_cost"))
        orientation = "held_then_expression"
    else:
        params = PCompose(A("prior", "params"), A("a", "params"))
        inner = Vec(L("compose"), _tree("prior"), _tree("a"))
        key = {"type": "StringConcat", "parts": [L("compose["),
            A("prior", "expression_key"), L("|"), A("a", "name"), L("]")]}
        prior_state = PApply(A("prior", "params"), A("task", "initial_state"))
        work = Plus(A("prior", "work_cost"), A("a", "cost"))
        orientation = "expression_then_held"
    applied = PApply(params, A("task", "initial_state"))
    tree = Vec(L("guard"), A("task", "initial_state"),
               Vec(L("subgoal"), prior_state, inner))
    return rule(
        f"ops_record_recursive_compose_{orientation}_attempt", ONLINE_AREA, 24,
        "Expand a residual graph-authored expression by one held operand, charging every expansion to the same bounded search ledger.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_open_process_search_request", "request"],
         ["request", "searches_task", "task"], ["task", "about_domain", "d"],
         ["request", "has_search_attempt", "prior"],
         ["prior", "about_task", "task"], ["d", "has_held_process", "a"]],
        And(policy_on(), Eq(A("request", "status"), L("funded")),
            Eq(A("task", "status"), L("stuck")),
            Eq(A("prior", "status"), L("residual")),
            Lt(A("prior", "depth"), A("pol", "max_depth")),
            Lt(Count(N("agent", "has_open_process_search_attempt")),
               A("pol", "max_attempts")),
            Lt(Count(N("request", "has_search_attempt")), A("request", "max_attempts")),
            Not(Eq(V("prior"), V("a"))),
            Not(Exists(N("request", "has_search_attempt"), "old",
                       Eq(A("old", "expression_key"), key)))),
        [["add_node_with_counters", "attempt", "OpenProcessSearchAttempt", {
            "expression_key": T(key), "operator_kind": "compose",
            "expression_tree": T(tree), "params": T(params),
            "predicted_state": T(applied), "goal_state": T(A("task", "goal")),
            "guard_state": T(A("task", "initial_state")),
            "subgoal_state": T(prior_state),
            "depth": T(Plus(A("prior", "depth"), L(1.0))),
            "effect_digest": T(PFingerprint(params, A("d", "probes"))),
            "expression_digest": "pending_native_expression_attestation",
            "expression_digest_status": "pending", "domain": T(A("d", "name")),
            "kind": T(A("d", "kind")), "source_epoch": T(A("d", "source_epoch")),
            "model_epoch": T(A("d", "model_epoch")),
            "frame_epoch": T(A("d", "frame_epoch")), "work_cost": T(work),
            "status": T(_attempt_status(params, applied, "task", "d", prior_state)),
            "rank_score": T(_attempt_rank(params, applied, "task", "d", prior_state, work))},
          "pol", "attempts_reserved", T(A("pol", "max_attempts")),
          "request", "attempts_reserved", T(A("request", "max_attempts"))],
         ["add_edge", "request", "has_search_attempt", "attempt", {}],
         ["add_edge", "agent", "has_open_process_search_attempt", "attempt", {}],
         ["add_edge", "attempt", "about_task", "task", {}],
         ["add_edge", "attempt", "extends_search_attempt", "prior", {}],
         ["add_edge", "attempt", "uses_parent_process", "a", {}]], batch=False)


def _recursive_unary_rule(operator, power=None):
    if operator == "inverse":
        params = PInverse(A("prior", "params"))
        inner = Vec(L("inverse"), _tree("prior"))
        subgoal = L(None)
        work = A("prior", "work_cost")
        key_parts = [L("inverse["), A("prior", "expression_key"), L("]")]
    else:
        params = PPower(A("prior", "params"), power)
        inner = Vec(L("power"), L(float(power)), _tree("prior"))
        subgoal = PApply(A("prior", "params"), A("task", "initial_state"))
        work = Times(L(float(power)), A("prior", "work_cost"))
        key_parts = [L(f"power{power}["), A("prior", "expression_key"), L("]")]
    key = {"type": "StringConcat", "parts": key_parts}
    applied = PApply(params, A("task", "initial_state"))
    tree = Vec(L("guard"), A("task", "initial_state"),
               Vec(L("subgoal"), subgoal, inner))
    return rule(
        f"ops_record_recursive_{operator}_attempt", ONLINE_AREA, 25,
        "Apply a bounded unary grammar constructor to a residual graph-authored expression.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_open_process_search_request", "request"],
         ["request", "searches_task", "task"], ["task", "about_domain", "d"],
         ["request", "has_search_attempt", "prior"],
         ["prior", "about_task", "task"]],
        And(policy_on(), Eq(A("request", "status"), L("funded")),
            Eq(A("task", "status"), L("stuck")),
            Eq(A("prior", "status"), L("residual")),
            Lt(A("prior", "depth"), A("pol", "max_depth")),
            Lt(Count(N("agent", "has_open_process_search_attempt")),
               A("pol", "max_attempts")),
            Lt(Count(N("request", "has_search_attempt")), A("request", "max_attempts")),
            Not(Exists(N("request", "has_search_attempt"), "old",
                       Eq(A("old", "expression_key"), key)))),
        [["add_node_with_counters", "attempt", "OpenProcessSearchAttempt", {
            "expression_key": T(key), "operator_kind": "recursive_unary",
            "expression_tree": T(tree), "params": T(params),
            "predicted_state": T(applied), "goal_state": T(A("task", "goal")),
            "guard_state": T(A("task", "initial_state")), "subgoal_state": T(subgoal),
            "depth": T(Plus(A("prior", "depth"), L(1.0))),
            "effect_digest": T(PFingerprint(params, A("d", "probes"))),
            "expression_digest": "pending_native_expression_attestation",
            "expression_digest_status": "pending", "domain": T(A("d", "name")),
            "kind": T(A("d", "kind")), "source_epoch": T(A("d", "source_epoch")),
            "model_epoch": T(A("d", "model_epoch")),
            "frame_epoch": T(A("d", "frame_epoch")), "work_cost": T(work),
            "status": T(_attempt_status(params, applied, "task", "d", subgoal)),
            "rank_score": T(_attempt_rank(params, applied, "task", "d", subgoal, work))},
          "pol", "attempts_reserved", T(A("pol", "max_attempts")),
          "request", "attempts_reserved", T(A("request", "max_attempts"))],
         ["add_edge", "request", "has_search_attempt", "attempt", {}],
         ["add_edge", "agent", "has_open_process_search_attempt", "attempt", {}],
         ["add_edge", "attempt", "about_task", "task", {}],
         ["add_edge", "attempt", "extends_search_attempt", "prior", {}]], batch=False)


def _mint_recursive_unary_rule():
    return rule(
        "ops_mint_verified_recursive_unary_candidate", ONLINE_AREA, 30,
        "Retain only the lowest-work exact recursive unary expression for the funded task.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_open_process_search_attempt", "attempt"],
         ["agent", "has_open_process_search_request", "request"],
         ["request", "has_search_attempt", "attempt"],
         ["attempt", "about_task", "task"], ["task", "about_domain", "d"]],
        And(policy_on(), Eq(A("attempt", "operator_kind"), L("recursive_unary")),
            Eq(A("attempt", "status"), L("verified")),
            Eq(A("attempt", "domain"), A("d", "name")),
            Eq(A("attempt", "source_epoch"), A("d", "source_epoch")),
            Eq(A("attempt", "model_epoch"), A("d", "model_epoch")),
            Eq(A("attempt", "frame_epoch"), A("d", "frame_epoch")),
            Eq(V("attempt"), Argmin(_unminted_attempts(),
                                    "best", A("best", "rank_score"))),
            Lt(Count(N("agent", "has_open_process_candidate")),
               A("pol", "max_candidates")),
            Not(Exists(N("request", "has_candidate"), "old", L(True)))),
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
         ["add_edge", "request", "has_candidate", "candidate", {}],
         ["add_edge", "candidate", "derived_from_attempt", "attempt", {}]], batch=False)


def _mint_recursive_compose_rule():
    return rule(
        "ops_mint_verified_recursive_compose_candidate", ONLINE_AREA, 30,
        "Retain the lowest-work verified recursive composition for one funded request.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_open_process_search_attempt", "attempt"],
         ["agent", "has_open_process_search_request", "request"],
         ["request", "has_search_attempt", "attempt"],
         ["attempt", "about_task", "task"], ["task", "about_domain", "d"]],
        And(policy_on(), Eq(A("attempt", "operator_kind"), L("recursive_compose")),
            Eq(A("attempt", "status"), L("verified")),
            Eq(A("attempt", "domain"), A("d", "name")),
            Eq(A("attempt", "source_epoch"), A("d", "source_epoch")),
            Eq(A("attempt", "model_epoch"), A("d", "model_epoch")),
            Eq(A("attempt", "frame_epoch"), A("d", "frame_epoch")),
            Eq(V("attempt"), Argmin(_unminted_attempts(),
                                    "best", A("best", "rank_score"))),
            Lt(Count(N("agent", "has_open_process_candidate")),
               A("pol", "max_candidates")),
            Not(Exists(N("request", "has_candidate"), "old", L(True)))),
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
         ["add_edge", "request", "has_candidate", "candidate", {}],
         ["add_edge", "candidate", "derived_from_attempt", "attempt", {}]], batch=False)


def _mint_candidate_composition_rule():
    eligible = Filter(N("request", "has_search_attempt"), "candidate_trial",
        And(Eq(A("candidate_trial", "operator_kind"), L("recursive_compose")),
            Eq(A("candidate_trial", "status"), L("verified")),
            Exists(N("candidate_trial", "extends_candidate"), "parent", L(True)),
            Not(Exists(N("agent", "has_open_process_candidate"), "old",
                Eq(A("old", "expression_key"), A("candidate_trial", "expression_key"))))))
    return rule("ops_mint_verified_candidate_composition", ONLINE_AREA, 30,
        "Preserve a verified candidate-plus-held composition as a child candidate with immutable parent lineage.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_open_process_search_attempt", "attempt"],
         ["agent", "has_open_process_search_request", "request"],
         ["request", "has_search_attempt", "attempt"],
         ["attempt", "extends_candidate", "parent_candidate"],
         ["attempt", "about_task", "task"], ["task", "about_domain", "d"]],
        And(policy_on(), Eq(A("attempt", "operator_kind"), L("recursive_compose")),
            Eq(A("attempt", "status"), L("verified")),
            Eq(V("attempt"), Argmin(eligible, "best", A("best", "rank_score"))),
            Lt(Count(N("agent", "has_open_process_candidate")), A("pol", "max_candidates")),
            Not(Exists(N("request", "has_candidate"), "old", L(True)))),
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
         ["add_edge", "request", "has_candidate", "candidate", {}],
         ["add_edge", "candidate", "derived_from_attempt", "attempt", {}]], batch=False)


def _independent_candidate_compose_rule(*, reverse=False):
    direction = "held_then_candidate" if reverse else "candidate_then_held"
    params = (PCompose(A("a", "params"), A("candidate", "params")) if reverse
              else PCompose(A("candidate", "params"), A("a", "params")))
    applied = PApply(params, A("task", "initial_state"))
    subgoal = (PApply(A("a", "params"), A("task", "initial_state")) if reverse
               else PApply(A("candidate", "params"), A("task", "initial_state")))
    key = StringConcat(L("independent-compose:"), A("candidate", "expression_digest"),
        L(":"), A("a", "source_digest"), L(":"), L(direction))
    tree = Vec(L("guard"), A("task", "initial_state"),
        Vec(L("independent_compose"), A("candidate", "expression_tree"),
            A("a", "name"), L(direction)))
    return rule(f"ops_test_candidate_composition_{direction}", ONLINE_AREA, 15 + int(reverse),
        "Test a digest-attested training candidate as an algebraic operand on a distinct training goal before broad search expansion.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_open_process_candidate", "candidate"],
         ["candidate", "derived_from_attempt", "source"],
         ["source", "about_task", "source_task"],
         ["agent", "has_open_process_search_request", "source_request"],
         ["source_request", "has_search_attempt", "source"],
         ["candidate", "has_expression_digest_receipt", "digest_receipt"],
         ["agent", "has_open_process_search_request", "request"],
         ["request", "searches_task", "task"], ["task", "about_domain", "d"],
         ["d", "has_held_process", "a"]],
        And(policy_on(), Eq(A("source_task", "split"), L("training")),
            Eq(A("task", "split"), L("training")),
            Eq(A("source", "status"), L("verified")),
            Eq(A("candidate", "status"), L("unapproved_candidate")),
            Eq(A("candidate", "expression_digest_status"), L("verified")),
            Eq(A("digest_receipt", "status"), L("verified")),
            Eq(A("digest_receipt", "expression_digest"), A("candidate", "expression_digest")),
            Eq(A("digest_receipt", "effect_digest"), A("candidate", "effect_digest")),
            Or(Eq(A("source_request", "status"), L("funded")),
               Eq(A("source_request", "status"), L("proposal_recorded"))),
            Or(Eq(A("request", "status"), L("funded")),
               Eq(A("request", "status"), L("proposal_recorded"))),
            Eq(A("task", "status"), L("stuck")),
            Eq(A("candidate", "domain"), A("d", "name")),
            Eq(A("candidate", "kind"), A("d", "kind")),
            Eq(A("candidate", "source_epoch"), A("d", "source_epoch")),
            Eq(A("candidate", "model_epoch"), A("d", "model_epoch")),
            Eq(A("candidate", "frame_epoch"), A("d", "frame_epoch")),
            Not(Eq(A("source_task", "goal"), A("task", "goal"))),
            Lt(Count(N("agent", "has_open_process_search_attempt")), A("pol", "max_attempts")),
            Lt(Count(N("request", "has_search_attempt")), A("request", "max_attempts")),
            Not(Exists(N("request", "has_search_attempt"), "old",
                       Eq(A("old", "expression_key"), key)))),
        [["add_node_with_counters", "trial", "OpenProcessSearchAttempt", {
            "expression_key": T(key), "operator_kind": "recursive_compose",
            "expression_tree": T(tree), "params": T(params),
            "predicted_state": T(applied), "goal_state": T(A("task", "goal")),
            "guard_state": T(A("task", "initial_state")),
            "subgoal_state": T(subgoal), "depth": 1.0,
            "effect_digest": T(PFingerprint(params, A("d", "probes"))),
            "expression_digest": "pending_native_expression_attestation",
            "expression_digest_status": "pending", "domain": T(A("d", "name")),
            "kind": T(A("d", "kind")), "source_epoch": T(A("d", "source_epoch")),
            "model_epoch": T(A("d", "model_epoch")), "frame_epoch": T(A("d", "frame_epoch")),
            "work_cost": T(Plus(A("candidate", "work_cost"), A("a", "cost"))),
            "status": T(IfThenElse(Eq(applied, A("task", "goal")), L("verified"), L("residual"))),
            "rank_score": T(Times(L(-1.0), Plus(A("candidate", "work_cost"), A("a", "cost"))))},
         "pol", "attempts_reserved", T(A("pol", "max_attempts")),
         "request", "attempts_reserved", T(A("request", "max_attempts"))],
         ["add_edge", "request", "has_search_attempt", "trial", {}],
         ["add_edge", "agent", "has_open_process_search_attempt", "trial", {}],
         ["add_edge", "trial", "about_task", "task", {}],
         ["add_edge", "trial", "uses_parent_process", "a", {}],
         ["add_edge", "trial", "extends_candidate", "candidate", {}],
         ["add_edge", "candidate", "has_independent_trial_attempt", "trial", {}]],
        batch=False)


def build():
    specs = [
        ("Agent", "has_open_process_search_policy", "OpenProcessSearchPolicy"),
        ("Agent", "has_open_process_search_request", "OpenProcessSearchRequest"),
        ("OpenProcessSearchRequest", "searches_task", "SolveTask"),
        ("OpenProcessSearchRequest", "has_search_attempt", "OpenProcessSearchAttempt"),
        ("Agent", "has_open_process_search_attempt", "OpenProcessSearchAttempt"),
        ("OpenProcessSearchAttempt", "about_task", "SolveTask"),
        ("OpenProcessSearchAttempt", "uses_parent_process", "ProcessSchema"),
        ("OpenProcessSearchAttempt", "extends_search_attempt", "OpenProcessSearchAttempt"),
        ("OpenProcessSearchRequest", "has_candidate", "OpenProcessCandidate"),
        ("Agent", "has_discovered_strategy", "DiscoveredStrategy"),
        ("DiscoveredStrategy", "has_strategy_failure_constraint", "StrategyFailureConstraint"),
        ("SolveTask", "has_relevant_strategy_failure", "StrategyFailureConstraint"),
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
                       Eq(A("old", "task_key"), _task_identity())))),
        [["add_node", "request", "OpenProcessSearchRequest", {
            "task_key": T(_task_identity()), "domain": T(A("d", "name")),
            "max_attempts": T(A("pol", "max_attempts_per_request")),
            "attempts_reserved": 0.0,
            "source_epoch": T(A("d", "source_epoch")),
            "model_epoch": T(A("d", "model_epoch")),
            "frame_epoch": T(A("d", "frame_epoch")), "status": "awaiting_budget"}],
         ["add_edge", "agent", "has_open_process_search_request", "request", {}],
         ["add_edge", "request", "searches_task", "task", {}],
         ["add_node", "budget_request", "ThinkingBudgetRequest", {
            "requester_kind": "open_process_search", "status": "pending",
            "cost": T(A("pol", "search_cost")),
            "source_key": T(_task_identity()),
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
    rules = [_link_failure_evidence_rule(), request, funded]
    rules.extend((_independent_candidate_compose_rule(),
                  _independent_candidate_compose_rule(reverse=True),
                  _mint_candidate_composition_rule(), _mint_recursive_compose_rule()))
    rules.extend(_expression_rule("compose", 0))
    rules.extend(_expression_rule("compose", 1, reverse=True))
    for index, operator in enumerate(("inverse", "power2", "power3"), start=2):
        rules.extend(_expression_rule(operator, index))
    rules.extend((_recursive_compose_rule(), _recursive_compose_rule(reverse=True)))
    rules.extend((_recursive_unary_rule("inverse"), _recursive_unary_rule("power", 2),
                  _recursive_unary_rule("power", 3), _mint_recursive_unary_rule()))
    rules.append(rule("ops_close_funded_request_at_global_attempt_ceiling",
        ONLINE_AREA, 90,
        "Close a funded search request explicitly when the shared native attempt ceiling prevents further enumeration.",
        [["agent", "has_open_process_search_policy", "pol"],
         ["agent", "has_open_process_search_request", "request"]],
        And(policy_on(), Eq(A("request", "status"), L("funded")),
            Gt(A("pol", "max_attempts"), L(0.0)),
            Not(Lt(Count(N("agent", "has_open_process_search_attempt")),
                   A("pol", "max_attempts"))),
            Eq(A("request", "global_ceiling_recorded"), L(None))),
        [["set_attr", "request", "status", "global_attempt_ceiling"],
         ["set_attr", "request", "global_ceiling_recorded", True]],
        batch=False))
    return {"id": SEED_ID, "version": "1.0.0",
        "depends_on": ["process_solving", "thinking_budget"],
        "self_load_only": True, "area": OFFLINE_AREA,
        "description": "P19 bounded source-driven expression search. Candidate remains unapproved until existing adoption gates pass.",
        "microtheory": {"name": SEED_ID,
            "description": "Enumerate typed process expressions from residual task effects and held process evidence."},
        "nodes": [{"local_id": 0, "type": "OpenProcessSearchPolicy", "attrs": {
            "name": "open_process_search_policy", "enabled": 0.0,
            "max_attempts": 64.0, "max_attempts_per_request": 256.0,
            "attempts_reserved": 0.0,
            "max_candidates": 16.0,
            "search_cost": 2.0, "max_depth": 4.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_open_process_search_policy",
            "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, specs), "rules": rules}


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
