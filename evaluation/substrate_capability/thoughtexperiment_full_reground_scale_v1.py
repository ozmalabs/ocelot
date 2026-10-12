#!/usr/bin/env python3
"""Source-locked full reground scaling probe for node-deletion receipts."""
from __future__ import annotations

import hashlib, json, math, os, platform, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
CELLS = ((1000, "chain", 1), (10000, "chain", 16), (50000, "chain", 128),
         (10000, "star_hub", 1), (50000, "star_hub", 1), (50000, "star_leaves", 128))
REPEATS = 5
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_full_reground_scale_v1.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_FULL_REGROUND_SCALE_V1_PREREG_20261001.md",
    "domains/imagination.py", "runners/dsl/src/py.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_full_reground_scale_v1.json"

def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def make_case(node_count: int, topology: str, deletion_count: int):
    from substrate_rs import NodeID, Substrate
    from domains.imagination import DetachedCollapse
    sub = Substrate()
    node_ids = [sub.add_node("State", {"ordinal": i}) for i in range(node_count)]
    if topology == "chain":
        for i in range(node_count - 1):
            sub.add_edge_unchecked(node_ids[i], "next", node_ids[i + 1], {"ordinal": i})
        targets = [((i + 1) * node_count // (deletion_count + 1))
                   for i in range(deletion_count)]
    elif topology in {"star_hub", "star_leaves"}:
        for i in range(1, node_count):
            sub.add_edge_unchecked(node_ids[0], "spoke", node_ids[i], {"ordinal": i})
        targets = [0] if topology == "star_hub" else [i + 1 for i in range(deletion_count)]
    else:
        raise ValueError(topology)
    imagination = sub.add_node("Imagination", {"status": "imagining"})
    conclusions = []
    validated_edges = 0
    for ordinal, node_index in enumerate(targets):
        nid = node_ids[node_index]
        node = sub.node(nid)
        incident = sub.incident_edges(nid)
        validated_edges += len(incident)
        cid = sub.add_node("ImaginedConclusion", {
            "kind": "node_removed", "detached_id": nid.value,
            "node_type_before": node["type"], "attrs_before": node["attrs"],
            "incident_edges_before": incident, "status": "pending", "reason": "",
            "ordinal": ordinal,
        })
        conclusions.append(cid)
    detached = DetachedCollapse(
        detached=None, imagination_node=imagination, conclusion_nodes=conclusions,
        focus_nodes=None, hypothesis=None, hyp_map={}, cut_grounding=False,
        grounding_cut_count=0, steps_run=0, steps_budget=0, converged=True,
        conclusions={}, derived_only={}, n_conclusions=len(conclusions),
        residual=0.0, confidence=1.0, phase_timings_ms={},
    )
    return sub, detached, validated_edges

def worker() -> dict:
    from domains.imagination import reground
    cells = []
    for node_count, topology, deletion_count in CELLS:
        sub, detached, validated_edges = make_case(node_count, topology, deletion_count)
        samples = []
        parity = True
        for _ in range(REPEATS):
            start = time.perf_counter_ns()
            result = reground(sub, detached)
            samples.append((time.perf_counter_ns() - start) / 1e6)
            parity = parity and (len(result["survivors"]) == deletion_count
                and len(result["discarded"]) == 0
                and len(result["detail"]) == deletion_count
                and all(item["survived"] for item in result["detail"]))
        ordered = sorted(samples)
        cells.append({"nodes": node_count, "topology": topology,
            "deletion_conclusions": deletion_count, "validated_incident_edges": validated_edges,
            "graph_edges": sub.edge_count(), "oracle_parity": parity,
            "median_ms": statistics.median(samples),
            "p95_ms_nearest_rank": ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)],
            "samples_ms": samples})
    return {"pid": os.getpid(), "cells": cells}

def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--worker":
        print(json.dumps(worker(), sort_keys=True, separators=(",", ":")))
        return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    workers = []
    for _ in range(3):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
            cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(proc.stderr[-4000:])
        workers.append(json.loads(proc.stdout))
    aggregates = []
    for index, (node_count, topology, deletion_count) in enumerate(CELLS):
        rows = [worker["cells"][index] for worker in workers]
        medians = [row["median_ms"] for row in rows]
        aggregates.append({"nodes": node_count, "topology": topology,
            "deletion_conclusions": deletion_count,
            "validated_incident_edges": rows[0]["validated_incident_edges"],
            "median_of_worker_medians_ms": statistics.median(medians),
            "p95_of_worker_medians_ms": sorted(medians)[max(0, math.ceil(.95 * len(medians)) - 1)],
            "all_oracles_pass": all(row["oracle_parity"] for row in rows)})
    import substrate_rs as srs
    binary = Path(srs._native.__file__).resolve()
    capture = {"schema": "ThoughtexperimentFullRegroundScaleV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "source_sha256": {name: sha_file(ROOT / name) for name in SOURCES},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "worker_count": len(workers), "workers": workers, "aggregates": aggregates,
        "checks": {"three_fresh_workers": len({worker["pid"] for worker in workers}) == 3,
                   "all_oracles_pass": all(row["all_oracles_pass"] for row in aggregates)}}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": capture["checks"], "aggregates": aggregates}, indent=2))
    return 0 if all(capture["checks"].values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
