#!/usr/bin/env python3
"""Measure current-source exact/min-fill graph-width analysis cost.

Synthetic, deterministic, undirected graph families only. This measures the
cost of deciding an inference/decomposition envelope, not solver quality or
natural-task locality. No Rust build or external I/O is used.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/graph_treewidth_cost_envelope_20260925.json"
EXACT_SIZES = (8, 9, 10)
EXACT_FAMILIES = ("path", "banded2", "complete", "sparse_random")
MIN_FILL_GRID = {
    "path": (32, 64, 128, 256, 512),
    "banded2": (32, 64, 128, 256, 512),
    "sparse_random": (32, 64, 128, 256, 512),
    "complete": (32, 48, 64, 80),
}
EXACT_REPEATS = 3
MIN_FILL_REPEATS = 5


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graph(n: int, family: str) -> tuple[list[int], list[tuple[int, int]]]:
    nodes = list(range(n))
    if family == "path":
        edges = [(i, i + 1) for i in range(n - 1)]
    elif family == "banded2":
        edges = [(i, j) for i in range(n) for j in range(i + 1, n) if j - i <= 2]
    elif family == "complete":
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    elif family == "sparse_random":
        rng = random.Random(1701 + n)
        p = min(1.0, 3.0 / max(n - 1, 1))
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)
                 if rng.random() < p]
    else:
        raise ValueError(f"unknown family {family}")
    return nodes, edges


def independent_order_width(nodes: list[int], edges: list[tuple[int, int]],
                             order: list[int]) -> int:
    if len(order) != len(nodes) or set(order) != set(nodes):
        raise AssertionError("returned elimination order is not a node permutation")
    adj = {n: set() for n in nodes}
    for a, b in edges:
        if a != b:
            adj[a].add(b)
            adj[b].add(a)
    width = 0
    for v in order:
        nbrs = set(adj[v])
        width = max(width, len(nbrs))
        for a in nbrs:
            for b in nbrs:
                if a != b:
                    adj[a].add(b)
            adj[a].discard(v)
        del adj[v]
    return width


def summarize(rows: list[dict], kind: str) -> list[dict]:
    out = []
    keys = sorted({(r["family"], r["nodes"]) for r in rows if r["kind"] == kind})
    for family, n in keys:
        group = [r for r in rows if r["kind"] == kind and r["family"] == family and r["nodes"] == n]
        wall = [r["wall_time_ns"] for r in group]
        cpu = [r["cpu_time_ns"] for r in group]
        widths = sorted({r["reported_width"] for r in group})
        out.append({"family": family, "nodes": n, "repeats": len(group),
                    "edges": group[0]["edges"], "widths_observed": widths,
                    "median_wall_ns": int(statistics.median(wall)),
                    "max_wall_ns": max(wall),
                    "median_cpu_ns": int(statistics.median(cpu))})
    return out


def main() -> None:
    from domains.graph_treewidth import exact_treewidth, min_fill_upper_bound

    rows = []
    for n in EXACT_SIZES:
        for family in EXACT_FAMILIES:
            nodes, edges = graph(n, family)
            for rep in range(EXACT_REPEATS):
                wall0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
                result = exact_treewidth(nodes, edges, max_exact_n=10)
                cpu_ns = time.process_time_ns() - cpu0
                wall_ns = time.perf_counter_ns() - wall0
                if result is None:
                    raise AssertionError("exact path unexpectedly refused within cap")
                check = independent_order_width(nodes, edges, result["elimination_order"])
                if check != result["treewidth"] or result["exact"] is not True:
                    raise AssertionError("exact treewidth/order mismatch")
                rows.append({"kind": "exact", "family": family, "nodes": n,
                             "edges": len(edges), "repeat": rep,
                             "wall_time_ns": wall_ns, "cpu_time_ns": cpu_ns,
                             "reported_width": result["treewidth"],
                             "independent_order_width": check,
                             "order_valid": True, "exact": True})
            upper = min_fill_upper_bound(nodes, edges)
            if upper["treewidth"] < rows[-1]["reported_width"]:
                raise AssertionError("min-fill width is below exact treewidth")

    for family, sizes in MIN_FILL_GRID.items():
        for n in sizes:
            nodes, edges = graph(n, family)
            for rep in range(MIN_FILL_REPEATS):
                wall0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
                result = min_fill_upper_bound(nodes, edges)
                cpu_ns = time.process_time_ns() - cpu0
                wall_ns = time.perf_counter_ns() - wall0
                check = independent_order_width(nodes, edges, result["elimination_order"])
                if check != result["treewidth"] or result["exact"] is not False:
                    raise AssertionError("min-fill width/order mismatch")
                rows.append({"kind": "min_fill", "family": family, "nodes": n,
                             "edges": len(edges), "repeat": rep,
                             "wall_time_ns": wall_ns, "cpu_time_ns": cpu_ns,
                             "reported_width": result["treewidth"],
                             "independent_order_width": check,
                             "order_valid": True, "exact": False})

    payload = {
        "schema_version": 1,
        "run_id": "graph-treewidth-cost-envelope-20260925",
        "method": "repeat exact permutation search through n=10 and min-fill heuristic on fixed synthetic families; independently recompute each returned ordering's induced width",
        "claim_boundary": "Algorithm cost on synthetic undirected graphs only; not inference runtime/quality, natural task locality, or a broad asymptotic guarantee.",
        "configuration": {"exact_sizes": EXACT_SIZES, "exact_families": EXACT_FAMILIES,
                          "exact_repeats": EXACT_REPEATS, "min_fill_grid": MIN_FILL_GRID,
                          "min_fill_repeats": MIN_FILL_REPEATS,
                          "random_edge_probability": "min(1,3/(n-1)); seed=1701+n"},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor(), "logical_cpus": os.cpu_count()},
        "provenance": {
            "script_sha256": sha(Path(__file__).resolve()),
            "graph_treewidth_sha256": sha(ROOT / "domains/graph_treewidth.py"),
        },
        "checks": {"all_orders_independently_recomputed": all(r["order_valid"] for r in rows),
                   "all_exact_widths_reconcile": all(r["reported_width"] == r["independent_order_width"]
                                                      for r in rows if r["kind"] == "exact"),
                   "all_min_fill_widths_reconcile": all(r["reported_width"] == r["independent_order_width"]
                                                         for r in rows if r["kind"] == "min_fill")},
        "summaries": {"exact": summarize(rows, "exact"),
                      "min_fill": summarize(rows, "min_fill")},
        "runs": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"exact_runs": sum(r["kind"] == "exact" for r in rows),
                      "min_fill_runs": sum(r["kind"] == "min_fill" for r in rows),
                      "checks": payload["checks"], "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
