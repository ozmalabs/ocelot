#!/usr/bin/env python3
"""Scale exact CAN MAP on runtime-extracted path graphs against a chain DP oracle."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import resource
import statistics
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/can_bounded_width_scale_20260925.json"
SIZES = (32, 64, 128, 256, 512, 1024, 2048)
REPLICATES = 3
VOCAB = (-1.0, 1.0)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_model(n: int, seed: int):
    rng = random.Random(seed)
    unary = {i: rng.randint(-8, 8) / 4.0 for i in range(n)}
    pairwise = {(i, i + 1): rng.randint(-8, 8) / 4.0 for i in range(n - 1)}
    return unary, pairwise


def independent_chain_map(unary, pairwise):
    """Two-state exact dynamic program, implemented independently of junction tree."""
    n = len(unary)
    costs = {}
    back = {}
    for state in VOCAB:
        costs[(0, state)] = -unary[0] * state
    for i in range(1, n):
        for state in VOCAB:
            choices = []
            for prev in VOCAB:
                value = costs[(i - 1, prev)] - unary[i] * state
                value -= pairwise[(i - 1, i)] * prev * state
                choices.append((value, prev))
            costs[(i, state)], back[(i, state)] = min(choices)
    final_energy, state = min((costs[(n - 1, s)], s) for s in VOCAB)
    assignment = {n - 1: state}
    for i in range(n - 1, 0, -1):
        assignment[i - 1] = back[(i, assignment[i])]
    return final_energy, assignment, 4 * n - 2


def worker(n: int, rep: int) -> dict:
    import substrate_rs as sr
    import domains.can_junction_tree as cjt
    from domains.graph_treewidth import min_fill_upper_bound

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

    t0 = time.perf_counter_ns()
    net0 = cjt.can_network_from_mt(s, mt)
    extract_ns = time.perf_counter_ns() - t0
    local_of = {node.value: i for i, node in enumerate(concepts)}
    edges = [(local_of[a], local_of[b]) for a, b in net0["edges"]]
    extracted_unary = {local_of[i]: v for i, v in net0["unary"].items()}
    extracted_pairwise = {
        tuple(sorted(local_of[i] for i in pair)): value
        for pair, value in net0["pairwise"].items()
    }
    if extracted_unary != unary or extracted_pairwise != pairwise:
        raise AssertionError("runtime extraction differs from generated model")

    t0 = time.perf_counter_ns()
    width = min_fill_upper_bound(list(range(n)), edges)
    width_ns = time.perf_counter_ns() - t0
    exact_energy, oracle_state, oracle_ops = independent_chain_map(unary, pairwise)
    jt_pairwise = {frozenset(edge): value for edge, value in extracted_pairwise.items()}
    tracemalloc.start()
    t0 = time.perf_counter_ns()
    exact = cjt.junction_tree_map(list(range(n)), edges, unary, jt_pairwise, VOCAB,
                                  order=width["elimination_order"])
    jt_ns = time.perf_counter_ns() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    scored_energy = -sum(unary[i] * exact["state"][i] for i in range(n))
    scored_energy -= sum(weight * exact["state"][i] * exact["state"][j]
                         for (i, j), weight in pairwise.items())
    oracle_scored = -sum(unary[i] * oracle_state[i] for i in range(n))
    oracle_scored -= sum(weight * oracle_state[i] * oracle_state[j]
                         for (i, j), weight in pairwise.items())
    if abs(exact_energy - oracle_scored) > 1e-9 or abs(scored_energy - oracle_scored) > 1e-9:
        raise AssertionError("junction tree disagrees with independent chain oracle")
    if width["treewidth"] != 1 or exact["max_bag_size"] != 2:
        raise AssertionError("path graph did not retain width one")
    return {
        "nodes": n, "edges": len(edges), "replicate": rep, "seed": seed,
        "treewidth_upper_bound": width["treewidth"],
        "max_bag_size": exact["max_bag_size"],
        "oracle_operations": oracle_ops,
        "exact_energy_gap": scored_energy - oracle_scored,
        "input_extraction_exact": True,
        "timing_ns": {"runtime_graph_extract": extract_ns, "min_fill_width": width_ns,
                      "junction_tree_map": jt_ns},
        "junction_tree_traced_peak_bytes": peak,
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), int(sys.argv[3])), sort_keys=True))
        return
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    records = []
    for n in SIZES:
        for rep in range(REPLICATES):
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(n), str(rep)],
                                  cwd=ROOT, env=env, text=True, capture_output=True, check=True)
            records.append(json.loads(proc.stdout.strip()))
            print(f"n={n} rep={rep} width={records[-1]['treewidth_upper_bound']} "
                  f"jt_ms={records[-1]['timing_ns']['junction_tree_map'] / 1e6:.3f}", flush=True)
    summaries = []
    for n in SIZES:
        group = [r for r in records if r["nodes"] == n]
        summaries.append({
            "nodes": n, "edges": n - 1, "replicates": len(group), "treewidth": 1,
            "median_timing_ns": {key: int(statistics.median(r["timing_ns"][key] for r in group))
                                 for key in group[0]["timing_ns"]},
            "median_traced_peak_bytes": int(statistics.median(r["junction_tree_traced_peak_bytes"] for r in group)),
            "max_process_peak_rss_kib": max(r["process_peak_rss_kib"] for r in group),
            "median_oracle_operations": int(statistics.median(r["oracle_operations"] for r in group)),
        })
    source_paths = [Path(__file__).resolve(), ROOT / "domains/can_junction_tree.py",
                    ROOT / "domains/graph_treewidth.py", ROOT / "runners/dsl/src/memory.rs",
                    ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"]
    payload = {
        "schema_version": 1,
        "run_id": "can-bounded-width-scale-20260925-v1",
        "scope": "exact MAP on runtime-extracted two-state path graphs, sizes 32..2048, compared to independent chain DP",
        "claim_boundary": "Measures one synthetic width-one inference family through the current substrate graph extractor and Python junction-tree implementation. Does not show frame discovery, natural-task locality, learned structure, general graph scaling, or native allocation totals.",
        "configuration": {"sizes": SIZES, "replicates": REPLICATES, "domain": list(VOCAB)},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor()},
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in source_paths},
        "checks": {"all_extractions_exact": all(r["input_extraction_exact"] for r in records),
                   "all_width_one": all(r["treewidth_upper_bound"] == 1 and r["max_bag_size"] == 2 for r in records),
                   "all_exact_oracle_agree": all(abs(r["exact_energy_gap"]) <= 1e-9 for r in records),
                   "replicates_per_size": all(sum(r["nodes"] == n for r in records) == REPLICATES for n in SIZES)},
        "summaries": summaries, "runs": records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"runs": len(records), "checks": payload["checks"], "output": str(OUT)}, indent=2))
    if not all(payload["checks"].values()):
        raise SystemExit("scale invariant failed")


if __name__ == "__main__":
    main()
