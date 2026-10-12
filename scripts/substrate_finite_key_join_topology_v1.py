#!/usr/bin/env python3
"""Measure finite-key closure across positive-join arity and graph topology."""
from __future__ import annotations

import hashlib
import json
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/mint_termination_join_topology_v1_20260926.json"
ARITIES = (1, 2, 3)
PATH_CYCLE_SIZES = (32, 64, 128, 256, 512)
LAYERED_SIZES = (16, 32, 64, 128)
REPEATS = 5
SCHEDULE_SEED = 1702
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_mint_termination_fragment import analyze  # noqa: E402
from substrate_rs import _native  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def graph_spec(topology: str, n: int) -> tuple[list[str], list[tuple[int, int]]]:
    if topology == "path":
        return [f"n{i}" for i in range(n)], [(i, i + 1) for i in range(n - 1)]
    if topology == "cycle":
        return [f"n{i}" for i in range(n)], [(i, (i + 1) % n) for i in range(n)]
    if topology == "layered":
        if n < 4 or (n - 2) % 2:
            raise ValueError(f"invalid layered node count {n}")
        s = (n - 2) // 2
        sizes = [1, s, s, 1]
        offsets, cur = [], 0
        for size in sizes:
            offsets.append(cur)
            cur += size
        edges = []
        for layer in range(3):
            for i in range(sizes[layer]):
                for j in range(sizes[layer + 1]):
                    edges.append((offsets[layer] + i, offsets[layer + 1] + j))
        return [f"n{i}" for i in range(n)], edges
    raise ValueError(topology)


def rule_for(q: int) -> dict:
    match = [[f"x{i}", "link", f"x{i+1}"] for i in range(q)]
    return {"name": f"q{q}_mint", "match": match,
            "effects": [["add_node_if_absent", "w", "Witness", {"tag": "w"}],
                        ["add_edge", f"x{q}", "result", "w", {}]]}


def enumerate_paths(n: int, edges: list[tuple[int, int]], q: int) -> tuple[int, list[int]]:
    adjacency = [[] for _ in range(n)]
    for src, tgt in edges:
        adjacency[src].append(tgt)
    count, endpoints = 0, set()
    def extend(node: int, remaining: int) -> None:
        nonlocal count
        if remaining == 0:
            count += 1
            endpoints.add(node)
            return
        for nxt in adjacency[node]:
            extend(nxt, remaining - 1)
    for start in range(n):
        extend(start, q)
    return count, sorted(endpoints)


def run_case(topology: str, n: int, q: int, replicate: int, warmup: bool = False) -> dict:
    node_names, input_edges = graph_spec(topology, n)
    rule = rule_for(q)
    match_count, terminal_nodes = enumerate_paths(n, input_edges, q)
    classified = analyze([rule], node_names,
                         [[f"n{i}", "link", f"n{j}", {}] for i, j in input_edges])
    if not classified["accepted"]:
        raise RuntimeError(classified["reasons"])

    t0 = time.perf_counter_ns()
    sub = _native.Substrate()
    engine_init_ns = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    node_ids = [sub.add_node("Seed", {"idx": i}) for i in range(n)]
    for i, j in input_edges:
        sub.add_edge_unchecked(node_ids[i], "link", node_ids[j])
    sub.add_rule(rule)
    setup_ns = time.perf_counter_ns() - t0
    budget = classified["progress_steps_upper_bound"] + 1
    t0 = time.perf_counter_ns()
    report = sub.run_rules_report(budget, False)
    closure_ns = time.perf_counter_ns() - t0
    graph = sub.graph_to_dict()

    nodes = {(x["type"], json.dumps(x["attrs"], sort_keys=True, separators=(",", ":")))
             for x in graph["nodes"]}
    expected_nodes = {
        *(('Seed', json.dumps({"idx": i}, sort_keys=True, separators=(",", ":"))) for i in range(n)),
        ('Witness', json.dumps({"tag": "w"}, sort_keys=True, separators=(",", ":"))),
    }
    edges = {(e["src"], e["type"], e["tgt"], json.dumps(e["attrs"], sort_keys=True, separators=(",", ":")))
             for e in graph["edges"]}
    expected_edges = {(node_ids[i], "link", node_ids[j], "{}") for i, j in input_edges}
    witness_id = next(x["id"] for x in graph["nodes"] if x["type"] == "Witness")
    expected_edges |= {(node_ids[i], "result", witness_id, "{}") for i in terminal_nodes}

    labels = {x["id"]: (x["type"], tuple(sorted(x["attrs"].items()))) for x in graph["nodes"]}
    projection = {"nodes": sorted((x["type"], tuple(sorted(x["attrs"].items()))) for x in graph["nodes"]),
                  "edges": sorted((labels[e["src"]], e["type"], labels[e["tgt"]],
                                   tuple(sorted(e["attrs"].items()))) for e in graph["edges"])}
    checks = {
        "analyzer_accepts": classified["accepted"],
        "native_fixed_point": report["status"] == "fixed_point",
        "no_budget_overshoot": report["budget_overshoot"] == 0,
        "exact_node_set": nodes == expected_nodes,
        "exact_edge_set": edges == expected_edges,
        "progress_within_bound": report["progress_steps"] <= classified["progress_steps_upper_bound"],
        "enumerated_match_count_positive": match_count > 0,
    }
    return {
        "case_id": f"{topology}_n{n}_q{q}_r{replicate}", "topology": topology,
        "n_initial_nodes": n, "n_initial_edges": len(input_edges), "match_arity": q,
        "enumerated_match_bindings": match_count, "distinct_terminal_nodes": len(terminal_nodes),
        "replicate": replicate, "warmup_discarded": warmup,
        "engine_init_ns": engine_init_ns, "setup_ns": setup_ns, "closure_ns": closure_ns,
        "native_report": report, "progress_bound": classified["progress_steps_upper_bound"],
        "actual_node_count": len(graph["nodes"]), "actual_edge_count": len(graph["edges"]),
        "actual_graph_projection_sha256": json_sha(projection),
        "checks": checks, "all_checks_pass": all(checks.values()),
    }


def main() -> int:
    configs = [(top, n, q) for top, sizes in (("path", PATH_CYCLE_SIZES), ("cycle", PATH_CYCLE_SIZES),
                                                   ("layered", LAYERED_SIZES))
               for n in sizes for q in ARITIES]
    warmups = [run_case(*c, replicate=0, warmup=True) for c in configs]
    schedule = [(top, n, q, r) for top, n, q in configs for r in range(1, REPEATS + 1)]
    random.Random(SCHEDULE_SEED).shuffle(schedule)
    cases = [run_case(*c) for c in schedule]
    native_path = Path(_native.__file__).resolve()
    hash_paths = [Path(__file__).resolve(), ROOT / "scripts/analyze_mint_termination_fragment.py",
                  ROOT / "runners/dsl/src/rewrite.rs", ROOT / "runners/dsl/src/graph.rs",
                  ROOT / "docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_JOIN_TOPOLOGY_PREREG_20260926.md"]
    payload = {
        "schema_version": 1, "run_id": "mint-termination-join-topology-v1-20260926",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version, "platform": platform.platform(),
        "provenance": {"source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in hash_paths},
                       "native_path": str(native_path), "native_sha256": sha(native_path)},
        "design": {"arities": list(ARITIES), "path_cycle_sizes": list(PATH_CYCLE_SIZES),
                   "layered_sizes": list(LAYERED_SIZES), "repeats": REPEATS,
                   "warmups_per_cell": 1, "schedule_seed": SCHEDULE_SEED,
                   "configuration_count": len(configs), "case_count": len(cases),
                   "claim_limit": "one fixed finite-key mint/effect schema; authored path/cycle/layered topologies"},
        "warmups": warmups, "cases": cases,
        "failed_cases": [x["case_id"] for x in cases if not x["all_checks_pass"]],
        "all_checks_pass": all(x["all_checks_pass"] for x in cases),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": payload["all_checks_pass"], "configurations": len(configs),
                      "cases": len(cases), "failed_cases": payload["failed_cases"], "output": str(OUT)}, indent=2))
    return 0 if payload["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
