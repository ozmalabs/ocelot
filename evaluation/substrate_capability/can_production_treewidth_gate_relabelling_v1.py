#!/usr/bin/env python3
"""Probe the production exact-inference width gate under grid node relabelling."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
PROTOCOL = ROOT / "docs/research/engine_substrate/CAN_PRODUCTION_TREEWIDTH_GATE_RELABELLING_V1_PREREG_20260929.md"
RUNNER = Path(__file__).resolve()
AMENDMENT = ROOT / "docs/research/engine_substrate/CAN_PRODUCTION_TREEWIDTH_GATE_RELABELLING_V1_1_AMENDMENT_20260929.md"
LOCK = ROOT / "evaluation/substrate_capability/can_production_treewidth_gate_relabelling_v1_1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/can_production_treewidth_gate_relabelling_v1_1_20260929.json"
WIDTHS = (1, 2, 3, 4, 5, 6)
LENGTH = 32
REPLICATES = 12
BOUND = 4
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
            "amendment": digest(AMENDMENT), "runner": digest(RUNNER),
            "sources": [digest(ROOT / p) for p in SOURCES], "widths": list(WIDTHS),
            "length": LENGTH, "replicates": REPLICATES, "bound": BOUND,
            "vocabulary": list(VOCAB),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                   text=True).strip()}


def generate(q: int, rep: int):
    seed = 20260929 + q * 1000003 + rep * 65537
    rng = random.Random(seed)
    n = q * LENGTH
    unary = {cell: rng.randint(-8, 8) / 4.0 for cell in range(n)}
    pair = {}
    for col in range(LENGTH):
        for row in range(q - 1):
            pair[(col*q+row, col*q+row+1)] = rng.randint(-8, 8) / 4.0
        if col + 1 < LENGTH:
            for row in range(q):
                pair[(col*q+row, (col+1)*q+row)] = rng.randint(-8, 8) / 4.0
    order = list(range(n))
    rng.shuffle(order)
    edge_order = list(pair)
    rng.shuffle(edge_order)
    return seed, unary, pair, order, edge_order


def grid_dp(q, m, unary, pair):
    states = list(itertools.product(VOCAB, repeat=q))
    def local(col, state):
        value = -sum(unary[col*q+r]*state[r] for r in range(q))
        return value - sum(pair[(col*q+r, col*q+r+1)]*state[r]*state[r+1]
                           for r in range(q-1))
    def link(col, prev, cur):
        return -sum(pair[(col*q+r, (col+1)*q+r)]*prev[r]*cur[r] for r in range(q))
    cost = {state: local(0, state) for state in states}
    back = {}
    for col in range(1, m):
        nxt = {}
        for state in states:
            nxt[state], back[(col, state)] = min(
                (cost[prev] + link(col-1, prev, state) + local(col, state), prev)
                for prev in states)
        cost = nxt
    return min(cost.values())


def energy(unary, pair, state):
    return (-sum(v*state[i] for i, v in unary.items())
            -sum(w*state[i]*state[j] for (i, j), w in pair.items()))


def worker(q: int, rep: int):
    import substrate_rs as sr
    import domains.can_junction_tree as cjt
    from domains.graph_treewidth import build_elimination_triangulation
    seed, unary, pair, insertion, edge_order = generate(q, rep)
    s = sr.Substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {"discrete_mode": "2state"})
    concept_by_cell = {}
    for cell in insertion:
        concept_by_cell[cell] = inner.add_node("Concept", {
            "name": f"cell_{cell}", "external_field": unary[cell],
            "identity_field": 0.0, "state": 0.0})
    for node in concept_by_cell.values():
        inner.add_edge_unchecked(mt, "has_concept", node, {})
    for i, j in edge_order:
        w = pair[(i, j)]
        inner.add_edge_unchecked(concept_by_cell[i], "causal_influence", concept_by_cell[j],
                                 {"weight": w})
        inner.add_edge_unchecked(concept_by_cell[j], "causal_influence", concept_by_cell[i],
                                 {"weight": w})
    net = cjt.can_network_from_mt(s, mt)
    id_for_cell = {cell: node.value for cell, node in concept_by_cell.items()}
    local = {node.value: cell for cell, node in concept_by_cell.items()}
    ext_unary = {local[node]: value for node, value in net["unary"].items()}
    ext_pair = {tuple(sorted(local[node] for node in edge)): value
                for edge, value in net["pairwise"].items()}
    extraction_exact = ext_unary == unary and ext_pair == {tuple(sorted(k)): v for k, v in pair.items()}
    nodes = list(net["nodes"])
    edges = list(net["edges"])
    column_order = [id_for_cell[col*q+row] for col in range(LENGTH) for row in range(q)]
    cert = build_elimination_triangulation(nodes, edges, column_order)
    certificate_width = max((len(bag)-1 for bag in cert["bags"].values()), default=0)
    initial_states = {cell: float(inner.node(handle)["attrs"].get("state", 0.0))
                      for cell, handle in concept_by_cell.items()}
    oracle = grid_dp(q, LENGTH, unary, pair)
    start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
    result = cjt.junction_tree_exact_settle(inner, mt, treewidth_bound=BOUND,
                                            max_exact_n=10, commit=False)
    wall_ns, cpu_ns = time.perf_counter_ns()-start_wall, time.process_time_ns()-start_cpu
    final_states = {cell: float(inner.node(handle)["attrs"].get("state", 0.0))
                    for cell, handle in concept_by_cell.items()}
    attempted = bool(result["attempted"])
    gap = None
    if attempted:
        by_cell = {local[node]: value for node, value in result["state"].items()}
        gap = energy(unary, pair, by_cell) - oracle
    return {"width": q, "length": LENGTH, "replicate": rep, "seed": seed,
            "nodes": len(nodes), "edges": len(edges), "insertion_order": insertion,
            "certificate_width": certificate_width, "extraction_exact": extraction_exact,
            "attempted": attempted, "exact": bool(result["exact"]),
            "reported_treewidth": result["treewidth"],
            "returned_state": isinstance(result.get("state"), dict),
            "oracle_energy_gap": gap, "no_mutation": initial_states == final_states,
            "reason": result.get("reason"), "wall_ns": wall_ns, "cpu_ns": cpu_ns,
            "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), int(sys.argv[3])), sort_keys=True))
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
    env["PYTHONPATH"] = f"{ROOT/'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH','')}"
    rows = []
    for q in WIDTHS:
        for rep in range(REPLICATES):
            proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(q), str(rep)],
                                  cwd=ROOT, env=env, text=True, capture_output=True, check=True)
            row = json.loads(proc.stdout.strip())
            rows.append(row)
            print(f"q={q} rep={rep} tw={row['reported_treewidth']} attempted={row['attempted']} "
                  f"wall_ms={row['wall_ns']/1e6:.2f}", flush=True)
    post = input_lock()
    checks = {"complete_workers": len(rows) == len(WIDTHS)*REPLICATES,
              "replicate_coverage": all(sum(r["width"] == q for r in rows) == REPLICATES for q in WIDTHS),
              "exact_graph_extraction": all(r["extraction_exact"] for r in rows),
              "column_width_certificates": all(r["certificate_width"] == r["width"] for r in rows),
              "accepted_routes_match_oracle": all(not r["attempted"] or
                  (r["exact"] and r["returned_state"] and abs(r["oracle_energy_gap"]) <= 1e-8)
                  for r in rows),
              "refused_routes_return_no_state": all(r["attempted"] or not r["returned_state"] for r in rows),
              "no_graph_mutation": all(r["no_mutation"] for r in rows),
              "no_unsafe_acceptance": all(r["width"] <= BOUND or not r["attempted"] for r in rows),
              "pre_post_lock_match": lock == post}
    payload = {"schema_version": 1, "run_id": "can-production-treewidth-gate-relabelling-v1.1-20260929",
               "status": "complete", "input_lock": lock, "post_run_input_lock": post,
               "claim_boundary": "label/order sensitivity for one binary grid family; no natural-task estimate",
               "configuration": {"widths": WIDTHS, "length": LENGTH, "replicates": REPLICATES,
                                 "default_width_bound": BOUND},
               "environment": {"python": platform.python_version(), "platform": platform.platform(),
                               "processor": platform.processor()},
               "checks": checks, "runs": rows}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("production gate probe integrity failure")


if __name__ == "__main__":
    main()
