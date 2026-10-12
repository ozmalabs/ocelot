#!/usr/bin/env python3
"""Measure verified-forest order dispatch with min-fill fallback on mixed topologies."""
from __future__ import annotations

import collections
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
OUT = ROOT / "evaluation/reports/can_guarded_forest_dispatch_20260925.json"
TREE_SIZES = (32, 64, 128, 256)
OTHER_SIZES = (32, 64, 128, 256)
CLIQUE_SIZES = (8, 12)
FAMILIES = ("path", "balanced_tree", "cycle", "ladder", "sparse_random", "clique")
REPLICATES = 3
VOCAB = (-1.0, 1.0)
MAP_WIDTH_GATE = 4


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_edges(family, n, seed):
    if family == "path":
        return [(i, i + 1) for i in range(n - 1)]
    if family == "balanced_tree":
        return [(i, (i - 1) // 2) for i in range(1, n)]
    if family == "cycle":
        return [(i, i + 1) for i in range(n - 1)] + [(n - 1, 0)]
    if family == "ladder":
        if n % 2:
            raise ValueError("ladder size must be even")
        half = n // 2
        return ([(i, i + 1) for i in range(half - 1)] +
                [(half + i, half + i + 1) for i in range(half - 1)] +
                [(i, half + i) for i in range(half)])
    if family == "sparse_random":
        rng = random.Random(seed)
        edges = {(i, i + 1) for i in range(n - 1)}
        # Add a bounded number of deterministic long-range edges.
        for _ in range(n // 2):
            a, b = rng.sample(range(n), 2)
            edges.add(tuple(sorted((a, b))))
        return sorted(edges)
    if family == "clique":
        return [(i, j) for i in range(n) for j in range(i + 1, n)]
    raise ValueError(family)


def is_forest(n, edges):
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        if a == b:
            return False
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
    return True


def forest_peo(n, edges):
    adj = [set() for _ in range(n)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    degree = [len(x) for x in adj]
    queue = collections.deque(i for i, d in enumerate(degree) if d <= 1)
    removed = [False] * n
    order = []
    while queue:
        v = queue.popleft()
        if removed[v]:
            continue
        removed[v] = True
        order.append(v)
        for u in adj[v]:
            if not removed[u]:
                degree[u] -= 1
                if degree[u] <= 1:
                    queue.append(u)
    if len(order) != n:
        raise ValueError("input is cyclic")
    return order


def worker(family, n, rep):
    import substrate_rs as sr
    import domains.can_junction_tree as cjt
    from domains.graph_treewidth import min_fill_upper_bound

    seed = 20260925 + n * 1009 + rep * 65537 + sum(map(ord, family))
    edges = make_edges(family, n, seed)
    rng = random.Random(seed ^ 0xC0FFEE)
    unary = {i: rng.randint(-8, 8) / 4.0 for i in range(n)}
    pairwise = {frozenset((i, j)): rng.randint(-8, 8) / 4.0 for i, j in edges}

    s = sr.Substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {"discrete_mode": "2state"})
    concepts = [inner.add_node("Concept", {
        "name": f"x{i}", "external_field": unary[i],
        "identity_field": 0.0, "state": 0.0,
    }) for i in range(n)]
    for node in concepts:
        inner.add_edge_unchecked(mt, "has_concept", node, {})
    for (i, j), weight in [(tuple(sorted(k)), v) for k, v in pairwise.items()]:
        inner.add_edge_unchecked(concepts[i], "causal_influence", concepts[j], {"weight": weight})
        inner.add_edge_unchecked(concepts[j], "causal_influence", concepts[i], {"weight": weight})
    net = cjt.can_network_from_mt(s, mt)
    local = {node.value: i for i, node in enumerate(concepts)}
    extracted_edges = sorted({tuple(sorted((local[a], local[b]))) for a, b in net["edges"]})
    extracted_pairwise = {
        frozenset(local[i] for i in pair): value for pair, value in net["pairwise"].items()
    }
    extracted_unary = {local[i]: value for i, value in net["unary"].items()}
    if extracted_edges != sorted(tuple(sorted(e)) for e in edges):
        raise AssertionError("extracted topology differs from generated topology")
    if extracted_pairwise != pairwise or extracted_unary != unary:
        raise AssertionError("extracted factor weights differ from generated model")

    t0 = time.perf_counter_ns()
    forest = is_forest(n, extracted_edges)
    detector_ns = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    minfill = min_fill_upper_bound(list(range(n)), extracted_edges)
    minfill_ns = time.perf_counter_ns() - t0
    if forest:
        t0 = time.perf_counter_ns()
        guarded_order = forest_peo(n, extracted_edges)
        leaf_ns = time.perf_counter_ns() - t0
    else:
        guarded_order = minfill["elimination_order"]
        leaf_ns = 0
    if forest and forest_peo(n, extracted_edges) != guarded_order:
        raise AssertionError("forest order changed across deterministic recomputation")
    guarded_width = (1 if extracted_edges else 0) if forest else minfill["treewidth"]
    # Exact MAP is invoked only when the same conservative width-4 gate admits the graph.
    admitted = minfill["treewidth"] <= MAP_WIDTH_GATE
    minfill_map_ns = guarded_map_ns = None
    exact_gap = None
    map_widths_agree = None
    if admitted:
        t0 = time.perf_counter_ns()
        a = cjt.junction_tree_map(list(range(n)), extracted_edges, unary, pairwise,
                                  VOCAB, order=minfill["elimination_order"])
        minfill_map_ns = time.perf_counter_ns() - t0
        t0 = time.perf_counter_ns()
        b = cjt.junction_tree_map(list(range(n)), extracted_edges, unary, pairwise,
                                  VOCAB, order=guarded_order)
        guarded_map_ns = time.perf_counter_ns() - t0
        exact_gap = a["energy"] - b["energy"]
        map_widths_agree = (a["max_bag_size"] == b["max_bag_size"])
        if abs(exact_gap) > 1e-9 or not map_widths_agree:
            raise AssertionError("guarded dispatch changed exact MAP result")
    elif forest:
        raise AssertionError("forest order should be admitted by width gate")

    return {
        "family": family, "nodes": n, "edges": len(extracted_edges),
        "replicate": rep, "seed": seed, "forest_detected": forest,
        "min_fill_width": minfill["treewidth"], "guarded_order_width": guarded_width,
        "min_fill_gate_admitted": admitted, "guarded_gate_admitted": guarded_width <= MAP_WIDTH_GATE,
        "exact_energy_gap": exact_gap, "map_bag_widths_agree": map_widths_agree,
        "timing_ns": {"forest_detector": detector_ns, "min_fill_order": minfill_ns,
                      "forest_order": leaf_ns,
                      "map_after_min_fill": minfill_map_ns, "map_after_guarded": guarded_map_ns},
    }


def main():
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), int(sys.argv[4])), sort_keys=True))
        return
    configs = []
    for fam in FAMILIES:
        sizes = CLIQUE_SIZES if fam == "clique" else (TREE_SIZES if fam in ("path", "balanced_tree") else OTHER_SIZES)
        configs.extend((fam, n, rep) for n in sizes for rep in range(REPLICATES))
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    runs = []
    for fam, n, rep in configs:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", fam, str(n), str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(proc.stdout.strip()))
        r = runs[-1]
        print(f"{fam} n={n} rep={rep} forest={r['forest_detected']} "
              f"width={r['min_fill_width']} exact={r['min_fill_gate_admitted']}", flush=True)
    summaries = []
    for fam in FAMILIES:
        for n in sorted({r["nodes"] for r in runs if r["family"] == fam}):
            group = [r for r in runs if r["family"] == fam and r["nodes"] == n]
            keys = group[0]["timing_ns"]
            med = {k: (None if group[0]["timing_ns"][k] is None else
                       int(statistics.median(r["timing_ns"][k] for r in group)))
                   for k in keys}
            summaries.append({
                "family": fam, "nodes": n, "edges": group[0]["edges"],
                "replicates": len(group), "forest_detection_rate":
                    sum(r["forest_detected"] for r in group) / len(group),
                "median_timing_ns": med,
                "min_fill_width": group[0]["min_fill_width"],
                "guarded_order_width": group[0]["guarded_order_width"],
                "exact_gate_admitted": group[0]["min_fill_gate_admitted"],
                "exact_map_passes": sum(r["exact_energy_gap"] is not None for r in group),
            })
    source_paths = [Path(__file__).resolve(), ROOT / "domains/can_junction_tree.py",
                    ROOT / "domains/graph_treewidth.py",
                    ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
                    ROOT / "runners/dsl/python/substrate_rs/_native.build.json"]
    payload = {
        "schema_version": 1, "run_id": "can-guarded-forest-dispatch-20260925-v1",
        "scope": "verified forest leaf order with min-fill fallback on mixed runtime-extracted CAN topologies",
        "claim_boundary": "Synthetic graph families only. DSU forest detection and fallback are benchmark code, not production dispatch. No natural-topology or general speedup claim.",
        "configuration": {"families": FAMILIES, "tree_sizes": TREE_SIZES,
                          "other_sizes": OTHER_SIZES, "clique_sizes": CLIQUE_SIZES,
                          "replicates": REPLICATES, "exact_width_gate": MAP_WIDTH_GATE},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor()},
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in source_paths},
        "checks": {
            "extracted_topologies_and_factors_exact": len(runs) == len(configs),
            "forest_positive_controls_detected": all(r["forest_detected"] for r in runs
                if r["family"] in ("path", "balanced_tree")),
            "cyclic_negative_controls_rejected": all(not r["forest_detected"] for r in runs
                if r["family"] in ("cycle", "ladder", "clique")),
            "guarded_gate_matches_min_fill_gate": all(r["guarded_gate_admitted"] == r["min_fill_gate_admitted"]
                                                       for r in runs),
            "all_admitted_exact_maps_match": all(r["exact_energy_gap"] is None or
                                                   abs(r["exact_energy_gap"]) <= 1e-9 for r in runs),
            "all_config_replicates_present": all(sum(r["family"] == f and r["nodes"] == n for r in runs) == REPLICATES
                for f, n, _ in configs[::REPLICATES]),
        },
        "summaries": summaries, "runs": runs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"runs": len(runs), "checks": payload["checks"], "output": str(OUT)}, indent=2))
    if not all(payload["checks"].values()):
        raise SystemExit("guarded dispatch invariant failed")


if __name__ == "__main__":
    main()
