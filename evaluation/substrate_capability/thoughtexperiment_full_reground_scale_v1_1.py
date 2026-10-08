#!/usr/bin/env python3
"""Balanced graph-size × deletion-receipt-size panel for complete reground."""
from __future__ import annotations

import hashlib, json, math, os, platform, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
SIZES = (1000, 10000, 50000)
DELETIONS = (1, 16, 128)
CELLS = tuple((size, count) for size in SIZES for count in DELETIONS)
REPEATS = 7
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_full_reground_scale_v1_1.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_FULL_REGROUND_SCALE_V1_1_PREREG_20261001.md",
    "domains/imagination.py", "runners/dsl/src/py.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_full_reground_scale_v1_1.json"

def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def make_case(node_count: int, deletion_count: int):
    from substrate_rs import Substrate
    from domains.imagination import DetachedCollapse
    sub = Substrate()
    node_ids = [sub.add_node("State", {"ordinal": i}) for i in range(node_count)]
    for i in range(node_count - 1):
        sub.add_edge_unchecked(node_ids[i], "next", node_ids[i + 1], {"ordinal": i})
    targets = [((i + 1) * node_count // (deletion_count + 1))
               for i in range(deletion_count)]
    imagination = sub.add_node("Imagination", {"status": "imagining"})
    conclusion_ids, incident_edge_count = [], 0
    for nid_index in targets:
        nid = node_ids[nid_index]
        before = sub.node(nid)
        incident = sub.incident_edges(nid)
        incident_edge_count += len(incident)
        conclusion_ids.append(sub.add_node("ImaginedConclusion", {
            "kind": "node_removed", "detached_id": nid.value,
            "node_type_before": before["type"], "attrs_before": before["attrs"],
            "incident_edges_before": incident, "status": "pending", "reason": "",
        }))
    detached = DetachedCollapse(detached=None, imagination_node=imagination,
        conclusion_nodes=conclusion_ids, focus_nodes=None, hypothesis=None, hyp_map={},
        cut_grounding=False, grounding_cut_count=0, steps_run=0, steps_budget=0,
        converged=True, conclusions={}, derived_only={}, n_conclusions=deletion_count,
        residual=0.0, confidence=1.0, phase_timings_ms={})
    return sub, detached, incident_edge_count

def worker() -> dict:
    from domains.imagination import reground
    rows = []
    for node_count, deletion_count in CELLS:
        sub, detached, incident_edge_count = make_case(node_count, deletion_count)
        samples, parity = [], True
        for _ in range(REPEATS):
            started = time.perf_counter_ns()
            result = reground(sub, detached)
            samples.append((time.perf_counter_ns() - started) / 1e6)
            parity &= (len(result["survivors"]) == deletion_count
                and len(result["discarded"]) == 0
                and len(result["detail"]) == deletion_count
                and all(item["survived"] for item in result["detail"]))
        ordered = sorted(samples)
        rows.append({"nodes": node_count, "deletions": deletion_count,
            "validated_incident_edges": incident_edge_count, "graph_edges": sub.edge_count(),
            "oracle_parity": parity, "median_ms": statistics.median(samples),
            "p95_ms_nearest_rank": ordered[math.ceil(.95 * len(ordered)) - 1],
            "samples_ms": samples})
    return {"pid": os.getpid(), "cells": rows}

def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--worker":
        print(json.dumps(worker(), sort_keys=True, separators=(",", ":")))
        return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    workers = []
    for _ in range(5):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
            cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(proc.stderr[-4000:])
        workers.append(json.loads(proc.stdout))
    aggregates = []
    for index, (nodes, deletions) in enumerate(CELLS):
        rows = [worker["cells"][index] for worker in workers]
        medians = [row["median_ms"] for row in rows]
        aggregates.append({"nodes": nodes, "deletions": deletions,
            "validated_incident_edges": rows[0]["validated_incident_edges"],
            "median_of_worker_medians_ms": statistics.median(medians),
            "max_worker_median_ms": max(medians),
            "all_oracles_pass": all(row["oracle_parity"] for row in rows)})
    import substrate_rs as srs
    binary = Path(srs._native.__file__).resolve()
    capture = {"schema": "ThoughtexperimentFullRegroundScaleV1_1",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "source_sha256": {name: sha_file(ROOT / name) for name in SOURCES},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "worker_count": len(workers), "workers": workers, "aggregates": aggregates,
        "checks": {"five_fresh_workers": len({w["pid"] for w in workers}) == 5,
                   "all_oracles_pass": all(row["all_oracles_pass"] for row in aggregates)}}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": capture["checks"], "aggregates": aggregates}, indent=2))
    return 0 if all(capture["checks"].values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
