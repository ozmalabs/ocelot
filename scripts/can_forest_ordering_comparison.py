#!/usr/bin/env python3
"""Paired exact MAP comparison: generic min-fill versus leaf elimination on paths."""
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
OUT = ROOT / "evaluation/reports/can_forest_ordering_comparison_20260925.json"
SIZES = (256, 512, 1024, 2048)
REPLICATES = 2
VOCAB = (-1.0, 1.0)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def forest_peo(n, edges):
    """Leaf stripping gives a perfect elimination order for a forest."""
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
        raise ValueError("leaf elimination requires a forest")
    seen = set()
    max_later = 0
    for v in reversed(order):
        later = adj[v] & seen
        max_later = max(max_later, len(later))
        if len(later) > 1:
            raise AssertionError("leaf order is not a perfect elimination order")
        seen.add(v)
    return order, max_later


def worker(n, rep):
    import substrate_rs as sr
    import domains.can_junction_tree as cjt
    from domains.graph_treewidth import min_fill_upper_bound
    from can_bounded_width_scale import make_model

    seed = 20260925 + n * 1009 + rep * 65537
    unary, pairwise = make_model(n, seed)
    s = sr.Substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {"discrete_mode": "2state"})
    concepts = [inner.add_node("Concept", {
        "name": f"x{i}", "external_field": unary[i],
        "identity_field": 0.0, "state": 0.0,
    }) for i in range(n)]
    for node in concepts:
        inner.add_edge_unchecked(mt, "has_concept", node, {})
    for (i, j), weight in pairwise.items():
        inner.add_edge_unchecked(concepts[i], "causal_influence", concepts[j], {"weight": weight})
        inner.add_edge_unchecked(concepts[j], "causal_influence", concepts[i], {"weight": weight})
    net = cjt.can_network_from_mt(s, mt)
    local = {node.value: i for i, node in enumerate(concepts)}
    edges = [(local[a], local[b]) for a, b in net["edges"]]
    if ({local[i]: v for i, v in net["unary"].items()} != unary or
        {frozenset(local[i] for i in pair): v for pair, v in net["pairwise"].items()} !=
        {frozenset(pair): v for pair, v in pairwise.items()}):
        raise AssertionError("runtime extraction mismatch")

    t0 = time.perf_counter_ns()
    greedy = min_fill_upper_bound(list(range(n)), edges)
    greedy_ns = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    leaf_order, leaf_width = forest_peo(n, edges)
    leaf_ns = time.perf_counter_ns() - t0
    if greedy["treewidth"] != 1 or leaf_width != 1:
        raise AssertionError("ordering width mismatch")

    t0 = time.perf_counter_ns()
    a = cjt.junction_tree_map(list(range(n)), edges, unary,
                              {frozenset(pair): v for pair, v in pairwise.items()},
                              VOCAB, order=greedy["elimination_order"])
    greedy_map_ns = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    b = cjt.junction_tree_map(list(range(n)), edges, unary,
                              {frozenset(pair): v for pair, v in pairwise.items()},
                              VOCAB, order=leaf_order)
    leaf_map_ns = time.perf_counter_ns() - t0
    if abs(a["energy"] - b["energy"]) > 1e-9 or a["max_bag_size"] != 2 or b["max_bag_size"] != 2:
        raise AssertionError("paired orders changed exact result or width")
    return {
        "nodes": n, "edges": len(edges), "replicate": rep, "seed": seed,
        "both_orders_width_one": True, "exact_energy_gap": a["energy"] - b["energy"],
        "timing_ns": {"min_fill_order": greedy_ns, "forest_leaf_order": leaf_ns,
                      "map_after_min_fill": greedy_map_ns, "map_after_leaf_order": leaf_map_ns},
    }


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), int(sys.argv[3])), sort_keys=True))
        return
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{ROOT / 'scripts'}:{env.get('PYTHONPATH', '')}"
    runs = []
    for n in SIZES:
        for rep in range(REPLICATES):
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(n), str(rep)],
                                  cwd=ROOT, env=env, text=True, capture_output=True, check=True)
            runs.append(json.loads(proc.stdout.strip()))
            r = runs[-1]
            print(f"n={n} rep={rep} minfill_ms={r['timing_ns']['min_fill_order']/1e6:.2f} "
                  f"leaf_ms={r['timing_ns']['forest_leaf_order']/1e6:.3f}", flush=True)
    summaries = []
    for n in SIZES:
        group = [r for r in runs if r["nodes"] == n]
        summaries.append({
            "nodes": n, "edges": n - 1, "replicates": len(group),
            "median_ns": {k: int(statistics.median(r["timing_ns"][k] for r in group))
                          for k in group[0]["timing_ns"]},
            "median_order_speedup": statistics.median(
                r["timing_ns"]["min_fill_order"] / max(1, r["timing_ns"]["forest_leaf_order"])
                for r in group),
        })
    source_paths = [Path(__file__).resolve(), ROOT / "scripts/can_bounded_width_scale.py",
                    ROOT / "domains/can_junction_tree.py", ROOT / "domains/graph_treewidth.py",
                    ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
                    ROOT / "runners/dsl/python/substrate_rs/_native.build.json"]
    payload = {
        "schema_version": 1, "run_id": "can-forest-ordering-comparison-20260925-v1",
        "scope": "paired min-fill and forest leaf-elimination ordering on runtime-extracted binary paths",
        "claim_boundary": "Leaf ordering is valid and measured only for forests; path result is not a general replacement for min-fill or evidence about natural graph topology.",
        "configuration": {"sizes": SIZES, "replicates": REPLICATES},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor()},
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in source_paths},
        "checks": {"all_orders_width_one": all(r["both_orders_width_one"] for r in runs),
                   "all_exact_maps_agree": all(abs(r["exact_energy_gap"]) <= 1e-9 for r in runs),
                   "all_replicates_present": all(sum(r["nodes"] == n for r in runs) == REPLICATES for n in SIZES)},
        "summaries": summaries, "runs": runs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"runs": len(runs), "checks": payload["checks"], "output": str(OUT)}, indent=2))
    if not all(payload["checks"].values()):
        raise SystemExit("ordering comparison failed")


if __name__ == "__main__":
    main()
