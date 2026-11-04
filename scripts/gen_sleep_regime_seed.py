#!/usr/bin/env python3
"""Generate the opt-in graph-native P13 staged sleep lifecycle."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "sleep_regime.json"
AREA = "sleep_regime"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(v): return {"__term__": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Lte(a, b): return {"type": "Lte", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Max(*xs): return {"type": "Max", "items": list(xs)}
def IDiv(a, b): return {"type": "IDiv", "a": a, "b": b}
def Ashr(a, b): return {"type": "Ashr", "a": a, "b": b}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def IfThenElse(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def quiet_gate():
    return And(
        Eq(A("pol", "enabled"), L(1.0)),
        Gte(A("mode", "default_mode_weight"), A("pol", "entry_weight")),
        Lte(A("mode", "task_demand"), A("pol", "maximum_task_demand")),
        Lte(A("mode", "exteroceptive_load"), A("pol", "maximum_external_load")),
        Lte(A("mode", "interoceptive_urgency"), A("pol", "maximum_urgency")),
        Gte(A("mode", "epoch"), A("cycle", "epoch")),
    )


def receipt_node(stage, *, status="completed", work_kind=None, extra=None):
    attrs = {
        "stage": stage,
        "status": status,
        "cycle_epoch": T(A("cycle", "epoch")),
        "stage_epoch": T(A("mode", "epoch")),
        "expires_epoch": T(Plus(A("cycle", "epoch"), A("pol", "receipt_retention_epochs"))),
        "model_epoch": T(A("pol", "model_epoch")),
        "receipt_kind": work_kind or f"sleep_stage_{stage}",
        "observation_status": "not_observed",
        "provenance_kind": "offline_sleep_stage",
        "shared_budget_debit": T(A("pol", "stage_cost")),
    }
    if extra:
        attrs.update(extra)
    return ["add_node", "receipt", "SleepStageReceipt", attrs]


def stage_rule(name, stage, next_stage, *, support_match=False, decay=False, recombine=False):
    prior_stage = {"consolidate": "replay", "decay": "consolidate",
                   "library": "decay", "recombine": "library"}[stage]
    match = [
        ["agent", "has_sleep_regime_policy", "pol"],
        ["agent", "has_memory_clock", "mode"],
        ["agent", "has_memory_cycle", "cycle"],
        ["agent", "has_thinking_budget", "budget"],
        ["cycle", "has_sleep_stage_receipt", "prior"],
    ]
    if support_match:
        match += [
            ["cycle", "selected_replay", "replay"],
            ["replay", "replays_episode", "episode"],
            ["episode", "instantiates_schema", "schema"],
            ["agent", "has_semantic_support", "support"],
            ["support", "supports_schema", "schema"],
        ]
    effects = []
    if decay:
        age = Max(L(0), Minus(A("mode", "epoch"), A("support", "last_updated_epoch")))
        shift = IDiv(age, A("pol", "decay_half_life"))
        freshness = Ashr(A("pol", "freshness_ceiling"), shift)
        effects += [
            ["set_attr", "support", "sleep_freshness", T(freshness)],
            ["set_attr", "support", "sleep_freshness_epoch", T(A("mode", "epoch"))],
            ["set_attr", "support", "sleep_accessibility", T(freshness)],
            ["set_attr", "support", "sleep_derived_uncertainty", T(Max(
                A("support", "uncertainty"),
                Div(Minus(A("pol", "freshness_ceiling"), freshness), A("pol", "freshness_ceiling")),
            ))],
            ["set_attr", "support", "sleep_decay_count", T(IfThenElse(
                Eq(A("support", "sleep_decay_count"), L(None)), L(1.0),
                Plus(A("support", "sleep_decay_count"), L(1.0)),
            ))],
        ]
    if recombine:
        effects += [
            ["add_node", "proposal", "SleepRecombinationProposal", {
                "status": "advisory",
                "source": "sleep_recombination",
                "cycle_epoch": T(A("cycle", "epoch")),
                "proposal_epoch": T(A("mode", "epoch")),
                "basis_stage": "library",
                "observation_status": "not_observed",
                "provenance_kind": "advisory_recombination",
            }],
            ["add_edge", "agent", "has_sleep_recombination_proposal", "proposal", {}],
            ["add_edge", "proposal", "based_on_sleep_stage", "prior", {}],
        ]
    receipt_status = "deferred" if stage == "library" else "completed"
    effects += [
        receipt_node(stage, status=receipt_status,
                     work_kind=("episodic_freshness_decay" if decay else
                                "awaits_library_learning" if stage == "library" else
                                "advisory_recombination" if recombine else
                                f"sleep_stage_{stage}")),
        ["add_edge", "agent", "has_sleep_stage_receipt", "receipt", {}],
        ["add_edge", "cycle", "has_sleep_stage_receipt", "receipt", {}],
        ["add_edge", "receipt", "follows_stage_receipt", "prior", {}],
        ["set_attr", "cycle", "sleep_stage_cursor", next_stage],
        ["set_attr", "cycle", "sleep_stage_epoch", T(A("mode", "epoch"))],
        ["set_attr", "budget", "remaining", T(Max(L(0), Minus(A("budget", "remaining"), A("pol", "stage_cost"))))],
    ]
    if support_match:
        effects.append(["add_edge", "receipt", "references_semantic_support", "support", {}])
    where = [
        quiet_gate(),
        Gte(A("budget", "enabled"), L(1.0)),
        Gte(A("budget", "remaining"), A("pol", "stage_cost")),
        Eq(A("cycle", "status"), L("completed")),
        Eq(A("cycle", "mode"), L("offline")),
        Eq(A("cycle", "sleep_stage_cursor"), L(stage)),
        Gt(A("mode", "epoch"), A("cycle", "sleep_stage_epoch")),
        Eq(A("prior", "stage"), L(prior_stage)),
    ]
    return {
        "name": name,
        "area": "intrinsic_state",
        "order": 30 + ["consolidate", "decay", "library", "recombine"].index(stage),
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": f"Advance one funded, quiet-epoch sleep stage: {stage} -> {next_stage}.",
        "match": match,
        "where": And(*where),
        "effects": effects,
    }


def rules():
    stale_cancel = {
        "name": "sr_cancel_pending_cycle_on_model_epoch_change",
        "area": "intrinsic_state",
        "order": 19,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Cancel a resumable sleep cursor when its provenance model epoch no longer matches the policy epoch.",
        "match": [["agent", "has_sleep_regime_policy", "pol"],
                  ["agent", "has_memory_cycle", "cycle"],
                  ["cycle", "has_sleep_stage_receipt", "receipt"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Not(Eq(A("cycle", "sleep_stage_cursor"), L("complete"))),
                      Not(Eq(A("cycle", "sleep_stage_cursor"), L("canceled"))),
                      Not(Eq(A("receipt", "model_epoch"), A("pol", "model_epoch")))),
        "effects": [["set_attr", "cycle", "sleep_stage_cursor", "canceled"],
                    ["set_attr", "cycle", "sleep_cancel_reason", "stale_model_epoch"]],
    }
    begin = {
        "name": "sr_begin_after_existing_replay",
        "area": "intrinsic_state",
        "order": 20,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Claim a completed offline scheduler cycle after EWM has emitted its single replay receipt.",
        "match": [
            ["agent", "has_sleep_regime_policy", "pol"],
            ["agent", "has_memory_clock", "mode"],
            ["agent", "has_memory_cycle", "cycle"],
            ["agent", "has_thinking_budget", "budget"],
            ["cycle", "selected_replay", "replay"],
            ["cycle", "has_consolidation_task_request", "request"],
        ],
        "where": And(
            quiet_gate(),
            Eq(A("cycle", "source"), L("consolidation_scheduler")),
            Eq(A("cycle", "mode"), L("offline")),
            Eq(A("cycle", "status"), L("completed")),
            Eq(A("cycle", "sleep_stage_cursor"), L("unclaimed")),
            Gte(A("budget", "enabled"), L(1.0)),
            Eq(A("request", "status"), L("serviced")),
        ),
        "effects": [
            receipt_node("replay", work_kind="delegated_existing_ewm_replay", extra={
                "replay_epoch": T(A("replay", "epoch")),
                "shared_budget_debit": T(A("request", "cost")),
            }),
            ["add_edge", "agent", "has_sleep_stage_receipt", "receipt", {}],
            ["add_edge", "cycle", "has_sleep_stage_receipt", "receipt", {}],
            ["add_edge", "receipt", "delegates_to_replay", "replay", {}],
            ["add_edge", "receipt", "funded_by_request", "request", {}],
            ["set_attr", "cycle", "sleep_stage_cursor", "consolidate"],
            ["set_attr", "cycle", "sleep_stage_epoch", T(A("mode", "epoch"))],
        ],
    }
    retention = {
        "name": "sr_extend_scheduler_retention_for_stages",
        "area": AREA,
        "order": 5,
        "latency_class": "hard_realtime",
        "match": [["agent", "has_sleep_regime_policy", "pol"],
                  ["agent", "has_consolidation_scheduler_policy", "scheduler"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Lt(A("scheduler", "retention_epochs"), A("pol", "cycle_retention_epochs"))),
        "effects": [["set_attr", "scheduler", "retention_epochs", T(A("pol", "cycle_retention_epochs"))]],
    }
    cleanup = {
        "name": "sr_prune_expired_receipts_and_advisories",
        "area": AREA,
        "order": 80,
        "latency_class": "hard_realtime",
        "match": [["agent", "has_sleep_regime_policy", "pol"],
                  ["agent", "has_memory_clock", "mode"],
                  ["agent", "has_sleep_stage_receipt", "receipt"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Gte(A("mode", "epoch"), A("receipt", "expires_epoch"))),
        "effects": [["del_node", "receipt"]],
    }
    proposal_cleanup = {
        "name": "sr_prune_expired_recombination_advisories",
        "area": AREA,
        "order": 81,
        "latency_class": "hard_realtime",
        "match": [["agent", "has_sleep_regime_policy", "pol"],
                  ["agent", "has_memory_clock", "mode"],
                  ["agent", "has_sleep_recombination_proposal", "proposal"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Gte(A("mode", "epoch"), Plus(A("proposal", "cycle_epoch"), A("pol", "cycle_retention_epochs")))),
        "effects": [["del_node", "proposal"]],
    }
    return [retention, stale_cancel, begin,
            stage_rule("sr_consolidate_after_semantic_receipt", "consolidate", "decay", support_match=True),
            stage_rule("sr_decay_episodic_semantic_accessibility", "decay", "library", support_match=True, decay=True),
            stage_rule("sr_yield_to_library_learning_stage", "library", "recombine"),
            stage_rule("sr_recombine_as_advisory_only", "recombine", "complete", recombine=True),
            cleanup, proposal_cleanup]


def build():
    relations = [
        ("Agent", "has_sleep_regime_policy", "SleepRegimePolicy"),
        ("Agent", "has_memory_cycle", "MemoryCycle"),
        ("MemoryCycle", "selected_replay", "ReplayTrace"),
        ("MemoryCycle", "has_sleep_stage_receipt", "SleepStageReceipt"),
        ("SleepStageReceipt", "delegates_to_replay", "ReplayTrace"),
        ("SleepStageReceipt", "follows_stage_receipt", "SleepStageReceipt"),
        ("Agent", "has_sleep_stage_receipt", "SleepStageReceipt"),
        ("Agent", "has_sleep_recombination_proposal", "SleepRecombinationProposal"),
        ("SleepRecombinationProposal", "based_on_sleep_stage", "SleepStageReceipt"),
        ("SleepStageReceipt", "references_semantic_support", "SemanticSupport"),
        ("SleepStageReceipt", "funded_by_request", "SystemTwoEscalation"),
        ("Agent", "has_memory_clock", "NetworkModeState"),
        ("Agent", "has_thinking_budget", "ThinkingBudget"),
        ("Agent", "has_consolidation_scheduler_policy", "ConsolidationSchedulerPolicy"),
        ("MemoryCycle", "has_consolidation_task_request", "SystemTwoEscalation"),
        ("ReplayTrace", "replays_episode", "Episode"),
        ("Episode", "instantiates_schema", "MemorySchema"),
        ("Agent", "has_semantic_support", "SemanticSupport"),
        ("SemanticSupport", "supports_schema", "MemorySchema"),
    ]
    return {
        "id": "sleep_regime",
        "version": "1.0.0",
        "depends_on": ["consolidation_scheduler", "episodic_working_memory_core", "thinking_budget"],
        "self_load_only": True,
        "area": AREA,
        "description": "Opt-in staged offline lifecycle over the existing replay scheduler, with resumable graph cursor, shared-budget stage debits and advisory recombination.",
        "microtheory": {"name": AREA, "description": "Advance one receipt-gated sleep stage per quiet epoch."},
        "nodes": [{"local_id": 0, "type": "SleepRegimePolicy", "attrs": {
            "name": "sleep_regime_policy", "enabled": 0.0,
            "entry_weight": 0.6, "maximum_task_demand": 0.2,
            "maximum_external_load": 0.2, "maximum_urgency": 0.2,
            "stage_cost": 1.0, "cycle_retention_epochs": 12.0,
            "receipt_retention_epochs": 8.0,
            "model_epoch": 0.0,
            "decay_half_life": 4.0, "freshness_ceiling": 1024.0,
        }}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_sleep_regime_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
                         "src": {"type": src, "var": "src"}, "edge_type": edge,
                         "tgt": {"type": tgt, "var": "tgt"}}
                        for src, edge, tgt in relations],
        "rules": rules(),
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
