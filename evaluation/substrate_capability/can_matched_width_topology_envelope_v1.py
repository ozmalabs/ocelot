#!/usr/bin/env python3
"""Matched-treewidth topology and relabelling envelope for min-fill gating."""
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
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
PROTOCOL = ROOT / "docs/research/engine_substrate/CAN_MATCHED_WIDTH_TOPOLOGY_ENVELOPE_V1_PREREG_20260929.md"
RUNNER = Path(__file__).resolve()
AMENDMENT = ROOT / "docs/research/engine_substrate/CAN_MATCHED_WIDTH_TOPOLOGY_ENVELOPE_V1_1_AMENDMENT_20260929.md"
LOCK = ROOT / "evaluation/substrate_capability/can_matched_width_topology_envelope_v1_1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/can_matched_width_topology_envelope_v1_1_20260929.json"
WIDTHS = (4, 5, 6)
N = 120
FAMILIES = ("grid", "qtree_path", "qtree_hub", "qtree_random")
REPLICATES = 12
SOURCES = ("domains/graph_treewidth.py", "domains/can_junction_tree.py")


def digest(path: Path):
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def input_lock():
    return {"schema_version": 1, "protocol": digest(PROTOCOL),
            "amendment": digest(AMENDMENT), "runner": digest(RUNNER),
            "sources": [digest(ROOT / path) for path in SOURCES], "widths": list(WIDTHS),
            "node_count": N, "families": list(FAMILIES), "replicates": REPLICATES,
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                   text=True).strip()}


def qtree(q, family, rng):
    # Each new vertex joins a q-clique. Reverse birth order is a width-q PEO certificate.
    edges = {tuple(sorted((i, j))) for i in range(q+1) for j in range(i+1, q+1)}
    bags = [frozenset(range(q+1))]
    birth = list(range(q+1))
    for v in range(q+1, N):
        if family == "qtree_path":
            parent = bags[-1]
            clique = frozenset(sorted(parent, reverse=True)[:q])
        elif family == "qtree_hub":
            clique = frozenset(range(q))
        else:
            clique = frozenset(rng.sample(sorted(rng.choice(bags)), q))
        for u in clique:
            edges.add(tuple(sorted((u, v))))
        bag = frozenset((*clique, v))
        bags.append(bag)
        birth.append(v)
    return edges, birth


def grid(q):
    m = N // q
    edges = set()
    for col in range(m):
        for row in range(q):
            cell = col*q+row
            if row+1 < q:
                edges.add((cell, cell+1))
            if col+1 < m:
                edges.add((cell, cell+q))
    order = list(range(N))
    return edges, order, m


def make_case(q, family, rep):
    seed = 20260929 + q*1000003 + FAMILIES.index(family)*10007 + rep*65537
    rng = random.Random(seed)
    if family == "grid":
        edges, order, m = grid(q)
        if q*m != N:
            raise AssertionError("grid node count mismatch")
    else:
        edges, order = qtree(q, family, rng)
        m = None
    # Fresh ID permutation plus shuffled node and edge order perturb repr/tie resolution.
    labels = list(range(N))
    rng.shuffle(labels)
    remapped = {old: labels[old] for old in range(N)}
    mapped_edges = [tuple(sorted((remapped[a], remapped[b]))) for a, b in edges]
    rng.shuffle(mapped_edges)
    nodes = list(range(N))
    rng.shuffle(nodes)
    if family == "grid":
        cert_order = [remapped[v] for v in order]
    else:
        cert_order = [remapped[v] for v in reversed(order)]
    return seed, nodes, mapped_edges, cert_order, m


def worker(q, family, rep):
    from domains.graph_treewidth import build_elimination_triangulation, min_fill_upper_bound, treewidth_bound_check
    seed, nodes, edges, cert_order, grid_columns = make_case(q, family, rep)
    cert = build_elimination_triangulation(nodes, edges, cert_order)
    cert_width = max((len(bag)-1 for bag in cert["bags"].values()), default=0)
    start = time.perf_counter_ns()
    result = min_fill_upper_bound(nodes, edges)
    ordering_ns = time.perf_counter_ns()-start
    bags = build_elimination_triangulation(nodes, edges, result["elimination_order"])["bags"]
    histogram = dict(sorted(Counter(len(bag) for bag in bags.values()).items()))
    start = time.perf_counter_ns()
    gate = treewidth_bound_check(nodes, edges, q, max_exact_n=10)
    gate_ns = time.perf_counter_ns()-start
    if family != "grid":
        clique_lower_bound = q  # Initial (q+1)-clique is retained by remapping.
    else:
        clique_lower_bound = None
    return {"width": q, "family": family, "replicate": rep, "seed": seed,
            "nodes": len(nodes), "edges": len(edges), "grid_columns": grid_columns,
            "certificate_width": cert_width, "clique_lower_bound": clique_lower_bound,
            "minfill_width": result["treewidth"], "minfill_bag_size_histogram": histogram,
            "production_gate_width": gate["treewidth"],
            "production_gate_within_bound_q": gate["within_bound"],
            "production_gate_within_bound_q_minus_1": gate["treewidth"] <= q-1,
            "ordering_ns": ordering_ns, "gate_ns": gate_ns}


def main():
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), sys.argv[3], int(sys.argv[4])), sort_keys=True))
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite existing lock/capture")
        LOCK.write_text(json.dumps(input_lock(), indent=2, sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT))
        return
    lock = json.loads(LOCK.read_text())
    if input_lock() != lock:
        raise SystemExit("source/fixture lock drift")
    rows = []
    for q in WIDTHS:
        for family in FAMILIES:
            for rep in range(REPLICATES):
                proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(q), family, str(rep)],
                                      cwd=ROOT, env={**os.environ,
                                      "PYTHONPATH": f"{ROOT}:{os.environ.get('PYTHONPATH','')}"},
                                      text=True, capture_output=True, check=True)
                row = json.loads(proc.stdout.strip())
                rows.append(row)
                print(f"q={q} family={family} rep={rep} minfill={row['minfill_width']} "
                      f"ms={row['ordering_ns']/1e6:.2f}", flush=True)
    post = input_lock()
    checks = {"complete_workers": len(rows) == len(WIDTHS)*len(FAMILIES)*REPLICATES,
              "coverage": all(sum(r["width"]==q and r["family"]==f for r in rows)==REPLICATES
                              for q in WIDTHS for f in FAMILIES),
              "fixed_width_certificates": all(r["certificate_width"]==r["width"] for r in rows),
              "minfill_no_underestimate": all(r["minfill_width"]>=r["width"] for r in rows),
              "gate_matches_minfill": all(r["production_gate_width"]==r["minfill_width"] and
                                           r["production_gate_within_bound_q"]==
                                           (r["minfill_width"]<=r["width"]) for r in rows),
              "stricter_bound_refuses": all(not r["production_gate_within_bound_q_minus_1"] for r in rows),
              "pre_post_lock_match": lock==post}
    payload = {"schema_version": 1, "run_id": "can-matched-width-topology-envelope-v1-20260929",
               "status": "complete", "input_lock": lock, "post_run_input_lock": post,
               "configuration": {"widths": WIDTHS, "node_count": N, "families": FAMILIES,
                                 "replicates_per_cell": REPLICATES},
               "claim_boundary": "four synthetic known-width graph families only; no natural-task prevalence",
               "environment": {"python": platform.python_version(), "platform": platform.platform()},
               "checks": checks, "runs": rows}
    payload["run_id"] = "can-matched-width-topology-envelope-v1.1-20260929"
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("matched topology envelope integrity failure")


if __name__ == "__main__":
    main()
