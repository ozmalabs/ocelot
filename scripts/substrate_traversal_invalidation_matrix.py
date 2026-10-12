#!/usr/bin/env python3
"""Runtime wakeup matrix for graph-traversal terms and dynamic edge reads."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_traversal_invalidation_matrix_20260924.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def var(name: str) -> dict:
    return {"type": "Var", "name": name}


def term(kind: str, **fields) -> dict:
    return {"type": kind, **fields}


def make_case(name: str, read_term: dict, oracle_kind: str,
              any_type_read: bool = False, edge_attr_case: bool = False) -> dict:
    from substrate_rs import Substrate, _native

    s = Substrate()
    source = s.add_node("WakeupRoot", {})
    target = s.add_node("WakeupTarget", {})
    s.add_edge_unchecked(source, "trigger", target)
    if edge_attr_case:
        old_target = s.add_node("WakeupTarget", {})
        s.add_edge_unchecked(source, "causal", old_target, {"weight": 0})

    reader_idx = s._inner.add_rule({
        "name": f"traversal_matrix_{name}_reader",
        "match": [["x", "trigger", "y"]],
        "effects": [["set_attr", "y", "observed_value", {"__term__": read_term}]],
    })
    writer_effect = ["add_edge", "x", "causal", "y"]
    if edge_attr_case:
        writer_effect.append({"weight": 1})
    writer_idx = s._inner.add_rule({
        "name": f"traversal_matrix_{name}_writer",
        "match": [["x", "trigger", "y"]],
        "effects": [writer_effect],
    })

    access = s._inner.rule_access_sets()
    reader_access = next(row for row in access if row[0] == reader_idx)
    writer_access = next(row for row in access if row[0] == writer_idx)
    progress = s._inner.run_rules(100)
    observed = s.node(target)["attrs"].get("observed_value")
    probe_progress = s._inner.run_rules(1)
    graph = s._inner.graph_to_dict()
    source_id = source.value
    target_id = target.value
    causal_edges = [e for e in graph["edges"] if e["type"] == "causal"]

    if oracle_kind == "outgoing_causal_count":
        oracle = sum(e["src"] == source_id for e in causal_edges)
    elif oracle_kind == "incoming_causal_count":
        oracle = sum(e["tgt"] == target_id for e in causal_edges)
    elif oracle_kind == "reachable_causal_count":
        adjacency: dict[int, set[int]] = {}
        for e in causal_edges:
            adjacency.setdefault(e["src"], set()).add(e["tgt"])
        reached: set[int] = set()
        stack = list(adjacency.get(source_id, set()))
        while stack:
            node_id = stack.pop()
            if node_id not in reached:
                reached.add(node_id)
                stack.extend(adjacency.get(node_id, set()) - reached)
        oracle = len(reached)
    elif oracle_kind == "all_outgoing_edge_count":
        oracle = sum(e["src"] == source_id for e in graph["edges"])
    elif oracle_kind == "mapped_causal_neighbor_count":
        roots = {n["id"] for n in graph["nodes"] if n["type"] == "WakeupRoot"}
        oracle = len({e["tgt"] for e in causal_edges if e["src"] in roots})
    elif oracle_kind == "causal_edge_weight_sum":
        oracle = sum(e["attrs"].get("weight", 0) for e in causal_edges
                     if e["src"] == source_id)
    else:
        raise ValueError(f"unknown oracle kind: {oracle_kind}")

    return {
        "case": name,
        "oracle_kind": oracle_kind,
        "reader_rule": reader_access[1],
        "writer_rule": writer_access[1],
        "reader_read_set": reader_access[3],
        "reader_term_edge_reads": reader_access[4],
        "reader_reads_any": reader_access[6],
        "writer_write_set": writer_access[5],
        "progress_count": progress,
        "terminal_probe_progress": probe_progress,
        "final_observed_value": observed,
        "independent_graph_oracle": oracle,
        "final_causal_edge_count": len(causal_edges),
        "settled_correctly": observed == oracle and probe_progress == 0,
        "rule_access_sets": [list(row) for row in access],
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "any_type_read_requested": any_type_read,
        "edge_attr_read_case": edge_attr_case,
    }


def main() -> None:
    from substrate_rs import _native

    x, y = var("x"), var("y")
    causal_edges = lambda node: term("Edges", node=node, edge_type="causal")
    matrix = [
        ("edges_typed", term("Count", source=causal_edges(x)), "outgoing_causal_count", False, False),
        ("neighbours_typed", term("Count", source=term("Neighbours", node=x, edge_type="causal")), "outgoing_causal_count", False, False),
        ("in_neighbours_typed", term("Count", source=term("InNeighbours", node=y, edge_type="causal")), "incoming_causal_count", False, False),
        ("reachable_from_typed", term("Count", source=term("ReachableFrom", node=x, edge_type="causal")), "reachable_causal_count", False, False),
        ("map_neighbours_typed", term("Count", source=term(
            "MapNeighbours", source=term("NodesOfType", node_type="WakeupRoot"), edge_type="causal")), "mapped_causal_neighbor_count", False, False),
        ("edges_any_type", term("Count", source=term("Edges", node=x, edge_type=None)), "all_outgoing_edge_count", True, False),
        ("edge_attr_sum", term("Sum", source=causal_edges(x), var_name="edge",
            value=term("EdgeAttr", edge=var("edge"), key="weight")), "causal_edge_weight_sum", False, True),
    ]
    cases = [make_case(name, query, oracle, any_type, edge_attr)
             for name, query, oracle, any_type, edge_attr in matrix]
    extension_path = Path(_native.__file__).resolve()
    result = {
        "run_state": "exploratory_runtime_term_matrix",
        "protocol": "typed traversal invalidation matrix v1",
        "command": "PYTHONPATH=<fresh-native-package>:. python3 scripts/substrate_traversal_invalidation_matrix.py",
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip() != "",
        "python": sys.version,
        "platform": platform.platform(),
        "native_extension_path": str(extension_path),
        "native_extension_sha256": sha(extension_path),
        "source_sha256": {
            "harness": sha(Path(__file__)),
            "rewrite": sha(ROOT / "runners/dsl/src/rewrite.rs"),
            "substrate": sha(ROOT / "runners/dsl/src/substrate.rs"),
            "binding": sha(ROOT / "runners/dsl/src/py.rs"),
        },
        "workload": {
            "rules_per_case": 2,
            "graph": "two roots/targets, stable trigger binding, writer adds one causal edge; edge-attribute case has a separate zero-weight causal edge",
            "reference": "direct final graph edge count, reachability, mapped-neighbour set, or edge-attribute sum from graph_to_dict",
        },
        "cases": cases,
        "all_settled_correctly": all(c["settled_correctly"] for c in cases),
        "claim_boundary": [
            "Seven deterministic two-rule insertion cases; one process/run per case.",
            "Direct graph snapshots provide the answer oracle; every case has a terminal no-work probe.",
            "This does not cover deletions for every term, external mutation entrypoints, parallel runners, or broader task-level effects.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT.relative_to(ROOT)),
        "all_settled_correctly": result["all_settled_correctly"],
        "cases": [{k: c[k] for k in ("case", "reader_reads_any", "final_observed_value",
                                      "independent_graph_oracle", "settled_correctly")}
                  for c in cases],
    }, indent=2))
    if not result["all_settled_correctly"]:
        raise SystemExit("a traversal invalidation case failed its independent graph oracle or settle probe")


if __name__ == "__main__":
    main()
