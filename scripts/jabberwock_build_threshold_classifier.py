#!/usr/bin/env python3
"""Have the Jabberwock synthesize and verify a thresholded classifier.

The examples and held-out observations enter at the experiment boundary.
Operator selection, quantity authority, program construction, and acceptance
remain graph-native.  The emitted JSON is a read-back of the accepted graph
program and its measured synthesis provenance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from substrate.world_adapter import WorldAdapter  # noqa: E402
from domains import prog_synthesis as ps  # noqa: E402


DEFAULT_OUTPUT = ROOT / "results" / "jabberwock_threshold_classifier.json"

REQUEST = (
    "write a function cost_excess that returns micros when processed is "
    "more than threshold times progress otherwise zero"
)

EXAMPLES = [
    ({"processed": 100, "progress": 20, "micros": 300,
      "threshold": 10}, 0),
    ({"processed": 201, "progress": 20, "micros": 300,
      "threshold": 10}, 300),
    ({"processed": 61, "progress": 20, "micros": 7,
      "threshold": 3}, 7),
    ({"processed": 60, "progress": 20, "micros": 11,
      "threshold": 3}, 0),
]

HELD_OUT = [
    ({"processed": 501, "progress": 50, "micros": 19,
      "threshold": 10}, 19),
    ({"processed": 500, "progress": 50, "micros": 19,
      "threshold": 10}, 0),
    ({"processed": 9, "progress": 4, "micros": 23,
      "threshold": 2}, 23),
    ({"processed": 8, "progress": 4, "micros": 23,
      "threshold": 2}, 0),
    ({"processed": 1, "progress": 0, "micros": 31,
      "threshold": 100}, 31),
]


def _evaluate_program(agent, program, inputs):
    roots = agent.s.neighbours(program, "ir_subgraph")
    if len(roots) != 1:
        raise RuntimeError("accepted Program must have one reflected IR root")
    outcome = agent.inner.evaluate({
        "type": "ProgEval",
        "prog": {"type": "Var", "name": "program"},
        "env": {"type": "Var", "name": "inputs"},
        "oracles": None,
        "fuel": 10000,
        "field": "",
    }, {"program": roots[0], "inputs": inputs})
    if outcome.get("halted") is not True or outcome.get("trap") is not None:
        raise RuntimeError(f"accepted program trapped: {outcome!r}")
    return outcome.get("result")


def _assert_integer_artifact(value: Any, path=()) -> None:
    if isinstance(value, float):
        raise TypeError(f"float escaped into classifier artifact at {path}")
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_integer_artifact(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_integer_artifact(child, path + (index,))


def build_artifact() -> dict[str, Any]:
    agent = WorldAdapter(seeds=())
    ps.ensure_program_synthesis(agent.s, agent.inner, agent.agent)
    result = ps.synthesize_from_request(
        agent.s, agent.agent, REQUEST, EXAMPLES
    )
    if result["status"] != "accepted" or result["program"] is None:
        raise RuntimeError(f"Jabberwock did not build classifier: {result!r}")

    checks = []
    for inputs, expected in HELD_OUT:
        got = _evaluate_program(agent, result["program"], inputs)
        checks.append({
            "inputs": inputs,
            "expected": expected,
            "got": got,
            "passed": int(got == expected),
        })
    if not all(check["passed"] == 1 for check in checks):
        raise RuntimeError(f"held-out classifier failure: {checks!r}")

    enumeration = result["enumerate"]
    artifact = {
        "artifact": "jabberwock_threshold_classifier",
        "version": 1,
        "policy_owner": "rust_graph",
        "request": REQUEST,
        "examples": [
            {"inputs": inputs, "expected": expected}
            for inputs, expected in EXAMPLES
        ],
        "status": result["status"],
        "program_name": result["name"],
        "program_ir": result["ir"],
        "rendered_term": agent.s.node(result["goal"])["attrs"].get(
            "ps_enumerate_note"
        ),
        "synthesis": {
            "operator_shape": enumeration["operator_shape"],
            "ops": enumeration["ops"],
            "grounded_constants": enumeration["grounded_constants"],
            "tested_candidates": int(enumeration["tested"]),
            "distinct_behaviours": int(enumeration["distinct"]),
            "solution_size": int(enumeration["solution_size"]),
        },
        "held_out": checks,
        "held_out_pass_count": sum(check["passed"] for check in checks),
        "held_out_count": len(checks),
    }
    _assert_integer_artifact(artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    artifact = build_artifact()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "status": artifact["status"],
        "rendered_term": artifact["rendered_term"],
        "held_out": (
            f"{artifact['held_out_pass_count']}/{artifact['held_out_count']}"
        ),
        "tested_candidates": artifact["synthesis"]["tested_candidates"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
