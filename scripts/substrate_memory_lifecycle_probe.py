#!/usr/bin/env python3
"""Measure current native long-term-memory page-out/restart behavior.

Uses a unique temporary directory and one synthetic record with an incident
graph edge. It does not modify the demo's fixed /tmp store or build artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
from time import perf_counter_ns
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402
from domains.long_term_memory import LongTermMemory  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cell(n_records: int, replicate: int, interleave: bool = True) -> dict:
    build_manifest = json.loads(
        (ROOT / "runners/dsl/python/substrate_rs/_native.build.json").read_text()
    )
    extension_hash = sha256(ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so")
    with tempfile.TemporaryDirectory(prefix="substrate-memory-lifecycle-") as store:
        sub = srs.Substrate()
        sub.memory_set_hot_window(0)
        anchor = sub.add_node("ProbeAnchor", {"name": "external-reference"})
        vector = [1.0, 2.0, 3.0]
        original_nodes = {}
        t0 = perf_counter_ns()
        for i in range(n_records):
            key = f"probe-{i:04d}"
            record = sub.add_node("MemoryRecord", {
                "record_key": key, "round": 0, "new_signs": i + 1,
                "note": "attribute payload survives if decoded",
            })
            original_nodes[key] = record
            sub.add_edge_unchecked(anchor, "references", record, {})
            if i:
                sub.add_edge_unchecked(previous, "next_record", record, {})
            previous = record
        build_graph_ns = perf_counter_ns() - t0

        t0 = perf_counter_ns()
        for i in range(n_records):
            key = f"probe-{i:04d}"
            record = original_nodes[key]
            cluster = sub.memory_consolidate(store, key, record, 0, vector, vector)
        consolidate_ns = perf_counter_ns() - t0

        t0 = perf_counter_ns()
        evicted = sub.memory_shuffle(1)
        pageout_ns = perf_counter_ns() - t0
        original_nodes_after_pageout = sum(
            sub.has_node(node_id) for node_id in original_nodes.values()
        )
        external_edges_after_pageout = sum(
            sub.has_edge(anchor, "references", node_id)
            for node_id in original_nodes.values()
        )

        # Consume some freed IDs before recall, so ID restoration is tested
        # under allocation pressure rather than only in the one-record case.
        t0 = perf_counter_ns()
        n_interleaved = n_records if interleave else 0
        for i in range(n_interleaved):
            sub.add_node("InterleavedAllocation", {"ordinal": i})
        interleave_ns = perf_counter_ns() - t0

        t0 = perf_counter_ns()
        recall = sub.memory_recall_by_shape(vector, vector, 2)
        recall_ns = perf_counter_ns() - t0
        restored_by_key = {}
        for restored in sub.nodes("MemoryRecord"):
            attrs = sub.node(restored)["attrs"]
            restored_by_key[attrs["record_key"]] = restored.value
        same_id_count = sum(
            restored_by_key.get(key) == node_id.value
            for key, node_id in original_nodes.items()
        )
        external_edges_after_recall = sum(
            sub.has_edge(anchor, "references", node_id)
            for node_id in original_nodes.values()
        )
        chain_edges_after_recall = sum(
            sub.has_edge(original_nodes[f"probe-{i:04d}"], "next_record",
                         original_nodes[f"probe-{i + 1:04d}"])
            for i in range(n_records - 1)
        )

        fresh = srs.Substrate()
        restart_recall = fresh.memory_recall_by_shape(vector, vector, 2)
        index_clusters_after_restart = fresh.memory_index_clusters()
        persisted_paths = sorted(str(p.relative_to(store)) for p in Path(store).glob("*.json"))
        adapter = LongTermMemory(store)
        exact_key_recall = adapter.recall(fresh, "probe-0000", 3)
        store_bytes = sum(p.stat().st_size for p in Path(store).glob("*.json"))

        return {
            "n_records": n_records,
            "replicate": replicate,
            "interleaved_allocations": n_interleaved,
            "same_substrate": {
                "index_clusters_before_pageout": 1,
                "evicted_clusters": evicted,
                "original_nodes_present_after_pageout": original_nodes_after_pageout,
                "external_edges_present_after_pageout": external_edges_after_pageout,
                "shape_recall": list(recall) if recall is not None else None,
                "records_restored": len(restored_by_key),
                "same_record_id_count_after_interleaved_allocations": same_id_count,
                "external_edges_restored": external_edges_after_recall,
                "chain_edges_restored": chain_edges_after_recall,
            },
            "fresh_substrate": {
                "record_files_present": len(persisted_paths),
                "store_bytes": store_bytes,
                "shape_index_clusters": index_clusters_after_restart,
                "shape_recall": list(restart_recall) if restart_recall is not None else None,
                "exact_key_recall": exact_key_recall,
            },
            "timing_ns": {
                "graph_setup": build_graph_ns,
                "consolidate_all": consolidate_ns,
                "pageout": pageout_ns,
                "interleaved_allocations": interleave_ns,
                "pagein_all": recall_ns,
            },
            "provenance": {
                "repo_head": subprocess.run(
                    ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                    check=True, capture_output=True, text=True,
                ).stdout.strip(),
                "native_extension": "runners/dsl/python/substrate_rs/_native.abi3.so",
                "native_extension_sha256": extension_hash,
                "native_extension_matches_build_manifest": extension_hash == build_manifest.get("engine_sha256"),
                "rust_memory_source_sha256": sha256(ROOT / "runners/dsl/src/memory.rs"),
            },
        }


def run() -> dict:
    cells = [run_cell(n, r) for n in (1, 8, 32, 64) for r in range(1, 4)]
    no_interleave_control = run_cell(1, 0, interleave=False)
    process_restart = run_process_restart_probe()
    by_size = {}
    for n in (1, 8, 32, 64):
        rows = [c for c in cells if c["n_records"] == n]
        by_size[str(n)] = {
            "replicates": len(rows),
            "all_records_pagein": [r["same_substrate"]["records_restored"] == n for r in rows],
            "same_id_counts": [r["same_substrate"]["same_record_id_count_after_interleaved_allocations"] for r in rows],
            "external_edges_restored": [r["same_substrate"]["external_edges_restored"] for r in rows],
            "chain_edges_restored": [r["same_substrate"]["chain_edges_restored"] for r in rows],
            "pagein_median_ms": round(statistics.median(r["timing_ns"]["pagein_all"] for r in rows) / 1e6, 4),
            "consolidate_median_ms": round(statistics.median(r["timing_ns"]["consolidate_all"] for r in rows) / 1e6, 4),
            "store_bytes": [r["fresh_substrate"]["store_bytes"] for r in rows],
            "restart_index_empty_all": all(r["fresh_substrate"]["shape_index_clusters"] == 0 for r in rows),
        }
    return {
            "schema_version": 2,
            "probe": "multi-record page-out/page-in and fresh-substrate restart analogue",
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "sizes": [1, 8, 32, 64],
            "replicates_per_size": 3,
            "summary_by_size": by_size,
            "single_record_no_interleave_control": no_interleave_control,
            "actual_process_restart": process_restart,
            "runs": cells,
            "provenance": {
                **cells[0]["provenance"],
                "build_manifest_sha256": sha256(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
                "adapter_source_sha256": sha256(ROOT / "domains/long_term_memory.py"),
                "probe_source_sha256": sha256(ROOT / "scripts/substrate_memory_lifecycle_probe.py"),
                "python": sys.version,
                "platform": platform.platform(),
                "logical_cpu_count": os.cpu_count(),
                "worktree_dirty": bool(subprocess.run(
                    ["git", "-C", str(ROOT), "status", "--porcelain"],
                    check=True, capture_output=True, text=True,
                ).stdout.strip()),
                "audited_rust_and_adapter_sources_clean": subprocess.run(
                    ["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--",
                     "runners/dsl/src/memory.rs", "domains/long_term_memory.py"],
                    check=False,
                ).returncode == 0,
            },
            "command": "PYTHONPATH=runners/dsl/python:. OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_memory_lifecycle_probe.py --output evaluation/reports/substrate_memory_lifecycle_20260925.json",
            "limits": [
                "Synthetic records share one category-shape cluster; sizes are small and do not represent an application memory workload.",
                "Each replicate uses an independent substrate and a unique TemporaryDirectory, removed automatically after the cell.",
                "The process restart probe covers one record; the size sweep itself remains in-process with independent substrate instances.",
            ],
    }


def run_process_restart_probe() -> dict:
    with tempfile.TemporaryDirectory(prefix="substrate-memory-restart-") as store:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join([
            str(ROOT / "runners/dsl/python"), str(ROOT), str(ROOT / "scripts"),
        ])
        common = [sys.executable, str(ROOT / "scripts/substrate_memory_lifecycle_probe.py"),
                  "--phase"]
        writer = subprocess.run(
            common + ["write", "--store-dir", store], cwd=ROOT, env=env,
            check=True, capture_output=True, text=True,
        )
        reader = subprocess.run(
            common + ["read", "--store-dir", store], cwd=ROOT, env=env,
            check=True, capture_output=True, text=True,
        )
        return {
            "writer_pid": int(json.loads(writer.stdout)["pid"]),
            "reader_pid": int(json.loads(reader.stdout)["pid"]),
            **json.loads(reader.stdout),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--phase", choices=("write", "read"), help=argparse.SUPPRESS)
    parser.add_argument("--store-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.phase:
        if args.store_dir is None:
            parser.error("--store-dir is required with --phase")
        if args.phase == "write":
            sub = srs.Substrate()
            node = sub.add_node("MemoryRecord", {
                "record_key": "process-restart-probe", "new_signs": 7,
                "note": "must be recovered after process exit",
            })
            vector = [1.0, 2.0, 3.0]
            cluster = sub.memory_consolidate(
                str(args.store_dir), "process-restart-probe", node, 0, vector, vector
            )
            result = {"pid": os.getpid(), "cluster_id": cluster,
                      "files": [p.name for p in args.store_dir.glob("*.json")]}
        else:
            sub = srs.Substrate()
            vector = [1.0, 2.0, 3.0]
            recalled = sub.memory_recall_by_shape(vector, vector, 1)
            result = {"pid": os.getpid(),
                      "files": [p.name for p in args.store_dir.glob("*.json")],
                      "index_clusters": sub.memory_index_clusters(),
                      "shape_recall": list(recalled) if recalled is not None else None}
        print(json.dumps(result))
        return
    result = run()
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
        print(args.output)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
