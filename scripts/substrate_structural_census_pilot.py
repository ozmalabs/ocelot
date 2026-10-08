#!/usr/bin/env python3
"""Exploratory census of treewidth and hierarchical cut statistics.

No substrate execution or task semantics are inferred here. The script
compares a stable ID-contiguous recursive partition with seeded shuffled
partitions on controlled undirected projections of synthetic graph families.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_structural_census_pilot_20260924.json"
SIZES = (8, 16, 32, 64)
FAMILIES = ("path", "banded_dag", "complete_dag", "star", "modular_chain", "sparse_random")
LEAF_FRAME_MAX_NODES = 8
RANDOM_PARTITIONS = 5


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def make_edges(n: int, family: str, seed: int = 0) -> list[tuple[int, int]]:
    if family == "path":
        return [(i, i + 1) for i in range(n - 1)]
    if family == "banded_dag":
        return [(i, j) for i in range(n) for j in range(i + 1, min(n, i + 3))]
    if family == "complete_dag":
        return [(i, j) for i in range(n) for j in range(i + 1, n)]
    if family == "star":
        return [(0, i) for i in range(1, n)]
    if family == "modular_chain":
        edges: list[tuple[int, int]] = []
        for start in range(0, n, 4):
            stop = min(start + 4, n)
            edges.extend((i, j) for i in range(start, stop) for j in range(i + 1, stop))
            if stop < n:
                edges.extend(((stop - 1, stop), (max(start, stop - 2), stop)))
        return edges
    if family == "sparse_random":
        rng = random.Random(seed)
        probability = min(1.0, 3.0 / max(n - 1, 1))
        return [(i, j) for i in range(n) for j in range(i + 1, n)
                if rng.random() < probability]
    raise ValueError(f"unknown family: {family}")


def recursive_partition(nodes: list[int], edges: list[tuple[int, int]],
                        max_leaf_nodes: int) -> dict:
    node_set = set(nodes)
    adjacency = {u: set() for u in nodes}
    for u, v in edges:
        if u in node_set and v in node_set and u != v:
            adjacency[u].add(v)
            adjacency[v].add(u)
    frames: list[list[int]] = []
    cuts: list[dict] = []

    def split(group: list[int], depth: int) -> None:
        if len(group) <= max_leaf_nodes:
            frames.append(group)
            return
        midpoint = len(group) // 2
        left, right = group[:midpoint], group[midpoint:]
        left_set, right_set = set(left), set(right)
        crossing = [(u, v) for u in left for v in adjacency[u] if v in right_set]
        crossing.extend((u, v) for u in right for v in adjacency[u] if v in left_set)
        boundary = {v for edge in crossing for v in edge}
        cuts.append({
            "depth": depth,
            "left_nodes": len(left),
            "right_nodes": len(right),
            "crossing_edges": len(crossing) // 2,
            "boundary_vertices": len(boundary),
            "left_aperture": len(boundary & left_set),
            "right_aperture": len(boundary & right_set),
        })
        split(left, depth + 1)
        split(right, depth + 1)

    split(nodes, 0)
    node_to_frame = {node: i for i, frame in enumerate(frames) for node in frame}
    leaf_crossings = [[] for _ in frames]
    cross_frame_edges = 0
    for u, v in edges:
        fu, fv = node_to_frame[u], node_to_frame[v]
        if fu != fv:
            cross_frame_edges += 1
            leaf_crossings[fu].extend((u, v))
            leaf_crossings[fv].extend((u, v))
    leaf_apertures = []
    for frame_i, frame in enumerate(frames):
        frame_nodes = set(frame)
        aperture = set()
        for edge_u, edge_v in zip(leaf_crossings[frame_i][::2], leaf_crossings[frame_i][1::2]):
            if edge_u in frame_nodes:
                aperture.add(edge_u)
            if edge_v in frame_nodes:
                aperture.add(edge_v)
        leaf_apertures.append(len(aperture))

    max_depth = max((cut["depth"] + 1 for cut in cuts), default=0)
    depth_rows = []
    for depth in range(max_depth):
        rows = [cut for cut in cuts if cut["depth"] == depth]
        if rows:
            depth_rows.append({
                "depth": depth,
                "cut_count": len(rows),
                "crossing_edges_total": sum(row["crossing_edges"] for row in rows),
                "max_boundary_vertices": max(row["boundary_vertices"] for row in rows),
                "max_child_aperture": max(max(row["left_aperture"], row["right_aperture"])
                                           for row in rows),
            })
    return {
        "frame_count": len(frames),
        "frame_sizes": [len(frame) for frame in frames],
        "hierarchy_depth": max_depth,
        "leaf_aperture_vertices": leaf_apertures,
        "leaf_aperture_max": max(leaf_apertures, default=0),
        "leaf_aperture_median": statistics.median(leaf_apertures) if leaf_apertures else 0,
        "cross_frame_edge_count": cross_frame_edges,
        "cut_rows": cuts,
        "by_depth": depth_rows,
    }


def main() -> None:
    from domains.graph_treewidth import exact_treewidth, min_fill_upper_bound

    records = []
    for family in FAMILIES:
        for n in SIZES:
            edges = make_edges(n, family, seed=1701 + n)
            t0 = time.perf_counter_ns()
            exact = exact_treewidth(list(range(n)), edges, max_exact_n=10)
            exact_ns = time.perf_counter_ns() - t0 if exact is not None else None
            t0 = time.perf_counter_ns()
            upper = min_fill_upper_bound(list(range(n)), edges)
            min_fill_ns = time.perf_counter_ns() - t0
            t0 = time.perf_counter_ns()
            contiguous = recursive_partition(list(range(n)), edges, LEAF_FRAME_MAX_NODES)
            contiguous_ns = time.perf_counter_ns() - t0
            partitions = []
            partitions.append({
                "partition_id": "contiguous_node_id",
                "seed": None,
                "construction_time_ns": contiguous_ns,
                **contiguous,
            })
            for seed in range(RANDOM_PARTITIONS):
                permutation = list(range(n))
                random.Random(91000 + seed).shuffle(permutation)
                t0 = time.perf_counter_ns()
                partition = recursive_partition(permutation, edges, LEAF_FRAME_MAX_NODES)
                construction_ns = time.perf_counter_ns() - t0
                partitions.append({
                    "partition_id": f"shuffled_{seed}",
                    "seed": 91000 + seed,
                    "construction_time_ns": construction_ns,
                    **partition,
                })
            records.append({
                "family": family,
                "nodes": n,
                "edges": len(edges),
                "edge_density_undirected": (2 * len(edges) / (n * (n - 1))) if n > 1 else 0.0,
                "degree_max": max((sum(v in edge for edge in edges) for v in range(n)), default=0),
                "treewidth_exact": exact["treewidth"] if exact is not None else None,
                "treewidth_upper_bound": upper["treewidth"],
                "min_fill_upper_bound_is_exact": exact is not None,
                "exact_treewidth_time_ns": exact_ns,
                "min_fill_decomposition_time_ns": min_fill_ns,
                "partitions": partitions,
            })

    patch = subprocess.check_output(["git", "diff", "--binary"], cwd=ROOT)
    manifest = {
        "run_state": "pilot",
        "protocol": "synthetic hierarchical structural census v1; benchmark protocol 1.1",
        "command": "PYTHONPATH=. python3 scripts/substrate_structural_census_pilot.py",
        "commit": git("rev-parse", "HEAD"),
        "dirty": git("status", "--porcelain") != "",
        "tracked_patch_sha256": hashlib.sha256(patch).hexdigest(),
        "harness_sha256": sha(Path(__file__)),
        "protocol_sha256": sha(ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md"),
        "treewidth_source_sha256": sha(ROOT / "domains/graph_treewidth.py"),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
        },
        "definitions": {
            "graph_projection": "Undirected simple projection of each synthetic input graph; self-loops excluded.",
            "contiguous_partition": "Recursive balanced bisection of ascending node IDs until each leaf has at most 8 nodes.",
            "random_baseline": "Same recursive balanced bisection after seeded node permutation; five fixed seeds per input.",
            "cut_boundary": "Unique vertices incident to an edge crossing a hierarchy cut.",
            "leaf_aperture": "Unique vertices in a leaf frame incident to any edge joining a different leaf frame.",
            "treewidth": "Exact brute-force minimum induced width when n<=10; deterministic min-fill upper bound at larger n.",
        },
        "limits": [
            "Synthetic structures only; node IDs encode the contiguous partition for the canonical arm.",
            "No rule-semantic dependency analysis or partitioned execution is performed.",
            "No natural task snapshot census or confirmatory sampling frame is established.",
        ],
        "workload": {
            "families": list(FAMILIES),
            "sizes": list(SIZES),
            "max_leaf_nodes": LEAF_FRAME_MAX_NODES,
            "random_partitions_per_instance": RANDOM_PARTITIONS,
        },
        "records": records,
    }
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT.relative_to(ROOT)),
        "records": len(records),
        "partition_instances": sum(len(record["partitions"]) for record in records),
        "exact_treewidth_records": sum(record["treewidth_exact"] is not None for record in records),
    }, indent=2))


if __name__ == "__main__":
    main()
