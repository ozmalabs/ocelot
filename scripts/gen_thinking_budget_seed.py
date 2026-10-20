#!/usr/bin/env python3
"""Author the `thinking_budget` seed (P2.A5).

Provides a shared `ThinkingBudget` resource pool for System-2 requesters,
refilled once per `NetworkModeState.epoch` up to `capacity` (optionally derived
from `ManifoldPolicy.future_manifold_projection_budget` via `tb_fund_from_horizon`),
with sequential debiting and deduplicated `ThinkingBudgetDenial` records when
`remaining < cost`.
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
    Eq,
    Gt,
    Gte,
    L,
    Max,
    N,
    Not,
    Plus,
    T,
)

AREA = "thinking_budget"
OUT = ROOT / "seeds" / "thinking_budget.json"


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def Exists(source, var_name, predicate):
    return {
        "type": "Exists",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def Min(*items):
    return {"type": "Min", "items": list(items)}


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Times(*items):
    return {"type": "Times", "items": list(items)}


def budget_enabled(var="budget"):
    return Gte(A(var, "enabled"), L(1.0))


def derived_capacity_term():
    return Min(
        A("budget", "capacity_ceiling"),
        Times(
            A("pol", "future_manifold_projection_budget"),
            A("budget", "funding_gain"),
        ),
    )


def denial_exists_for(kind_term):
    return Exists(
        N("agent", "has_thinking_budget_denial"),
        "d",
        And(
            Eq(A("d", "requester_kind"), kind_term),
            Eq(A("d", "epoch"), A("mode", "epoch")),
        ),
    )


def fund_from_horizon_rule():
    cap_term = derived_capacity_term()
    return {
        "name": "tb_fund_from_horizon",
        "area": AREA,
        "order": 8,
        "latency_class": "hard_realtime",
        "comment": (
            "When the agent has `governs_horizon -> ManifoldPolicy` with a positive "
            "`future_manifold_projection_budget`, scale `ThinkingBudget.capacity` "
            "as `Min(capacity_ceiling, future_manifold_projection_budget * funding_gain)`."
        ),
        "match": [
            ["agent", "has_thinking_budget", "budget"],
            ["agent", "governs_horizon", "pol"],
        ],
        "where": And(
            budget_enabled(),
            Gt(A("pol", "future_manifold_projection_budget"), L(0.0)),
            Not(Eq(A("budget", "capacity"), cap_term)),
        ),
        "effects": [
            ["set_attr", "budget", "capacity", T(cap_term)],
            ["set_attr", "budget", "remaining", T(Min(A("budget", "remaining"), cap_term))],
        ],
    }


def refill_once_per_epoch_rule():
    return {
        "name": "tb_refill_once_per_epoch",
        "area": AREA,
        "order": 9,
        "latency_class": "hard_realtime",
        "comment": (
            "Refill `ThinkingBudget.remaining` by `refill_per_epoch` up to `capacity` "
            "at most once per `NetworkModeState.epoch`."
        ),
        "match": [
            ["agent", "has_thinking_budget", "budget"],
            ["agent", "has_network_mode_state", "mode"],
        ],
        "where": And(
            budget_enabled(),
            Gt(A("mode", "epoch"), A("budget", "last_refill_epoch")),
        ),
        "effects": [
            [
                "set_attr",
                "budget",
                "remaining",
                T(
                    Min(
                        A("budget", "capacity"),
                        Plus(A("budget", "remaining"), A("budget", "refill_per_epoch")),
                    )
                ),
            ],
            ["set_attr", "budget", "last_refill_epoch", T(A("mode", "epoch"))],
        ],
    }


def pass_when_disabled_rule():
    return {
        "name": "tb_pass_when_disabled",
        "area": AREA,
        "order": 10,
        "latency_class": "hard_realtime",
        "comment": "When ThinkingBudget is disabled, approve pending requests without debiting.",
        "match": [
            ["agent", "has_thinking_budget", "budget"],
            ["req", "draws_on_thinking_budget", "budget"],
        ],
        "where": And(
            Not(budget_enabled()),
            Eq(A("req", "status"), L("pending")),
        ),
        "effects": [
            ["set_attr", "req", "status", "approved"],
        ],
    }


def debit_request_rule():
    return {
        "name": "tb_debit_request",
        "area": AREA,
        "order": 10,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": (
            "Approve and debit a pending request when `ThinkingBudget.remaining >= req.cost` "
            "(non-batched so multiple requests in one epoch debit sequentially)."
        ),
        "match": [
            ["agent", "has_thinking_budget", "budget"],
            ["agent", "has_network_mode_state", "mode"],
            ["req", "draws_on_thinking_budget", "budget"],
        ],
        "where": And(
            budget_enabled(),
            Eq(A("req", "status"), L("pending")),
            Gte(A("budget", "remaining"), A("req", "cost")),
        ),
        "effects": [
            ["set_attr", "req", "status", "approved"],
            ["set_attr", "req", "debited_epoch", T(A("mode", "epoch"))],
            [
                "set_attr",
                "budget",
                "remaining",
                T(Max(L(0.0), Minus(A("budget", "remaining"), A("req", "cost")))),
            ],
        ],
    }


def record_exhaustion_rule():
    return {
        "name": "tb_record_exhaustion",
        "area": AREA,
        "order": 11,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": (
            "When a pending request cannot be funded because `remaining < cost`, "
            "mark it denied and mint at most one `ThinkingBudgetDenial` per "
            "(requester_kind, epoch)."
        ),
        "match": [
            ["agent", "has_thinking_budget", "budget"],
            ["agent", "has_network_mode_state", "mode"],
            ["req", "draws_on_thinking_budget", "budget"],
        ],
        "where": And(
            budget_enabled(),
            Eq(A("req", "status"), L("pending")),
            Lt(A("budget", "remaining"), A("req", "cost")),
            Not(denial_exists_for(A("req", "requester_kind"))),
        ),
        "effects": [
            ["set_attr", "req", "status", "denied"],
            ["set_attr", "req", "terminal_reason", "budget_exhausted"],
            [
                "add_node",
                "denial",
                "ThinkingBudgetDenial",
                {
                    "reason": "budget_exhausted",
                    "requester_kind": T(A("req", "requester_kind")),
                    "epoch": T(A("mode", "epoch")),
                },
            ],
            ["add_edge", "agent", "has_thinking_budget_denial", "denial", {}],
        ],
    }


def deny_exhausted_request_after_denial_rule():
    return {
        "name": "tb_deny_exhausted_request_after_denial",
        "area": AREA,
        "order": 12,
        "latency_class": "hard_realtime",
        "comment": (
            "Mark subsequent exhausted requests of the same requester_kind in the "
            "same epoch as denied without duplicating `ThinkingBudgetDenial`."
        ),
        "match": [
            ["agent", "has_thinking_budget", "budget"],
            ["agent", "has_network_mode_state", "mode"],
            ["req", "draws_on_thinking_budget", "budget"],
        ],
        "where": And(
            budget_enabled(),
            Eq(A("req", "status"), L("pending")),
            Lt(A("budget", "remaining"), A("req", "cost")),
            denial_exists_for(A("req", "requester_kind")),
        ),
        "effects": [
            ["set_attr", "req", "status", "denied"],
            ["set_attr", "req", "terminal_reason", "budget_exhausted"],
        ],
    }


def productions():
    specs = [
        ("Agent", "has_thinking_budget", "ThinkingBudget"),
        ("Agent", "has_thinking_budget_denial", "ThinkingBudgetDenial"),
        ("Agent", "governs_horizon", "ManifoldPolicy"),
        ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("SystemTwoEscalation", "draws_on_thinking_budget", "ThinkingBudget"),
    ]
    return [
        {
            "provenance": f"seed:thinking_budget:{edge_type}:{src}:{tgt}",
            "src": {"type": src, "var": "src"},
            "edge_type": edge_type,
            "tgt": {"type": tgt, "var": "tgt"},
        }
        for src, edge_type, tgt in specs
    ]


def build():
    return {
        "id": "thinking_budget",
        "version": "1.0.0",
        "depends_on": ["default_mode_core"],
        "area": AREA,
        "description": (
            "Shared ThinkingBudget resource pool for System-2 requesters (P2.A5). "
            "Refills once per NetworkModeState.epoch up to capacity (optionally funded "
            "from ManifoldPolicy.future_manifold_projection_budget), debits approved "
            "requests, and records deduplicated ThinkingBudgetDenial nodes on exhaustion."
        ),
        "microtheory": {
            "name": "thinking_budget",
            "description": (
                "System-2 escalation and offline consolidation requesters draw from a "
                "shared epoch-refilled ThinkingBudget."
            ),
        },
        "nodes": [
            {
                "local_id": 0,
                "type": "ThinkingBudget",
                "attrs": {
                    "name": "core_thinking_budget",
                    "enabled": 0.0,
                    "capacity": 16.0,
                    "capacity_ceiling": 64.0,
                    "funding_gain": 2.0,
                    "remaining": 16.0,
                    "refill_per_epoch": 2.0,
                    "last_refill_epoch": -1.0,
                },
            }
        ],
        "edges": [
            {
                "src": {"role": "agent_root"},
                "type": "has_thinking_budget",
                "tgt": {"local": 0},
                "attrs": {},
            }
        ],
        "productions": productions(),
        "rules": [
            fund_from_horizon_rule(),
            refill_once_per_epoch_rule(),
            pass_when_disabled_rule(),
            debit_request_rule(),
            record_exhaustion_rule(),
            deny_exhausted_request_after_denial_rule(),
        ],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
