#!/usr/bin/env python3
"""Capture native closure for mixed positive rule bodies and edge types."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/mint_termination_interaction_v1_20260926.json"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_CLOSURE_RULE_INTERACTION_PREREG_20260926.md"
RUNNER = Path(__file__).resolve()
from substrate_rs import _native


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rules() -> dict[str, dict]:
    return {
        "A": {"name": "mint_A", "match": [["x", "link", "y"]], "effects": [
            ["add_node_if_absent", "a", "Witness", {"tag": "A"}],
            ["add_edge", "x", "made_a", "a", {}]]},
        "B": {"name": "mint_B", "match": [["x", "link", "y"], ["y", "rel", "z"]], "effects": [
            ["add_node_if_absent", "b", "Witness", {"tag": "B"}],
            ["add_edge", "x", "made_b", "b", {}]]},
        "C": {"name": "join_AB", "match": [["x", "made_a", "a"], ["x", "made_b", "b"]], "effects": [
            ["add_node_if_absent", "c", "Witness", {"tag": "C"}],
            ["add_edge", "a", "result", "c", {}],
            ["add_edge", "b", "result", "c", {}]]},
    }


def input_edges(n: int, topology: str) -> list[tuple[str, int, int]]:
    pairs = ([(i, (i + 1) % n) for i in range(n)] if topology == "cycle"
             else [(i, i + 1) for i in range(n - 1)])
    return [(edge_type, src, tgt) for edge_type in ("link", "rel") for src, tgt in pairs]


def one_case(n: int, topology: str, order: str, replicate: int) -> dict:
    edges0 = input_edges(n, topology)
    rules_by_name = rules()
    rule_specs = [rules_by_name[key] for key in order]
    initial_node_ids = [f"n{i}" for i in range(n)]
    initial_edges = [[f"n{s}", t, f"n{d}", {}] for t, s, d in edges0]

    sub = _native.Substrate()
    ids = [sub.add_node("Seed", {"idx": i}) for i in range(n)]
    for t, s, d in edges0:
        sub.add_edge_unchecked(ids[s], t, ids[d])
    for rule in rule_specs:
        sub.add_rule(rule)
    report = sub.run_rules_report(200000, False)
    graph = sub.graph_to_dict()

    return {
        "case_id": f"n{n}_{topology}_{order}_r{replicate}",
        "n_initial_nodes": n, "topology": topology, "rule_order": order,
        "replicate": replicate, "initial_node_ids": initial_node_ids,
        "initial_edges": initial_edges, "rule_specs": rule_specs,
        "native_report": report, "native_graph": graph,
    }


def main() -> int:
    cases = [one_case(n, topology, order, rep)
             for n in (4, 8) for topology in ("cycle", "line")
             for order in ("ABC", "CBA", "BCA") for rep in (1, 2, 3)]
    native_path = Path(_native.__file__).resolve()
    out = {
        "schema_version": 1,
        "run_id": "mint-termination-interaction-v1-20260926",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "engine": provenance_line(), "python": sys.version, "platform": platform.platform(),
        "provenance": {"runner_sha256": sha(RUNNER), "prereg_sha256": sha(PREREG),
                       "native_sha256": sha(native_path), "native_path": str(native_path)},
        "design": {"N": [4, 8], "topologies": ["cycle", "line"],
                   "rule_orders": ["ABC", "CBA", "BCA"], "replicates": 3,
                   "budget": 200000, "cases": len(cases),
                   "rule_effect_edge_types": ["made_a", "made_b", "result"],
                   "claim_limit": "one three-rule positive schema, no deletion/updates/external state"},
        "cases": cases,
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"run_id": out["run_id"], "cases": len(cases),
                      "output": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
