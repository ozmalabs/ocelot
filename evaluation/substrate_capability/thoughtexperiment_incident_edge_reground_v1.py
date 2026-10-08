#!/usr/bin/env python3
"""Measure local incident-edge reads against full graph serialization."""
from __future__ import annotations

import hashlib, json, os, platform, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
CELLS = ((0, 4), (10000, 4), (50000, 4), (50000, 32))
REPEATS = 5
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_incident_edge_reground_v1.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_INCIDENT_EDGE_REGROUND_V1_PREREG_20261001.md",
    "domains/imagination.py", "runners/dsl/src/py.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_incident_edge_reground_v1.json"

def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def make_graph(background_nodes: int, target_degree: int):
    from substrate_rs import Substrate
    sub = Substrate()
    target = sub.add_node("Target", {"version": 1})
    peers = [sub.add_node("Peer", {"ordinal": i}) for i in range(target_degree)]
    for i, peer in enumerate(peers):
        sub.add_edge_unchecked(target, f"target_edge_{i}", peer, {"weight": i})
    previous = None
    for i in range(background_nodes):
        node = sub.add_node("Background", {"ordinal": i})
        if previous is not None:
            sub.add_edge_unchecked(previous, "background_next", node, {})
        previous = node
    expected = sorted(
        [{"src": target.value, "type": f"target_edge_{i}", "tgt": peer.value,
          "attrs": {"weight": i}} for i, peer in enumerate(peers)],
        key=lambda edge: (edge["src"], edge["type"], edge["tgt"]))
    return sub, target, expected

def worker() -> dict:
    from substrate_rs import Substrate
    rows = []
    for size, degree in CELLS:
        sub, target, expected = make_graph(size, degree)
        local_samples, full_samples = [], []
        for _ in range(REPEATS):
            start = time.perf_counter_ns()
            local = sub.incident_edges(target)
            local_samples.append((time.perf_counter_ns() - start) / 1e6)
            start = time.perf_counter_ns()
            graph = sub.graph_to_dict()
            filtered = [edge for edge in graph["edges"]
                        if edge["src"] == target.value or edge["tgt"] == target.value]
            full_samples.append((time.perf_counter_ns() - start) / 1e6)
        local = sorted(local, key=lambda edge: (edge["src"], edge["type"], edge["tgt"]))
        filtered = sorted(filtered, key=lambda edge: (edge["src"], edge["type"], edge["tgt"]))
        rows.append({
            "background_nodes": size, "target_degree": degree,
            "graph_edges": sub.edge_count(), "local_matches_oracle": local == expected,
            "full_scan_matches_oracle": filtered == expected,
            "local_median_ms": statistics.median(local_samples),
            "full_scan_median_ms": statistics.median(full_samples),
            "local_samples_ms": local_samples, "full_scan_samples_ms": full_samples,
        })
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
    for index, (size, degree) in enumerate(CELLS):
        samples = [worker["cells"][index] for worker in workers]
        local = statistics.median(row["local_median_ms"] for row in samples)
        full = statistics.median(row["full_scan_median_ms"] for row in samples)
        aggregates.append({"background_nodes": size, "target_degree": degree,
            "graph_edges": samples[0]["graph_edges"],
            "local_median_ms_across_workers": local,
            "full_scan_median_ms_across_workers": full,
            "full_scan_over_local": full / local if local else None,
            "all_oracle_checks_pass": all(row["local_matches_oracle"]
                                           and row["full_scan_matches_oracle"]
                                           for row in samples)})
    import substrate_rs as srs
    binary = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentIncidentEdgeRegroundV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "source_sha256": {name: sha_file(ROOT / name) for name in SOURCES},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "worker_count": len(workers), "workers": workers, "aggregates": aggregates,
        "checks": {"five_fresh_workers": len({w["pid"] for w in workers}) == 5,
                   "all_local_and_full_oracles_match": all(
                       row["all_oracle_checks_pass"] for row in aggregates)},
    }
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": capture["checks"], "aggregates": aggregates}, indent=2))
    return 0 if all(capture["checks"].values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
