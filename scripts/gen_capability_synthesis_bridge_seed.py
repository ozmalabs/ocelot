#!/usr/bin/env python3
"""Author the integer-native capability_synthesis_bridge seed (P1.A1).

Bridges CapabilityCollapseState.synthesis_requested to graph-native
CapabilitySynthesisRequest and SelfConcern nodes, and re-arms collapse
when a unique higher-order CapabilityProgram is supplied.
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
    Filter,
    Gt,
    Gte,
    L,
    Max,
    N,
    Not,
    ONE,
    Or,
    Plus,
    T,
    ZERO,
    numeric,
)

AREA = "general_cognition_synthesis_bridge"


def open_request_rule():
    existing_for_epoch_or_open = Filter(
        N("state", "has_capability_synthesis_request"),
        "r",
        Or(
            Eq(A("r", "status"), L("open")),
            Eq(numeric("r", "request_epoch"), numeric("state", "request_epoch")),
        ),
    )
    return {
        "name": "csb_open_request",
        "area": AREA,
        "order": 3,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Mint an open CapabilitySynthesisRequest and SelfConcern when collapse is unresolved and requests synthesis.",
        "match": [
            ["agent", "has_capability_synthesis_bridge_policy", "policy"],
            ["state", "has_active_capability_program", "program"],
        ],
        "where": And(
            Eq(numeric("policy", "enabled"), ONE),
            Eq(numeric("state", "synthesis_requested"), ONE),
            Eq(A("state", "stage"), L("unresolved")),
            Not(Eq(A("state", "override_status"), L("conflicting_leases"))),
            Eq(Count(existing_for_epoch_or_open), ZERO),
        ),
        "effects": [
            ["add_node", "r", "CapabilitySynthesisRequest", {
                "status": "open",
                "reason": T(A("state", "unresolved_reason")),
                "request_epoch": T(numeric("state", "request_epoch")),
                "order": T(numeric("program", "order")),
                "residual_quanta": T(numeric("program", "residual_quanta")),
                "boundary_quanta": T(numeric("program", "capability_boundary_quanta")),
            }],
            ["add_edge", "state", "has_capability_synthesis_request", "r"],
            ["add_edge", "r", "requests_higher_program_for", "program"],
            ["add_node", "sc", "SelfConcern", {
                "status": "noted",
                "source": "capability_collapse",
                "kind": "capability_synthesis",
                "content": T(A("state", "unresolved_reason")),
            }],
            ["add_edge", "agent", "has_self_concern", "sc"],
            ["add_edge", "sc", "about_request", "r"],
        ],
    }


def open_authority_conflict_rule():
    existing_conflict = Filter(
        N("state", "has_capability_synthesis_request"),
        "r",
        Eq(A("r", "reason"), L("conflicting_leases")),
    )
    return {
        "name": "csb_open_authority_conflict",
        "area": AREA,
        "order": 5,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "File a conflicting_leases synthesis request and SelfConcern without re-arming.",
        "match": [
            ["agent", "has_capability_synthesis_bridge_policy", "policy"],
            ["state", "has_active_capability_program", "program"],
        ],
        "where": And(
            Eq(numeric("policy", "enabled"), ONE),
            Eq(numeric("state", "synthesis_requested"), ONE),
            Eq(A("state", "override_status"), L("conflicting_leases")),
            Eq(Count(existing_conflict), ZERO),
        ),
        "effects": [
            ["add_node", "r", "CapabilitySynthesisRequest", {
                "status": "open",
                "reason": "conflicting_leases",
                "request_epoch": T(numeric("state", "request_epoch")),
                "order": T(numeric("program", "order")),
                "residual_quanta": T(numeric("program", "residual_quanta")),
                "boundary_quanta": T(numeric("program", "capability_boundary_quanta")),
            }],
            ["add_edge", "state", "has_capability_synthesis_request", "r"],
            ["add_edge", "r", "requests_higher_program_for", "program"],
            ["add_node", "sc", "SelfConcern", {
                "status": "noted",
                "source": "capability_collapse",
                "kind": "capability_synthesis",
                "content": "conflicting_leases",
            }],
            ["add_edge", "agent", "has_self_concern", "sc"],
            ["add_edge", "sc", "about_request", "r"],
        ],
    }


def supplied_rearm_oneshot_rule():
    return {
        "name": "csb_supplied_rearm_oneshot",
        "area": AREA,
        "order": 0,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Re-arm one-shot collapse when a unique higher-order CapabilityProgram is supplied.",
        "match": [
            ["agent", "has_capability_synthesis_bridge_policy", "policy"],
            ["state", "has_capability_synthesis_request", "r"],
            ["r", "requests_higher_program_for", "program"],
        ],
        "where": And(
            Eq(numeric("policy", "enabled"), ONE),
            Eq(A("r", "status"), L("open")),
            Not(Eq(A("r", "reason"), L("conflicting_leases"))),
            Eq(Count(N("program", "continues_to_higher_order_capability_program")), ONE),
            Not(Eq(numeric("state", "continuous_enabled"), ONE)),
        ),
        "effects": [
            ["set_attr", "r", "status", "supplied"],
            ["set_attr", "state", "stage", "ready"],
            ["set_attr", "state", "collapse_armed", 1],
            ["set_attr", "state", "request_epoch",
             T(Plus(numeric("state", "request_epoch"), ONE))],
        ],
    }


def supplied_rearm_continuous_rule():
    return {
        "name": "csb_supplied_rearm_continuous",
        "area": AREA,
        "order": 0,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Advance cycle_request_epoch in continuous mode when a unique higher-order CapabilityProgram is supplied.",
        "match": [
            ["agent", "has_capability_synthesis_bridge_policy", "policy"],
            ["state", "has_capability_synthesis_request", "r"],
            ["r", "requests_higher_program_for", "program"],
        ],
        "where": And(
            Eq(numeric("policy", "enabled"), ONE),
            Eq(A("r", "status"), L("open")),
            Not(Eq(A("r", "reason"), L("conflicting_leases"))),
            Eq(Count(N("program", "continues_to_higher_order_capability_program")), ONE),
            Eq(numeric("state", "continuous_enabled"), ONE),
            Gte(numeric("state", "completed_cycle_epoch"),
                numeric("state", "request_epoch")),
        ),
        "effects": [
            ["set_attr", "r", "status", "supplied"],
            ["set_attr", "state", "cycle_request_epoch", T(Plus(
                Max(
                    numeric("state", "cycle_request_epoch"),
                    numeric("state", "completed_cycle_epoch"),
                ),
                ONE,
            ))],
        ],
    }


def close_on_settlement_rule():
    return {
        "name": "csb_close_on_settlement",
        "area": AREA,
        "order": 3,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Mark a supplied synthesis request resolved once the re-armed collapse settles.",
        "match": [
            ["agent", "has_capability_synthesis_bridge_policy", "policy"],
            ["state", "has_capability_synthesis_request", "r"],
        ],
        "where": And(
            Eq(numeric("policy", "enabled"), ONE),
            Eq(A("r", "status"), L("supplied")),
            Eq(A("state", "stage"), L("settled")),
        ),
        "effects": [
            ["set_attr", "r", "status", "resolved"],
            ["set_attr", "r", "resolved_order",
             T(numeric("state", "achieved_order"))],
        ],
    }


def close_on_ambiguity_rule():
    return {
        "name": "csb_close_on_ambiguity",
        "area": AREA,
        "order": 3,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Mark an open synthesis request ambiguous without re-arming when multiple continuations are attached.",
        "match": [
            ["agent", "has_capability_synthesis_bridge_policy", "policy"],
            ["state", "has_capability_synthesis_request", "r"],
            ["r", "requests_higher_program_for", "program"],
        ],
        "where": And(
            Eq(numeric("policy", "enabled"), ONE),
            Eq(A("r", "status"), L("open")),
            Gt(Count(N("program", "continues_to_higher_order_capability_program")), ONE),
        ),
        "effects": [
            ["set_attr", "r", "status", "ambiguous"],
        ],
    }


def productions():
    specs = [
        ("Agent", "has_capability_synthesis_bridge_policy", "CapabilitySynthesisBridgePolicy"),
        ("CapabilityCollapseState", "has_capability_synthesis_request", "CapabilitySynthesisRequest"),
        ("CapabilitySynthesisRequest", "requests_higher_program_for", "CapabilityProgram"),
        ("Agent", "has_self_concern", "SelfConcern"),
        ("SelfConcern", "about_request", "CapabilitySynthesisRequest"),
    ]
    return [
        {
            "provenance": f"seed:capability_synthesis_bridge:{edge_type}",
            "src": {"type": src, "var": "src"},
            "edge_type": edge_type,
            "tgt": {"type": tgt, "var": "tgt"},
        }
        for src, edge_type, tgt in specs
    ]


def build():
    return {
        "id": "capability_synthesis_bridge",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": ["capability_collapse"],
        "area": "general_cognition",
        "description": (
            "Opt-in integer-native bridge turning CapabilityCollapseState.synthesis_requested "
            "into explicit CapabilitySynthesisRequest and SelfConcern nodes, and re-arming "
            "collapse when a unique higher-order CapabilityProgram is supplied."
        ),
        "microtheory": {
            "name": "capability_synthesis_bridge",
            "description": (
                "Unresolved capability boundaries file explicit synthesis requests on the "
                "SelfConcern spine and re-arm collapse automatically once a unique higher-order "
                "CapabilityProgram continuation arrives."
            ),
        },
        "nodes": [
            {
                "local_id": 0,
                "type": "CapabilitySynthesisBridgePolicy",
                "attrs": {
                    "enabled": 0,
                },
            },
        ],
        "edges": [
            {
                "src": {"role": "agent_root"},
                "type": "has_capability_synthesis_bridge_policy",
                "tgt": {"local": 0},
                "attrs": {},
            },
        ],
        "productions": productions(),
        "rules": [
            open_request_rule(),
            open_authority_conflict_rule(),
            supplied_rearm_oneshot_rule(),
            supplied_rearm_continuous_rule(),
            close_on_settlement_rule(),
            close_on_ambiguity_rule(),
        ],
    }


def main():
    out = ROOT / "seeds" / "capability_synthesis_bridge.json"
    out.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
