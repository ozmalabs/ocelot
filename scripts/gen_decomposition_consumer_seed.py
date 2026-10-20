#!/usr/bin/env python3
"""Author the decomposition_consumer seed (P1.A2).

Consumes `Impasse -needs_decomposition-> CapabilityAxis` edges produced by
`order3_reframe` (`impasse_escalation`) by partitioning the parent axis across
its `requires_key` CapKeys into distinct subskill child CapabilityAxis nodes.
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
    L,
    Lte,
    N,
    Not,
    ONE,
    Plus,
    T,
    V,
    ZERO,
    numeric,
)


def Exists(source, var_name, predicate):
    return {
        "type": "Exists",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def Sum(source, var_name, value):
    return {
        "type": "Sum",
        "source": source,
        "var_name": var_name,
        "value": value,
    }


def Div(a, b):
    return {
        "type": "Div",
        "a": a,
        "b": b,
    }


def Vec(*items):
    return {
        "type": "Vec",
        "items": list(items),
    }


def policy_enabled():
    return Eq(numeric("pol", "enabled"), ONE)


def mint_child_per_key_rule():
    return {
        "name": "dc_mint_child_per_key",
        "batch": False,
        "comment": (
            "Partition a multi-key CapabilityAxis under needs_decomposition into one "
            "subskill child axis per required CapKey, each with distinct capability_keys."
        ),
        "match": [
            ["agent", "has_decomposition_consumer_policy", "pol"],
            ["mi", "needs_decomposition", "ax"],
            ["ax", "requires_key", "k"],
        ],
        "where": And(
            policy_enabled(),
            Not(Eq(numeric("mi", "dc_handled"), ONE)),
            Gt(Count(N("ax", "requires_key")), ONE),
            Not(Exists(
                N("ax", "decomposes_into"),
                "c",
                Eq(A("c", "decomposed_key"), A("k", "name")),
            )),
        ),
        "effects": [
            ["add_node", "child", "CapabilityAxis", {
                "is_axis": 1.0,
                "subskill": 1.0,
                "saturation": 0.0,
                "shortfall": T(A("pol", "child_shortfall")),
                "mf_stall": 0,
                "decomposed_key": T(A("k", "name")),
                "parent_axis_ref": T(V("ax")),
                "capability_keys": T(Vec(A("k", "name"))),
            }],
            ["add_edge", "ax", "decomposes_into", "child"],
            ["add_edge", "child", "requires_key", "k"],
        ],
    }


def inherit_operator_rule():
    return {
        "name": "dc_inherit_operator",
        "batch": False,
        "comment": "Bind newly partitioned subskill child axes to the parent axis's current operator when present.",
        "match": [
            ["agent", "has_decomposition_consumer_policy", "pol"],
            ["ax", "decomposes_into", "child"],
            ["ax", "investigated_by", "op"],
        ],
        "where": And(
            policy_enabled(),
            Eq(Count(N("child", "investigated_by")), ZERO),
        ),
        "effects": [
            ["add_edge", "child", "investigated_by", "op"],
        ],
    }


def mark_handled_rule():
    missing_key = Exists(
        N("ax", "requires_key"),
        "k",
        Not(Exists(
            N("ax", "decomposes_into"),
            "c",
            Eq(A("c", "decomposed_key"), A("k", "name")),
        )),
    )
    return {
        "name": "dc_mark_handled",
        "batch": False,
        "comment": "Record partitioned outcome once every required CapKey of the parent axis has a child axis.",
        "match": [
            ["agent", "has_decomposition_consumer_policy", "pol"],
            ["mi", "needs_decomposition", "ax"],
        ],
        "where": And(
            policy_enabled(),
            Not(Eq(numeric("mi", "dc_handled"), ONE)),
            Gt(Count(N("ax", "requires_key")), ONE),
            Not(missing_key),
        ),
        "effects": [
            ["set_attr", "mi", "dc_handled", 1],
            ["set_attr", "mi", "dc_outcome", "partitioned"],
        ],
    }


def no_partition_rule():
    return {
        "name": "dc_no_partition",
        "batch": False,
        "comment": "Record honest no_partition outcome when the axis has at most one CapKey to decompose.",
        "match": [
            ["agent", "has_decomposition_consumer_policy", "pol"],
            ["mi", "needs_decomposition", "ax"],
        ],
        "where": And(
            policy_enabled(),
            Not(Eq(numeric("mi", "dc_handled"), ONE)),
            Lte(Count(N("ax", "requires_key")), ONE),
        ),
        "effects": [
            ["set_attr", "mi", "dc_handled", 1],
            ["set_attr", "mi", "dc_outcome", "no_partition"],
        ],
    }


def parent_progress_from_children_rule():
    children = N("ax", "decomposes_into")
    mean_saturation = Div(
        Sum(children, "c", Plus(A("c", "saturation"), L(0.0))),
        Count(children),
    )
    return {
        "name": "dc_parent_progress_from_children",
        "batch": False,
        "comment": "Aggregate child axis saturations into child_mean_saturation on the parent axis.",
        "match": [
            ["agent", "has_decomposition_consumer_policy", "pol"],
            ["ax", "decomposes_into", "child"],
        ],
        "where": And(
            policy_enabled(),
            Gt(Count(children), ZERO),
            Not(Eq(A("ax", "child_mean_saturation"), mean_saturation)),
        ),
        "effects": [
            ["set_attr", "ax", "child_mean_saturation", T(mean_saturation)],
        ],
    }


def productions():
    specs = [
        ("Agent", "has_decomposition_consumer_policy", "DecompositionConsumerPolicy"),
        ("Impasse", "needs_decomposition", "CapabilityAxis"),
        ("CapabilityAxis", "requires_key", "CapKey"),
        ("CapabilityAxis", "decomposes_into", "CapabilityAxis"),
        ("CapabilityAxis", "investigated_by", "Operator"),
    ]
    return [
        {
            "provenance": f"seed:decomposition_consumer:{edge_type}",
            "src": {"type": src, "var": "src"},
            "edge_type": edge_type,
            "tgt": {"type": tgt, "var": "tgt"},
        }
        for src, edge_type, tgt in specs
    ]


def build():
    return {
        "id": "decomposition_consumer",
        "version": "1.0.0",
        "depends_on": [],
        "description": (
            "Opt-in consumer for Impasse -needs_decomposition-> CapabilityAxis edges "
            "minted by order3_reframe. Partitions a multi-key parent axis across its "
            "requires_key CapKeys into distinct subskill child axes and tracks their "
            "mean saturation."
        ),
        "microtheory": {
            "name": "decomposition_consumer",
            "description": (
                "Partition an order-3 reframed CapabilityAxis into one subskill child "
                "axis per required CapKey without duplicating the parent's capability_keys."
            ),
        },
        "nodes": [
            {
                "local_id": 0,
                "type": "DecompositionConsumerPolicy",
                "attrs": {
                    "enabled": 0.0,
                    "child_shortfall": 0.6,
                },
            },
        ],
        "edges": [
            {
                "src": {"role": "agent_root"},
                "type": "has_decomposition_consumer_policy",
                "tgt": {"local": 0},
                "attrs": {},
            },
        ],
        "productions": productions(),
        "rules": [
            mint_child_per_key_rule(),
            inherit_operator_rule(),
            mark_handled_rule(),
            no_partition_rule(),
            parent_progress_from_children_rule(),
        ],
    }


def main():
    out = ROOT / "seeds" / "decomposition_consumer.json"
    out.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
