#!/usr/bin/env python3
"""Author the `invention_operators` seed (Track I, I2.1).

Invention operators are DATA: one `InventionOperator` node per operator,
holding its expression template over the process-algebra Terms, its arity
and its cost formula. The rules that apply an operator live in
`invention_round` (one rule family per operator, because a rule cannot
evaluate a template held as data). Yields and trials are recorded per
(domain kind, operator) on `StrategyRecord` nodes by `invention_round`
(I3.3), which is what lets yield-guided selection, and later I7.1
meta-invention, treat operators as countable, selectable objects.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import OFFLINE_AREA, productions  # noqa: E402

SEED_ID = "invention_operators"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"

OPERATORS = [
    ("inverse", "a⁻¹", 1, "cost(a)"),
    ("compose", "a · b", 2, "cost(a) + cost(b)"),
    ("conjugate", "b · a · b⁻¹", 2, "cost(a) + 2·cost(b)"),
    ("commutator", "a · b · a⁻¹ · b⁻¹", 2, "2·(cost(a) + cost(b))"),
    ("power2", "a · a", 1, "2·cost(a)"),
    ("power3", "a · a · a", 1, "3·cost(a)"),
    ("root2", "x such that x · x = a (search, records root_of)", 1, "cost(x)"),
]


def build():
    nodes = []
    edges = []
    for i, (name, template, arity, cost) in enumerate(OPERATORS):
        nodes.append({"local_id": i, "type": "InventionOperator", "attrs": {
            "name": name, "template": template, "arity": float(arity),
            "cost_formula": cost, "enabled": 1.0}})
        edges.append({"src": {"role": "agent_root"}, "type": "has_invention_operator",
                      "tgt": {"local": i}, "attrs": {}})
    return {
        "id": SEED_ID,
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "area": OFFLINE_AREA,
        "description": (
            "Track I I2.1: the invention operators (inverse, compose, conjugate, commutator, "
            "powers, square root) as countable, selectable graph data."
        ),
        "microtheory": {
            "name": SEED_ID,
            "description": "New processes are built from held ones by compose and inverse.",
        },
        "nodes": nodes,
        "edges": edges,
        "productions": productions(SEED_ID, [("Agent", "has_invention_operator", "InventionOperator")]),
        "rules": [],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
