#!/usr/bin/env python3
"""Author the bounded, funded goal-regression and inverse probe seed (P10.03)."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import (  # noqa: E402
    A, And, Count, Eq, Exists, Filter, Gt, L, Lt, Lte, N, Not, OFFLINE_AREA,
    ONLINE_AREA, PApply, PFingerprint, PInverse, PSupport, Plus, T, Times,
    Vec, ZERO, hamming, is_none, not_none, policy_on, productions, rule,
)

SEED_ID = "goal_invention"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def has_gap():
    # The task edge is the identity; names are optional world metadata.
    return Exists(N("t", "has_process_gap"), "old", Eq(A("old", "status"), A("old", "status")))


def usable_inverse(h="h"):
    inv = PInverse(A(h, "params"))
    fp = PFingerprint(inv, A("d", "probes"))
    effect = PApply(inv, A("t", "state"))
    return And(Eq(A(h, "status"), L("active")), Eq(A(h, "kind"), A("d", "kind")),
               not_none(inv), not_none(fp), Lte(PSupport(inv), A("pol", "max_support")),
               Gt(hamming(A("t", "state"), A("t", "goal")), ZERO),
               Gt(hamming(A("t", "state"), A("t", "goal")),
                  hamming(effect, A("t", "goal"))),
               Not(Exists(NodesWhere("ProcessSchema", "fingerprint", fp), "old_schema",
                          Eq(A("old_schema", "domain"), A("d", "name")))))


def NodesWhere(ntype, key, value):
    return {"type": "NodesWhere", "node_type": ntype, "attr_key": key, "value": value}


def gap_rule():
    return rule("gi_mint_process_gap", ONLINE_AREA, 18,
        "Record a typed state-transition gap when a task is stuck and no gap for that task exists.",
        [["agent", "has_goal_invention_policy", "pol"], ["agent", "has_solve_task", "t"],
         ["t", "about_domain", "d"]],
        And(policy_on(), Eq(A("t", "status"), L("stuck")), Not(has_gap()),
            Lt(Count(N("agent", "has_process_gap")), A("pol", "max_gaps"))),
        [["add_node", "g", "ProcessGap", {
            "source_task": T(A("t", "name")), "domain": T(A("d", "name")),
            "domain_kind": T(A("d", "kind")), "source_state": T(A("t", "state")),
            "goal_state": T(A("t", "goal")), "required_effect_kind": "state_transition",
            "source_epoch": T(A("d", "source_epoch")), "model_epoch": T(A("d", "model_epoch")),
            "frame_epoch": T(A("d", "frame_epoch")), "status": "open",
            "frontier_depth": 0, "expansions": 0}],
         ["add_edge", "agent", "has_process_gap", "g", {}],
         ["add_edge", "t", "has_process_gap", "g", {}],
         ["add_edge", "g", "about_domain", "d", {}]])


def request_rule():
    return rule("gi_request_targeted_rung", OFFLINE_AREA, 20,
        "Fund one bounded target-inverse probe for an open process gap.",
        [["agent", "has_goal_invention_policy", "pol"], ["agent", "has_process_gap", "g"],
         ["agent", "has_invention_policy", "ip"], ["agent", "has_thinking_budget", "budget"]],
        And(policy_on(), Eq(A("pol", "targeted_enabled"), L(1.0)),
            Eq(A("g", "status"), L("open")), Eq(A("budget", "enabled"), L(1.0)),
            Not(Exists(N("agent", "has_goal_invention_episode"), "old",
                       Eq(A("old", "gap_name"), A("g", "name"))))),
        [["add_node", "req", "ThinkingBudgetRequest", {
            "status": "pending", "cost": T(A("pol", "rung_cost")),
            "requester_kind": "goal_invention"}],
         ["add_node", "ep", "GoalInventionEpisode", {
            "status": "awaiting_budget", "gap_name": T(A("g", "name")),
            "prior_invention_enabled": T(A("ip", "enabled")),
            "request_cost": T(A("pol", "rung_cost")), "operator": "inverse",
            "candidate_cap": T(A("pol", "candidate_cap"))}],
         ["add_edge", "agent", "has_goal_invention_episode", "ep", {}],
         ["add_edge", "ep", "about_gap", "g", {}],
         ["add_edge", "ep", "has_step_request", "req", {}],
         ["add_edge", "req", "draws_on_thinking_budget", "budget", {}]])


def funding_rules():
    return [
        rule("gi_rung_approved", OFFLINE_AREA, 21,
             "Begin the bounded inverse probe only after the shared budget approves it.",
             [["agent", "has_goal_invention_policy", "pol"],
              ["agent", "has_goal_invention_episode", "ep"], ["ep", "about_gap", "g"],
              ["ep", "has_step_request", "req"], ["agent", "has_invention_policy", "ip"]],
             And(policy_on(), Eq(A("ep", "status"), L("awaiting_budget")),
                 Eq(A("req", "status"), L("approved")), Eq(A("g", "status"), L("open"))),
             [["set_attr", "ep", "status", "active"],
              ["set_attr", "ip", "enabled", 1.0],
              ["set_attr", "g", "status", "targeted_probe"]]),
        rule("gi_rung_denied", OFFLINE_AREA, 21,
             "A denied targeted rung leaves the prior invention policy untouched and the gap unresolved.",
             [["agent", "has_goal_invention_episode", "ep"], ["ep", "about_gap", "g"],
              ["ep", "has_step_request", "req"]],
             And(Eq(A("ep", "status"), L("awaiting_budget")), Eq(A("req", "status"), L("denied"))),
             [["set_attr", "ep", "status", "denied"], ["set_attr", "g", "status", "open"]]),
    ]


def target_rule():
    inv = PInverse(A("h", "params"))
    fp = PFingerprint(inv, A("d", "probes"))
    state = PApply(inv, A("t", "state"))
    return rule("gi_mint_goal_targeted_inverse", ONLINE_AREA, 20,
        "Mint a bounded exact inverse only when its native effect strictly closes the current state-goal gap.",
        [["agent", "has_goal_invention_policy", "pol"], ["agent", "has_goal_invention_episode", "ep"],
         ["ep", "about_gap", "g"], ["g", "about_domain", "d"], ["agent", "has_solve_task", "t"],
         ["t", "has_process_gap", "g"], ["d", "has_held_process", "h"],
         ["agent", "has_invention_policy", "ip"]],
        And(policy_on(), Eq(A("ep", "status"), L("active")),
            Eq(A("pol", "targeted_enabled"), L(1.0)), Eq(A("t", "status"), L("stuck")),
            usable_inverse(), not_none(fp), not_none(state),
            Lt(Count(N("d", "has_invented_process")), A("pol", "candidate_cap"))),
        [["add_node", "s", "ProcessSchema", {
            "kind": T(A("h", "kind")), "domain": T(A("d", "name")),
            "domain_kind": T(A("d", "kind")), "name": T(Vec(L("goal_inverse"), A("h", "name"))),
            "params": T(inv), "fingerprint": T(fp), "support": T(PSupport(inv)),
            "cost": T(A("h", "cost")), "provenance": "goal_targeted_inverse",
            "operator": "inverse", "expr_tree": T(Vec(L("inverse"), A("h", "expr_tree"))),
            "status": "active", "invented": 1, "fingerprint_checked": 1,
            "dedup_checked": 1, "indexed": 1, "effect_evaluation": "exact:native_goal_gap_reduction",
            "verification_receipt": "native_apply_reduces_current_goal_distance",
            "model_epoch": T(A("d", "model_epoch")), "frame_epoch": T(A("d", "frame_epoch")),
            "probe_epoch": T(A("d", "probe_epoch")),
        }],
         ["add_edge", "agent", "has_process_schema", "s", {}],
         ["add_edge", "d", "has_invented_process", "s", {}],
         ["add_edge", "s", "has_arg0", "h", {}],
         ["set_attr", "g", "status", "candidate_found"],
         ["set_attr", "ep", "status", "found"],
         ["set_attr", "t", "status", "active"],
         ["set_attr", "ip", "enabled", T(A("ep", "prior_invention_enabled"))]],
        batch=False)


def no_candidate_rule():
    possible = Exists(N("d", "has_held_process"), "h", usable_inverse("h"))
    return rule("gi_gap_needs_tool", ONLINE_AREA, 22,
        "A funded gap with no supported candidate closes as needs_tool and emits an explicit synthesis interface.",
        [["agent", "has_goal_invention_policy", "pol"], ["agent", "has_goal_invention_episode", "ep"],
         ["ep", "about_gap", "g"], ["g", "about_domain", "d"],
         ["agent", "has_solve_task", "t"], ["t", "has_process_gap", "g"],
         ["agent", "has_invention_policy", "ip"]],
        And(policy_on(), Eq(A("ep", "status"), L("active")), Not(possible)),
        [["add_node", "req", "SynthesisInterfaceRequest", {
            "status": "needs_tool", "missing_effect_kind": T(A("g", "required_effect_kind")),
            "domain": T(A("d", "name")), "reason": "no_supported_covering_inverse",
            "source_epoch": T(A("g", "source_epoch")), "model_epoch": T(A("g", "model_epoch"))}],
         ["add_edge", "agent", "has_synthesis_interface_request", "req", {}],
         ["add_edge", "g", "has_synthesis_interface_request", "req", {}],
         ["set_attr", "g", "status", "needs_tool"],
         ["set_attr", "ep", "status", "needs_tool"],
         ["set_attr", "ip", "enabled", T(A("ep", "prior_invention_enabled"))]],
        batch=False)


def build():
    specs = [
        ("Agent", "has_goal_invention_policy", "GoalInventionPolicy"),
        ("Agent", "has_process_gap", "ProcessGap"),
        ("SolveTask", "has_process_gap", "ProcessGap"),
        ("ProcessGap", "about_domain", "ProcessDomain"),
        ("Agent", "has_goal_invention_episode", "GoalInventionEpisode"),
        ("GoalInventionEpisode", "about_gap", "ProcessGap"),
        ("GoalInventionEpisode", "has_step_request", "ThinkingBudgetRequest"),
        ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("Agent", "has_thinking_budget", "ThinkingBudget"),
        ("Agent", "has_invention_policy", "InventionPolicy"),
        ("Agent", "has_solve_task", "SolveTask"),
        ("Agent", "has_process_domain", "ProcessDomain"),
        ("ProcessDomain", "has_held_process", "ProcessSchema"),
        ("ProcessDomain", "has_invented_process", "ProcessSchema"),
        ("Agent", "has_process_schema", "ProcessSchema"),
        ("ProcessSchema", "has_arg0", "ProcessSchema"),
        ("Agent", "has_synthesis_interface_request", "SynthesisInterfaceRequest"),
        ("ProcessGap", "has_synthesis_interface_request", "SynthesisInterfaceRequest"),
    ]
    return {
        "id": SEED_ID, "version": "1.0.0",
        "depends_on": ["process_schema", "invention_round", "process_solving"],
        "self_load_only": True, "area": ONLINE_AREA,
        "description": "Bounded graph-native goal gaps, funded target-inverse search and explicit unsupported-effect interfaces.",
        "microtheory": {"name": SEED_ID, "description": "Regress stuck goals into typed, funded process gaps."},
        "nodes": [{"local_id": 0, "type": "GoalInventionPolicy", "attrs": {
            "name": "core_goal_invention_policy", "enabled": 0.0, "targeted_enabled": 0.0,
            "max_gaps": 4.0, "candidate_cap": 20.0, "max_support": 4.0,
            "rung_cost": 2.0,
        }}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_goal_invention_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, specs),
        "rules": [gap_rule(), request_rule(), *funding_rules(), target_rule(), no_candidate_rule()],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
