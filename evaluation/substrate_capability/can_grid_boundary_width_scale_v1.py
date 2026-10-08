#!/usr/bin/env python3
"""Exact CAN MAP scaling across grid separator width and length."""
from __future__ import annotations

import hashlib
import itertools
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
PROTOCOL = ROOT / "docs/research/engine_substrate/CAN_GRID_BOUNDARY_WIDTH_SCALE_V1_PREREG_20260929.md"
RUNNER = Path(__file__).resolve()
AMENDMENT = ROOT / "docs/research/engine_substrate/CAN_GRID_BOUNDARY_WIDTH_SCALE_V1_1_AMENDMENT_20260929.md"
AMENDMENT_V1_2 = ROOT / "docs/research/engine_substrate/CAN_GRID_BOUNDARY_WIDTH_SCALE_V1_2_AMENDMENT_20260929.md"
LOCK = ROOT / "evaluation/substrate_capability/can_grid_boundary_width_scale_v1_2_lock_20260929.json"
OUT = ROOT / "evaluation/reports/can_grid_boundary_width_scale_v1_2_20260929.json"
WIDTHS = (1, 2, 3, 4, 5, 6)
LENGTHS = (32, 128, 512)
REPLICATES = 3
VOCAB = (-1.0, 1.0)
SOURCES = (
    "domains/can_junction_tree.py", "domains/graph_treewidth.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)


def digest(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def input_lock() -> dict:
    return {"schema_version": 1, "protocol": digest(PROTOCOL),
            "amendments": [digest(AMENDMENT), digest(AMENDMENT_V1_2)],
            "runner": digest(RUNNER),
            "sources": [digest(ROOT / p) for p in SOURCES], "widths": list(WIDTHS),
            "lengths": list(LENGTHS), "replicates": REPLICATES,
            "vocabulary": list(VOCAB),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                   text=True).strip()}


def make_model(q: int, m: int, rep: int):
    seed = 20260929 + q * 1000003 + m * 1009 + rep * 65537
    rng = random.Random(seed)
    n = q * m
    unary = {i: rng.randint(-8, 8) / 4.0 for i in range(n)}
    pair = {}
    for col in range(m):
        for row in range(q - 1):
            pair[(col * q + row, col * q + row + 1)] = rng.randint(-8, 8) / 4.0
        if col + 1 < m:
            for row in range(q):
                pair[(col * q + row, (col + 1) * q + row)] = rng.randint(-8, 8) / 4.0
    return seed, unary, pair


def grid_dp(q: int, m: int, unary: dict, pair: dict):
    states = list(itertools.product(VOCAB, repeat=q))
    def local(col, state):
        cost = -sum(unary[col * q + row] * state[row] for row in range(q))
        for row in range(q - 1):
            cost -= pair[(col * q + row, col * q + row + 1)] * state[row] * state[row + 1]
        return cost
    def link(col, prev, cur):
        return -sum(pair[(col * q + row, (col + 1) * q + row)] * prev[row] * cur[row]
                    for row in range(q))
    costs = {s: local(0, s) for s in states}
    back = {}
    operations = len(states)
    for col in range(1, m):
        nxt = {}
        for cur in states:
            best = min((costs[prev] + link(col - 1, prev, cur) + local(col, cur), prev)
                       for prev in states)
            nxt[cur], back[(col, cur)] = best
            operations += len(states)
        costs = nxt
    best_energy, state = min((costs[s], s) for s in states)
    assignment = {((m - 1) * q + row): state[row] for row in range(q)}
    for col in range(m - 1, 0, -1):
        state = back[(col, state)]
        for row in range(q):
            assignment[(col - 1) * q + row] = state[row]
    return best_energy, assignment, operations


def energy(unary, pair, state):
    return (-sum(v * state[i] for i, v in unary.items())
            -sum(w * state[i] * state[j] for (i, j), w in pair.items()))


def timed_map(cjt, nodes, edges, unary, pair, order):
    tracemalloc.start()
    start = time.perf_counter_ns()
    result = cjt.junction_tree_map(nodes, edges, unary,
                                   {frozenset(k): v for k, v in pair.items()}, VOCAB, order=order)
    elapsed = time.perf_counter_ns() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def worker(q: int, m: int, rep: int) -> dict:
    import substrate_rs as sr
    import domains.can_junction_tree as cjt
    from domains.graph_treewidth import min_fill_upper_bound
    seed, unary, pair = make_model(q, m, rep)
    s = sr.Substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {"discrete_mode": "2state"})
    concepts = [inner.add_node("Concept", {"name": f"x{i}", "external_field": unary[i],
                                            "identity_field": 0.0, "state": 0.0})
                for i in range(q * m)]
    for node in concepts:
        inner.add_edge_unchecked(mt, "has_concept", node, {})
    for (i, j), w in pair.items():
        inner.add_edge_unchecked(concepts[i], "causal_influence", concepts[j], {"weight": w})
        inner.add_edge_unchecked(concepts[j], "causal_influence", concepts[i], {"weight": w})
    start = time.perf_counter_ns()
    net = cjt.can_network_from_mt(s, mt)
    extract_ns = time.perf_counter_ns() - start
    local = {node.value: i for i, node in enumerate(concepts)}
    got_unary = {local[i]: v for i, v in net["unary"].items()}
    got_pair = {tuple(sorted(local[i] for i in edge)): v for edge, v in net["pairwise"].items()}
    want_pair = {tuple(sorted(k)): v for k, v in pair.items()}
    extraction_exact = got_unary == unary and got_pair == want_pair
    if not extraction_exact:
        raise AssertionError("runtime extraction differs from generated grid")
    nodes = list(range(q * m))
    edges = [tuple(k) for k in got_pair]
    start = time.perf_counter_ns()
    ordering = min_fill_upper_bound(nodes, edges)
    minfill_ns = time.perf_counter_ns() - start
    oracle_energy, _, oracle_ops = grid_dp(q, m, unary, pair)
    minfill, minfill_ns_map, minfill_peak = timed_map(
        cjt, nodes, edges, unary, pair, ordering["elimination_order"])
    fixed, fixed_ns_map, fixed_peak = timed_map(cjt, nodes, edges, unary, pair, nodes)
    minfill_gap = energy(unary, pair, minfill["state"]) - oracle_energy
    fixed_gap = energy(unary, pair, fixed["state"]) - oracle_energy
    return {"width": q, "length": m, "nodes": q * m, "edges": len(edges), "replicate": rep,
            "seed": seed, "reported_treewidth": ordering["treewidth"],
            "minfill_bag_size": minfill["max_bag_size"],
            "fixed_order_bag_size": fixed["max_bag_size"],
            "oracle_operations": oracle_ops, "minfill_energy_gap": minfill_gap,
            "fixed_order_energy_gap": fixed_gap, "extraction_exact": extraction_exact,
            "timing_ns": {"runtime_graph_extract": extract_ns, "min_fill_order": minfill_ns,
                          "junction_tree_minfill": minfill_ns_map,
                          "junction_tree_fixed_order": fixed_ns_map},
            "traced_peak_bytes": {"minfill": minfill_peak, "fixed_order": fixed_peak},
            "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def main() -> None:
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])), sort_keys=True))
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite existing lock/capture")
        LOCK.write_text(json.dumps(input_lock(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    lock = json.loads(LOCK.read_text())
    if input_lock() != lock:
        raise SystemExit("source/fixture lock drift")
    from domains.engine_provenance import build_is_stale
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("native build stale:\n" + "\n".join(stale))
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    rows = []
    for q in WIDTHS:
        for m in LENGTHS:
            for rep in range(REPLICATES):
                proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(q), str(m), str(rep)],
                                      cwd=ROOT, env=env, text=True, capture_output=True, check=True)
                row = json.loads(proc.stdout.strip())
                rows.append(row)
                print(f"width={q} length={m} rep={rep} nodes={row['nodes']} tw={row['reported_treewidth']} "
                      f"jt_ms={row['timing_ns']['junction_tree_minfill']/1e6:.2f}", flush=True)
    post = input_lock()
    if post != lock:
        raise SystemExit("post-run source/fixture lock drift")
    summaries = []
    for q in WIDTHS:
        for m in LENGTHS:
            cell = [r for r in rows if r["width"] == q and r["length"] == m]
            summaries.append({"known_grid_width": q, "minfill_width_median": int(statistics.median(
                                  r["reported_treewidth"] for r in cell)),
                              "length": m, "nodes": q*m, "replicates": len(cell),
                              "median_timing_ns": {k: int(statistics.median(r["timing_ns"][k] for r in cell))
                                                   for k in cell[0]["timing_ns"]},
                              "median_traced_peak_bytes": {k: int(statistics.median(r["traced_peak_bytes"][k]
                                                                                 for r in cell))
                                                           for k in cell[0]["traced_peak_bytes"]},
                              "max_process_peak_rss_kib": max(r["process_peak_rss_kib"] for r in cell),
                              "median_oracle_operations": int(statistics.median(r["oracle_operations"]
                                                                                 for r in cell))})
    payload = {"schema_version": 1, "run_id": "can-grid-boundary-width-scale-v1.2-20260929",
               "status": "complete", "input_lock": lock, "post_run_input_lock": post,
               "scope": "binary exact MAP on runtime-extracted rectangular grids with independent column DP",
               "claim_boundary": "synthetic known-separator family only; no natural-cut or frame-discovery claim",
               "configuration": {"widths": WIDTHS, "lengths": LENGTHS,
                                 "replicates_per_cell": REPLICATES, "vocabulary": VOCAB},
               "environment": {"python": platform.python_version(), "platform": platform.platform(),
                               "processor": platform.processor()},
               "checks": {"complete_workers": len(rows) == len(WIDTHS)*len(LENGTHS)*REPLICATES,
                          "three_replicates_each": all(sum(r["width"] == q and r["length"] == m for r in rows)
                                                        == REPLICATES for q in WIDTHS for m in LENGTHS),
                          "fixed_column_order_expected_bags": all(
                              r["fixed_order_bag_size"] == r["width"]+1 for r in rows),
                          "minfill_width_is_valid_upper_bound_record": all(
                              r["reported_treewidth"] >= r["width"] and
                              r["minfill_bag_size"] == r["reported_treewidth"]+1 for r in rows),
                          "exact_extraction": all(r["extraction_exact"] for r in rows),
                          "minfill_oracle_match": all(abs(r["minfill_energy_gap"]) <= 1e-8 for r in rows),
                          "fixed_order_oracle_match": all(abs(r["fixed_order_energy_gap"]) <= 1e-8 for r in rows),
                          "pre_post_lock_match": lock == post},
               "summaries": summaries, "runs": rows}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(), "checks": payload["checks"]}, indent=2))
    if not all(payload["checks"].values()):
        raise SystemExit("grid width scale invariants failed")


if __name__ == "__main__":
    main()
