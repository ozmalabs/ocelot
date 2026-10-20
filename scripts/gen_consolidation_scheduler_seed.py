#!/usr/bin/env python3
"""Author the consolidation_scheduler seed (P1.B1).

Binds NetworkModeState as the memory clock for episodic_working_memory_core,
mints cooldown-paced offline MemoryCycle nodes (plus a SystemTwoEscalation
recruiting memory_replay, memory_consolidation, and memory_cleanup) during
low-demand default-mode epochs, and prunes completed cycles after retention.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from gen_capability_collapse_seed import (
    A,
    And,
    Count,
    Eq,
    Gt,
    Gte,
    L,
    Lte,
    N,
    Plus,
    T,
    ZERO,
)

AREA = "consolidation_scheduler"


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def policy_enabled():
    return Eq(A("pol", "enabled"), L(1.0))


def bind_memory_clock_rule():
    return {
        "name": "csch_bind_memory_clock",
        "area": AREA,
        "order": 5,
        "latency_class": "hard_realtime",
        "comment": "Bind NetworkModeState as the canonical memory clock when none is bound.",
        "match": [
            ["agent", "has_consolidation_scheduler_policy", "pol"],
            ["agent", "has_network_mode_state", "mode"],
        ],
        "where": And(
            policy_enabled(),
            Eq(Count(N("agent", "has_memory_clock")), ZERO),
        ),
        "effects": [
            ["add_edge", "agent", "has_memory_clock", "mode", {}],
        ],
    }


def mint_offline_cycle_rule():
    deadline_term = Plus(A("mode", "epoch"), A("pol", "retention_epochs"))
    return {
        "name": "csch_mint_offline_cycle",
        "area": AREA,
        "order": 15,
        "latency_class": "hard_realtime",
        "comment": (
            "Mint an offline MemoryCycle and recruit memory_replay, memory_consolidation, "
            "and memory_cleanup when default_mode_weight is high, task_demand is low, "
            "and the cooldown has elapsed."
        ),
        "match": [
            ["agent", "has_consolidation_scheduler_policy", "pol"],
            ["agent", "has_network_mode_state", "mode"],
            ["agent", "has_memory_replay_task_set", "replay_ts"],
            ["agent", "has_memory_consolidation_task_set", "cons_ts"],
            ["agent", "has_memory_cleanup_task_set", "clean_ts"],
        ],
        "where": And(
            policy_enabled(),
            Gte(A("mode", "default_mode_weight"), A("pol", "entry_weight")),
            Lte(A("mode", "task_demand"), A("pol", "maximum_task_demand")),
            Gte(
                Minus(A("mode", "epoch"), A("pol", "last_cycle_epoch")),
                A("pol", "cooldown_epochs"),
            ),
            Gt(Count(N("agent", "recorded_episode")), ZERO),
        ),
        "effects": [
            ["add_node", "cycle", "MemoryCycle", {
                "status": "pending",
                "mode": "offline",
                "epoch": T(A("mode", "epoch")),
                "source": "consolidation_scheduler",
            }],
            ["add_node", "req", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "offline_consolidation",
                "request_kind": "consolidation",
                "input_epoch": T(A("mode", "epoch")),
                "deadline_epoch": T(deadline_term),
            }],
            ["add_edge", "agent", "has_memory_cycle", "cycle", {}],
            ["add_edge", "cycle", "has_consolidation_task_request", "req", {}],
            ["add_edge", "req", "about_context", "mode", {}],
            ["add_edge", "req", "recruits_task_set", "replay_ts", {}],
            ["add_edge", "req", "recruits_task_set", "cons_ts", {}],
            ["add_edge", "req", "recruits_task_set", "clean_ts", {}],
            ["set_attr", "pol", "last_cycle_epoch", T(A("mode", "epoch"))],
        ],
    }


def prune_completed_cycle_request_rule():
    return {
        "name": "csch_prune_completed_cycle_request",
        "area": AREA,
        "order": 54,
        "latency_class": "hard_realtime",
        "comment": "Prune the consolidation SystemTwoEscalation once its MemoryCycle is past retention and its ReplayTrace is gone.",
        "match": [
            ["agent", "has_consolidation_scheduler_policy", "pol"],
            ["agent", "has_network_mode_state", "mode"],
            ["agent", "has_memory_cycle", "cycle"],
            ["cycle", "has_consolidation_task_request", "req"],
        ],
        "where": And(
            policy_enabled(),
            Eq(A("cycle", "status"), L("completed")),
            Gte(
                A("mode", "epoch"),
                Plus(A("cycle", "epoch"), A("pol", "retention_epochs")),
            ),
            Eq(Count(N("cycle", "selected_replay")), ZERO),
        ),
        "effects": [
            ["del_node", "req"],
        ],
    }


def prune_completed_cycle_rule():
    return {
        "name": "csch_prune_completed_cycle",
        "area": AREA,
        "order": 55,
        "latency_class": "hard_realtime",
        "comment": "Prune a completed MemoryCycle after retention once its selected ReplayTrace and request have been cleaned up.",
        "match": [
            ["agent", "has_consolidation_scheduler_policy", "pol"],
            ["agent", "has_network_mode_state", "mode"],
            ["agent", "has_memory_cycle", "cycle"],
        ],
        "where": And(
            policy_enabled(),
            Eq(A("cycle", "status"), L("completed")),
            Gte(
                A("mode", "epoch"),
                Plus(A("cycle", "epoch"), A("pol", "retention_epochs")),
            ),
            Eq(Count(N("cycle", "selected_replay")), ZERO),
            Eq(Count(N("cycle", "has_consolidation_task_request")), ZERO),
        ),
        "effects": [
            ["del_node", "cycle"],
        ],
    }


def productions():
    specs = [
        ("Agent", "has_consolidation_scheduler_policy", "ConsolidationSchedulerPolicy"),
        ("Agent", "has_memory_replay_task_set", "SystemTwoTaskSet"),
        ("Agent", "has_memory_consolidation_task_set", "SystemTwoTaskSet"),
        ("Agent", "has_memory_cleanup_task_set", "SystemTwoTaskSet"),
        ("Agent", "has_memory_clock", "NetworkModeState"),
        ("Agent", "has_memory_cycle", "MemoryCycle"),
        ("MemoryCycle", "has_consolidation_task_request", "SystemTwoEscalation"),
        ("SystemTwoEscalation", "about_context", "NetworkModeState"),
        ("SystemTwoEscalation", "recruits_task_set", "SystemTwoTaskSet"),
    ]
    return [
        {
            "provenance": f"seed:consolidation_scheduler:{edge_type}:{src}:{tgt}",
            "src": {"type": src, "var": "src"},
            "edge_type": edge_type,
            "tgt": {"type": tgt, "var": "tgt"},
        }
        for src, edge_type, tgt in specs
    ]


def build():
    return {
        "id": "consolidation_scheduler",
        "version": "1.0.0",
        "depends_on": [
            "episodic_working_memory_core",
            "default_mode_core",
        ],
        "area": AREA,
        "description": (
            "Opt-in offline replay and consolidation scheduler. Binds NetworkModeState "
            "as the memory clock, mints cooldown-paced offline MemoryCycle nodes when "
            "default_mode_weight is high and task_demand is low, recruits the EWM "
            "background replay/consolidation/cleanup areas, and prunes completed cycles "
            "after retention."
        ),
        "microtheory": {
            "name": "consolidation_scheduler",
            "description": (
                "Quiet default-mode epochs schedule bounded offline episodic replay "
                "and semantic consolidation without unbounded transient growth."
            ),
        },
        "nodes": [
            {
                "local_id": 0,
                "type": "ConsolidationSchedulerPolicy",
                "attrs": {
                    "enabled": 0.0,
                    "entry_weight": 0.6,
                    "maximum_task_demand": 0.2,
                    "cooldown_epochs": 4.0,
                    "retention_epochs": 4.0,
                    "last_cycle_epoch": -1000000.0,
                },
            },
            {
                "local_id": 1,
                "type": "SystemTwoTaskSet",
                "attrs": {
                    "name": "consolidation_memory_replay",
                    "area": "memory_replay",
                    "task_kind": "offline_replay",
                    "enabled": 1.0,
                },
            },
            {
                "local_id": 2,
                "type": "SystemTwoTaskSet",
                "attrs": {
                    "name": "consolidation_memory_consolidation",
                    "area": "memory_consolidation",
                    "task_kind": "semantic_consolidation",
                    "enabled": 1.0,
                },
            },
            {
                "local_id": 3,
                "type": "SystemTwoTaskSet",
                "attrs": {
                    "name": "consolidation_memory_cleanup",
                    "area": "memory_cleanup",
                    "task_kind": "memory_transient_cleanup",
                    "enabled": 1.0,
                },
            },
        ],
        "edges": [
            {
                "src": {"role": "agent_root"},
                "type": "has_consolidation_scheduler_policy",
                "tgt": {"local": 0},
                "attrs": {},
            },
            {
                "src": {"role": "agent_root"},
                "type": "has_memory_replay_task_set",
                "tgt": {"local": 1},
                "attrs": {},
            },
            {
                "src": {"role": "agent_root"},
                "type": "has_memory_consolidation_task_set",
                "tgt": {"local": 2},
                "attrs": {},
            },
            {
                "src": {"role": "agent_root"},
                "type": "has_memory_cleanup_task_set",
                "tgt": {"local": 3},
                "attrs": {},
            },
        ],
        "productions": productions(),
        "rules": [
            bind_memory_clock_rule(),
            mint_offline_cycle_rule(),
            prune_completed_cycle_request_rule(),
            prune_completed_cycle_rule(),
        ],
    }


def main():
    out = ROOT / "seeds" / "consolidation_scheduler.json"
    out.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
