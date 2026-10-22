#!/usr/bin/env python3
"""Generate bounded graph-native recall from observed strategy outcomes."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import (  # noqa: E402
    A, And, Count, Div, Eq, Exists, Filter, Gt, IfThenElse, L, Lte, Lt,
    MapList, N, Not, ONLINE_AREA, Or, PApply, Plus, T, V, Vec,
    policy_on, productions, rule,
)

SEED_ID = "strategy_library"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def not_none(term):
    return Not(Eq(term, L(None)))


def compatible(entry="entry", task="t", domain="d"):
    return And(
        Eq(A(entry, "status"), L("active")),
        Eq(A(entry, "kind"), A(domain, "kind")),
        Eq(A(entry, "state_size"), Count(A(task, "initial_state"))),
        Eq(A(entry, "goal_size"), Count(A(task, "goal"))),
        Eq(A(entry, "source_epoch"), A(domain, "source_epoch")),
        Eq(A(entry, "model_epoch"), A(domain, "model_epoch")),
        Eq(A(entry, "frame_epoch"), A(domain, "frame_epoch")),
        Eq(A(entry, "probe_epoch"), A(domain, "probe_epoch")),
        Lte(Count(A(entry, "trace")), A("pol", "max_steps")),
    )


def _soft_choice(task="t", domain="d"):
    compatible_entries = Filter(N("agent", "has_strategy_library_entry"),
                                "candidate", compatible("candidate", task, domain))
    weights = {
        "type": "SoftWeights", "source": compatible_entries,
        "var_name": "candidate", "value": A("candidate", "observed_yield"),
        "temperature": A("pol", "temperature"),
    }
    best_pair = {"type": "Argmax", "source": weights, "var_name": "weighted",
                 "value": {"type": "Nth", "items": V("weighted"), "index": 1}}
    return {"type": "Nth", "items": best_pair, "index": 0}


def record_observed_success_rule():
    already = Exists(N("agent", "has_strategy_library_entry"), "entry",
                     Eq(A("entry", "source_task"), V("t")))
    return rule(
        "sl_record_observed_solved_strategy", ONLINE_AREA, 5,
        "Create a reusable strategy entry only from a genuinely solved graph task and its actual process trace; the initial yield prior is one observed success, never an expected outcome.",
        [["agent", "has_strategy_library_policy", "pol"],
         ["agent", "has_solve_task", "t"], ["t", "about_domain", "d"]],
        And(policy_on(), Eq(A("t", "status"), L("solved")),
            Not(Eq(A("t", "trace"), L([]))),
            Lt(Count(N("agent", "has_strategy_library_entry")), A("pol", "max_entries")),
            Not(already)),
        [["add_node", "entry", "StrategyLibraryEntry", {
            "status": "active", "kind": T(A("d", "kind")),
            "domain": T(A("d", "name")), "state_size": T(Count(A("t", "initial_state"))),
            "goal_size": T(Count(A("t", "goal"))),
            "initial_state": T(A("t", "initial_state")), "goal_state": T(A("t", "goal")),
            "trace": T(A("t", "trace")), "source_task": T(V("t")),
            "step_count": T(Count(A("t", "trace"))),
            "source_epoch": T(A("d", "source_epoch")),
            "model_epoch": T(A("d", "model_epoch")),
            "frame_epoch": T(A("d", "frame_epoch")),
            "probe_epoch": T(A("d", "probe_epoch")),
            "observed_attempts": 1, "observed_successes": 1,
            "observed_yield": 1.0, "yield_source": "observed_solved_task",
            "provenance": "observed_graph_process_trace",
        }],
         ["add_edge", "agent", "has_strategy_library_entry", "entry", {}],
         ["add_edge", "entry", "about_domain", "d", {}],
         ["add_edge", "entry", "source_task", "t", {}],
         ["set_attr", "t", "strategy_library_recorded", 1]],
    )


def request_recall_budget_rule():
    eligible = Exists(N("agent", "has_strategy_library_entry"), "candidate",
                      compatible("candidate"))
    already = Exists(N("t", "has_strategy_recall_request"), "old",
                     Eq(A("old", "requester_key"), V("t")))
    return rule(
        "sl_request_funded_strategy_recall", ONLINE_AREA, 5,
        "Request one shared ThinkingBudget debit before weighting or applying any compatible strategy; bind it to this task and its source/model epoch.",
        [["agent", "has_strategy_library_policy", "pol"],
         ["agent", "has_thinking_budget", "budget"],
         ["agent", "has_network_mode_state", "mode"],
         ["agent", "has_solve_task", "t"], ["t", "about_domain", "d"]],
        And(policy_on(), Eq(A("budget", "enabled"), L(1.0)),
            Eq(A("t", "status"), L("active")),
            Not(Eq(A("t", "strategy_funding_requested"), L(1))),
            eligible, Not(already)),
        [["add_node", "req", "ThinkingBudgetRequest", {
            "requester_kind": "strategy_library_recall",
            "requester_key": T(V("t")), "source_key": T(V("t")),
            "source_epoch": T(A("d", "source_epoch")),
            "model_epoch": T(A("d", "model_epoch")),
            "requested_epoch": T(A("mode", "epoch")),
            "deadline_epoch": T(Plus(A("mode", "epoch"), L(1))),
            "cost": T(A("pol", "recall_cost")), "status": "pending",
        }],
         ["add_edge", "agent", "has_thinking_budget_request", "req", {}],
         ["add_edge", "t", "has_strategy_recall_request", "req", {}],
         ["add_edge", "req", "draws_on_thinking_budget", "budget", {}],
         ["set_attr", "t", "strategy_funding_requested", 1]],
        batch=False,
    )


def start_recall_rule():
    choice = _soft_choice()
    return rule(
        "sl_start_soft_weighted_compatible_recall", ONLINE_AREA, 6,
        "Recall among structurally compatible strategies using native SoftWeights over observed yield, gated by context and all source/model/frame/probe epochs; leave cold-start tasks to the bounded solver.",
        [["agent", "has_strategy_library_policy", "pol"],
         ["agent", "has_network_mode_state", "mode"],
         ["agent", "has_solve_task", "t"], ["t", "about_domain", "d"],
         ["agent", "has_strategy_library_entry", "entry"],
         ["agent", "has_thinking_budget_request", "req"],
         ["t", "has_strategy_recall_request", "req"]],
        And(policy_on(), Eq(A("t", "status"), L("active")),
            Not(Eq(A("t", "strategy_recall_attempted"), L(1))),
            Eq(A("req", "requester_kind"), L("strategy_library_recall")),
            Eq(A("req", "status"), L("approved")),
            Eq(A("req", "requested_epoch"), A("mode", "epoch")),
            Eq(A("req", "source_epoch"), A("d", "source_epoch")),
            Eq(A("req", "model_epoch"), A("d", "model_epoch")),
            Eq(V("entry"), choice), compatible()),
        [["add_node", "attempt", "StrategyRecallAttempt", {
            "status": "running", "signature_kind": T(A("d", "kind")),
            "state_size": T(Count(A("t", "initial_state"))),
            "goal_size": T(Count(A("t", "goal"))),
            "observed_yield_at_selection": T(A("entry", "observed_yield")),
            "model_epoch": T(A("d", "model_epoch")),
            "candidate_count": T(Count(Filter(
                N("agent", "has_strategy_library_entry"), "c", compatible("c")))),
            "cold_start_process_count": T(Count(Filter(
                N("agent", "has_process_schema"), "p",
                And(Eq(A("p", "domain"), A("d", "name")),
                    Eq(A("p", "status"), L("active")))))),
            "source": "observed_yield_softweights",
        }],
         ["add_edge", "agent", "has_strategy_recall_attempt", "attempt", {}],
         ["add_edge", "t", "has_strategy_recall_attempt", "attempt", {}],
         ["add_edge", "t", "recalls_strategy_entry", "entry", {}],
         ["add_edge", "attempt", "uses_strategy_entry", "entry", {}],
         ["set_attr", "t", "strategy_recall_attempted", 1],
         ["set_attr", "t", "strategy_index", 0],
         ["set_attr", "t", "status", "strategy_replaying"]],
    )


def apply_recall_step_rule():
    result = PApply(A("p", "params"), A("t", "state"))
    idx = A("t", "strategy_index")
    trace = A("entry", "trace")
    updated_index = Plus(idx, L(1))
    return rule(
        "sl_apply_and_reverify_strategy_step", ONLINE_AREA, 7,
        "Apply one stored process through native ProcessApply, write an application receipt, and check progress against the current task; strategy recall never substitutes expected yield for verification.",
        [["agent", "has_strategy_library_policy", "pol"],
         ["agent", "has_solve_task", "t"], ["t", "about_domain", "d"],
         ["t", "recalls_strategy_entry", "entry"],
         ["agent", "has_process_schema", "p"]],
        And(policy_on(), Eq(A("t", "status"), L("strategy_replaying")),
            Lt(idx, Count(trace)), Eq(V("p"), {"type": "IndexAt", "seq": trace, "index": idx}),
            Eq(A("p", "status"), L("active")),
            Eq(A("entry", "model_epoch"), A("d", "model_epoch")),
            not_none(result), Not(Eq(result, A("t", "state")))),
        [["add_node", "receipt", "StrategyApplicationReceipt", {
            "status": "native_applied", "input_state": T(A("t", "state")),
            "output_state": T(result), "step_index": T(idx),
            "model_epoch": T(A("d", "model_epoch")),
            "verification": "native_process_apply_progress_checked",
        }],
         ["add_edge", "t", "has_strategy_application_receipt", "receipt", {}],
         ["add_edge", "receipt", "used_process", "p", {}],
         ["set_attr", "t", "strategy_next_state", T(result)],
         ["set_attr", "t", "state", T(A("t", "strategy_next_state"))],
         ["set_attr", "t", "trace", T({"type": "Append", "seq": A("t", "trace"), "item": V("p")})],
         ["set_attr", "t", "steps", T(Plus(A("t", "steps"), L(1)))],
         ["set_attr", "t", "strategy_index", T(updated_index)],
         ["set_attr", "t", "status", T(IfThenElse(
             Eq(A("t", "strategy_next_state"), A("t", "goal")), L("solved"),
             IfThenElse(Eq(A("t", "strategy_index"), Count(trace)), L("strategy_failed"), L("strategy_replaying"))))],
         ["set_attr", "t", "strategy_next_state", None]],
        batch=False,
    )


def observe_recall_outcome_rule(success: bool):
    outcome = "observed_success" if success else "observed_failure"
    status = "solved" if success else "strategy_failed"
    new_successes = Plus(A("entry", "observed_successes"), L(1 if success else 0))
    new_attempts = Plus(A("entry", "observed_attempts"), L(1))
    return rule(
        "sl_record_" + outcome, ONLINE_AREA, 8 if success else 9,
        "Update yield only from a terminal observed strategy-recall outcome.",
        [["agent", "has_strategy_library_policy", "pol"],
         ["agent", "has_solve_task", "t"],
         ["t", "recalls_strategy_entry", "entry"],
         ["t", "has_strategy_recall_attempt", "attempt"]],
        And(policy_on(), Eq(A("t", "status"), L(status)),
            Not(Eq(A("t", "strategy_yield_recorded"), L(1)))),
        [["add_node", "obs", "StrategyYieldObservation", {
            "result": outcome, "steps": T(A("t", "steps")),
            "model_epoch": T(A("attempt", "model_epoch")),
            "source": "observed_task_terminal_outcome",
        }],
         ["add_edge", "attempt", "has_yield_observation", "obs", {}],
         ["add_edge", "entry", "has_yield_observation", "obs", {}],
         ["set_attr", "entry", "observed_yield", T(Div(new_successes, new_attempts))],
         ["set_attr", "entry", "observed_attempts", T(new_attempts)],
         ["set_attr", "entry", "observed_successes", T(new_successes)],
         ["set_attr", "attempt", "status", outcome],
         ["set_attr", "t", "strategy_yield_recorded", 1]],
        batch=False,
    )


def fail_nonapplicable_step_rule():
    result = PApply(A("p", "params"), A("t", "state"))
    return rule(
        "sl_fail_nonapplicable_recall_step", ONLINE_AREA, 7,
        "Reject a recalled step when native application is unknown or makes no state change, so the bounded solver can resume instead of stalling.",
        [["agent", "has_strategy_library_policy", "pol"],
         ["agent", "has_solve_task", "t"], ["t", "about_domain", "d"],
         ["t", "recalls_strategy_entry", "entry"],
         ["agent", "has_process_schema", "p"]],
        And(policy_on(), Eq(A("t", "status"), L("strategy_replaying")),
            Lt(A("t", "strategy_index"), Count(A("entry", "trace"))),
            Eq(V("p"), {"type": "IndexAt", "seq": A("entry", "trace"),
                         "index": A("t", "strategy_index")}),
            Or(Eq(result, L(None)), Eq(result, A("t", "state")))),
        [["set_attr", "t", "status", "strategy_failed"],
         ["set_attr", "t", "strategy_failure_reason", "native_process_not_applicable_or_no_progress"]],
    )


def fallback_after_bad_recall_rule():
    return rule(
        "sl_fallback_to_bounded_solver_after_bad_recall", ONLINE_AREA, 10,
        "A failed or inapplicable recalled sequence is recorded as a rejected candidate, then yields the task to the existing bounded solver.",
        [["agent", "has_strategy_library_policy", "pol"],
         ["agent", "has_solver_policy", "solver_pol"],
         ["agent", "has_solve_task", "t"], ["t", "recalls_strategy_entry", "entry"]],
        And(policy_on(), Eq(A("t", "status"), L("strategy_failed")),
            Not(Eq(A("t", "strategy_fallback_started"), L(1)))),
        [["add_edge", "t", "rejected_strategy_recall", "entry", {}],
         ["set_attr", "t", "strategy_fallback_started", 1],
         ["set_attr", "t", "status", "active"],
         ["set_attr", "solver_pol", "enabled", 1.0]],
    )


def invalidate_changed_distribution_rule():
    return rule(
        "sl_invalidate_strategy_distribution_change", ONLINE_AREA, 4,
        "Retire a strategy yield record when its owning process distribution/model epoch changes.",
        [["agent", "has_strategy_library_policy", "pol"],
         ["agent", "has_strategy_library_entry", "entry"],
         ["entry", "about_domain", "d"]],
        And(policy_on(), Eq(A("entry", "status"), L("active")),
            Or(Not(Eq(A("entry", "source_epoch"), A("d", "source_epoch"))),
               Not(Eq(A("entry", "model_epoch"), A("d", "model_epoch"))),
               Not(Eq(A("entry", "frame_epoch"), A("d", "frame_epoch"))),
               Not(Eq(A("entry", "probe_epoch"), A("d", "probe_epoch"))))),
        [["set_attr", "entry", "status", "stale"],
         ["set_attr", "entry", "stale_reason", "distribution_epoch_changed"]],
    )


def fallback_without_compatible_entry_rule():
    eligible = Exists(N("agent", "has_strategy_library_entry"), "candidate",
                      compatible("candidate"))
    return rule(
        "sl_record_cold_start_fallback", ONLINE_AREA, 11,
        "When no current structurally compatible observed strategy exists, preserve cold start and let the bounded existing solver proceed.",
        [["agent", "has_strategy_library_policy", "pol"],
         ["agent", "has_solver_policy", "solver_pol"],
         ["agent", "has_solve_task", "t"], ["t", "about_domain", "d"]],
        And(policy_on(), Eq(A("t", "status"), L("active")),
            Not(Eq(A("t", "strategy_fallback_recorded"), L(1))), Not(eligible)),
        [["add_node", "fallback", "StrategyRecallFallback", {
            "status": "cold_start", "reason": "no_compatible_observed_strategy",
            "model_epoch": T(A("d", "model_epoch")),
            "candidate_work": T(Count(Filter(
                N("agent", "has_process_schema"), "p",
                And(Eq(A("p", "domain"), A("d", "name")),
                    Eq(A("p", "status"), L("active")))))),
        }],
         ["add_edge", "agent", "has_strategy_recall_fallback", "fallback", {}],
         ["add_edge", "t", "has_strategy_recall_fallback", "fallback", {}],
         ["set_attr", "t", "strategy_fallback_recorded", 1],
         ["set_attr", "solver_pol", "enabled", 1.0]],
    )


def fallback_after_denied_funding_rule():
    return rule(
        "sl_fallback_after_recall_funding_denial", ONLINE_AREA, 12,
        "If the shared budget denies or expires the recall request, record the denial and continue through the bounded solver without retrying or bypassing the budget.",
        [["agent", "has_strategy_library_policy", "pol"],
         ["agent", "has_solver_policy", "solver_pol"],
         ["agent", "has_solve_task", "t"],
         ["t", "has_strategy_recall_request", "req"]],
        And(policy_on(), Eq(A("t", "status"), L("active")),
            Or(Eq(A("req", "status"), L("denied")),
               Eq(A("req", "status"), L("canceled"))),
            Not(Eq(A("t", "strategy_funding_fallback"), L(1)))),
        [["set_attr", "t", "strategy_funding_fallback", 1],
         ["set_attr", "t", "status", "active"],
         ["set_attr", "solver_pol", "enabled", 1.0]],
    )


def fallback_when_budget_disabled_rule():
    eligible = Exists(N("agent", "has_strategy_library_entry"), "candidate",
                      compatible("candidate"))
    return rule(
        "sl_fallback_when_shared_budget_disabled", ONLINE_AREA, 12,
        "Do not perform strategy weighting without an enabled shared budget; record the reason and yield to the bounded solver.",
        [["agent", "has_strategy_library_policy", "pol"],
         ["agent", "has_thinking_budget", "budget"],
         ["agent", "has_solver_policy", "solver_pol"],
         ["agent", "has_solve_task", "t"], ["t", "about_domain", "d"]],
        And(policy_on(), Eq(A("budget", "enabled"), L(0.0)),
            Eq(A("t", "status"), L("active")), eligible,
            Not(Eq(A("t", "strategy_fallback_recorded"), L(1)))),
        [["add_node", "fallback", "StrategyRecallFallback", {
            "status": "cold_start", "reason": "shared_budget_disabled",
            "model_epoch": T(A("d", "model_epoch")), "candidate_work": 0,
        }],
         ["add_edge", "agent", "has_strategy_recall_fallback", "fallback", {}],
         ["add_edge", "t", "has_strategy_recall_fallback", "fallback", {}],
         ["set_attr", "t", "strategy_fallback_recorded", 1],
         ["set_attr", "solver_pol", "enabled", 1.0]],
    )


def build_seed():
    return {
        "id": SEED_ID, "version": "1.0.0",
        "depends_on": ["process_solving", "thinking_budget"], "self_load_only": True,
        "area": ONLINE_AREA,
        "description": "Recall structurally compatible graph strategies using observed yield and native per-step application receipts; stale contexts invalidate and failed candidates fall back to bounded search.",
        "microtheory": {"name": SEED_ID,
                        "description": "Retain observed strategy yields and recall compatible candidates without treating expected yield as proof."},
        "nodes": [{"local_id": 0, "type": "StrategyLibraryPolicy", "attrs": {
            "name": "core_strategy_library_policy", "enabled": 0.0,
            "max_entries": 128.0, "max_steps": 32.0, "temperature": 0.5,
            "recall_cost": 1.0,
        }}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_strategy_library_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, [
            ("Agent", "has_strategy_library_policy", "StrategyLibraryPolicy"),
            ("Agent", "has_thinking_budget", "ThinkingBudget"),
            ("Agent", "has_network_mode_state", "NetworkModeState"),
            ("Agent", "has_thinking_budget_request", "ThinkingBudgetRequest"),
            ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
            ("Agent", "has_strategy_library_entry", "StrategyLibraryEntry"),
            ("StrategyLibraryEntry", "about_domain", "ProcessDomain"),
            ("StrategyLibraryEntry", "source_task", "SolveTask"),
            ("Agent", "has_strategy_recall_attempt", "StrategyRecallAttempt"),
            ("SolveTask", "has_strategy_recall_attempt", "StrategyRecallAttempt"),
            ("SolveTask", "has_strategy_recall_request", "ThinkingBudgetRequest"),
            ("SolveTask", "recalls_strategy_entry", "StrategyLibraryEntry"),
            ("StrategyRecallAttempt", "uses_strategy_entry", "StrategyLibraryEntry"),
            ("SolveTask", "has_strategy_application_receipt", "StrategyApplicationReceipt"),
            ("StrategyApplicationReceipt", "used_process", "ProcessSchema"),
            ("StrategyRecallAttempt", "has_yield_observation", "StrategyYieldObservation"),
            ("StrategyLibraryEntry", "has_yield_observation", "StrategyYieldObservation"),
            ("SolveTask", "rejected_strategy_recall", "StrategyLibraryEntry"),
            ("Agent", "has_strategy_recall_fallback", "StrategyRecallFallback"),
            ("SolveTask", "has_strategy_recall_fallback", "StrategyRecallFallback"),
        ]),
        "rules": [
            invalidate_changed_distribution_rule(), record_observed_success_rule(),
            request_recall_budget_rule(),
            start_recall_rule(), apply_recall_step_rule(),
            fail_nonapplicable_step_rule(),
            observe_recall_outcome_rule(True), observe_recall_outcome_rule(False),
            fallback_after_bad_recall_rule(), fallback_without_compatible_entry_rule(),
            fallback_after_denied_funding_rule(), fallback_when_budget_disabled_rule(),
        ],
    }


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
