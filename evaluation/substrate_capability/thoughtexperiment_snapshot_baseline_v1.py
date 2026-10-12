#!/usr/bin/env python3
"""Measure the current detached-graph snapshot path used by imagination.

This is the baseline for the proposed Rust thoughtexperiment harness, not a
CoW implementation. It times the native graph export and restore separately
and together on deterministic sparse attributed graphs. Output is a JSON
capture with source/binary locks so a later branch implementation can be
compared on the same workload and host.

Example:
  python3 evaluation/substrate_capability/thoughtexperiment_snapshot_baseline_v1.py \
      --sizes 1000 10000 100000 --repeats 9 --out evaluation/reports/thoughtexperiment_snapshot_baseline_v1.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

import substrate_rs as srs  # noqa: E402


LOCKED_SOURCES = (
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/persist.rs",
    "runners/dsl/src/py.rs",
    "domains/imagination.py",
    "domains/self_correction.py",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return "sha256:" + h.hexdigest()


def make_graph(n_nodes: int):
    native = srs.Substrate()
    nodes = [native.add_node(
        "ThoughtexperimentBenchNode",
        {"ordinal": i, "partition": i % 32, "payload": "x" * 24},
    ) for i in range(n_nodes)]
    for i in range(n_nodes):
        if i + 1 < n_nodes:
            native.add_edge_unchecked(nodes[i], "bench_next", nodes[i + 1])
        if i + 8 < n_nodes:
            native.add_edge_unchecked(nodes[i], "bench_skip8", nodes[i + 8])
    return native


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def summarize(values: list[float]) -> dict:
    return {
        "median_ms": statistics.median(values) * 1_000.0,
        "p95_ms": percentile(values, 0.95) * 1_000.0,
        "min_ms": min(values) * 1_000.0,
        "max_ms": max(values) * 1_000.0,
    }


def measure(n_nodes: int, repeats: int, warmups: int) -> dict:
    primary = make_graph(n_nodes)
    target = srs.Substrate()
    export_s: list[float] = []
    import_s: list[float] = []
    total_s: list[float] = []
    payload_bytes = 0
    observed_nodes = observed_edges = None

    for iteration in range(warmups + repeats):
        t0 = time.perf_counter()
        snapshot = primary.graph_to_dict()
        t1 = time.perf_counter()
        target.graph_from_dict(snapshot)
        t2 = time.perf_counter()
        if iteration >= warmups:
            export_s.append(t1 - t0)
            import_s.append(t2 - t1)
            total_s.append(t2 - t0)
            payload_bytes = len(json.dumps(snapshot, separators=(",", ":"),
                                           sort_keys=True).encode("utf-8"))
            observed_nodes = len(snapshot["nodes"])
            observed_edges = len(snapshot["edges"])

    return {
        "requested_nodes": n_nodes,
        "observed_nodes": observed_nodes,
        "observed_edges": observed_edges,
        "json_payload_bytes": payload_bytes,
        "repeats": repeats,
        "warmups": warmups,
        "export": summarize(export_s),
        "restore": summarize(import_s),
        "export_plus_restore": summarize(total_s),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int,
                        default=[1_000, 10_000, 50_000])
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0 or any(n < 0 for n in args.sizes):
        parser.error("repeats must be positive; warmups and sizes must be nonnegative")

    binary_path = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentSnapshotBaselineV1",
        "measurement": "native_graph_to_dict_plus_graph_from_dict",
        "implementation_status": "serialization_copy_baseline; no CoW fork",
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
            "pid": os.getpid(),
        },
        "binary": {"path": str(binary_path), "sha256": sha256(binary_path)},
        "runner": {"path": str(Path(__file__).resolve()),
                   "sha256": sha256(Path(__file__).resolve())},
        "sources": {name: sha256(ROOT / name) for name in LOCKED_SOURCES},
        "workload": {
            "node_type": "ThoughtexperimentBenchNode",
            "attrs_per_node": 3,
            "edges": "chain plus forward skip-8; max out-degree 2",
            "payload_attr_bytes": 24,
        },
        "results": [measure(n, args.repeats, args.warmups) for n in args.sizes],
    }
    rendered = json.dumps(capture, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
