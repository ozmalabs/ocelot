#!/usr/bin/env python3
"""Measure durable shape recall quality under rank-preserving and magnitude shifts."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_memory_shape_quality_pilot_20260925.json"
FEATURES = ("new_signs", "utts", "round")
SCALES = (1.0, 100.0)
REPLICATES = 3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rank_label(values):
    ordered = sorted(FEATURES, key=lambda k: values[k])
    return "<".join(ordered)


def build_records_and_queries():
    records, queries = [], []
    for perm in itertools.permutations(FEATURES):
        rank_values = {name: float(i + 1) for i, name in enumerate(perm)}
        label = rank_label(rank_values)
        for scale in SCALES:
            magnitude = "high" if scale > 1 else "low"
            for rep in range(REPLICATES):
                offset = rep * 0.1
                values = {k: rank_values[k] * scale + offset for k in FEATURES}
                key = f"{label}|{magnitude}|{rep}"
                records.append({
                    "key": key, "attrs": {
                        **values, "record_key": key, "rank_label": label,
                        "magnitude_label": magnitude, "replicate": rep,
                    },
                    "rank_label": label, "magnitude_label": magnitude,
                })
        for scale in SCALES:
            values = {k: rank_values[k] * scale + 0.05 for k in FEATURES}
            queries.append({
                "query_id": f"{label}|{'high' if scale > 1 else 'low'}",
                "attrs": values, "rank_label": label,
                "magnitude_label": "high" if scale > 1 else "low",
                "exact_key": f"{label}|{'high' if scale > 1 else 'low'}|1",
            })
    return records, queries


def child(mode, store_dir, payload):
    from substrate_rs import Substrate
    from domains.long_term_memory import LongTermMemory

    s = Substrate()
    memory = LongTermMemory(str(store_dir), hot_window=1)
    t0 = time.perf_counter_ns()
    memory._bind(s)
    bind_ns = time.perf_counter_ns() - t0
    if mode == "shape":
        t0 = time.perf_counter_ns()
        result = memory.recall_by_shape(s, payload["attrs"], 10000)
        recall_ns = time.perf_counter_ns() - t0
        items = []
        for nid in s.nodes(type="MemoryRecord"):
            attrs = s.node(nid)["attrs"]
            items.append((attrs.get("record_key"), attrs.get("rank_label"),
                          attrs.get("magnitude_label")))
        items.sort()
        return {
            "mode": mode, "query_id": payload["query_id"], "bind_ns": bind_ns,
            "recall_ns": recall_ns, "shape_result": result, "candidates": items,
            "restore": memory.stats()["restore"],
        }
    if mode == "exact":
        t0 = time.perf_counter_ns()
        nid = memory.recall(s, payload["exact_key"], 10000)
        recall_ns = time.perf_counter_ns() - t0
        node = s.node(nid) if nid is not None else None
        attrs = node["attrs"] if node is not None else {}
        return {
            "mode": mode, "query_id": payload["query_id"], "bind_ns": bind_ns,
            "recall_ns": recall_ns, "found": nid is not None,
            "record_key": attrs.get("record_key"),
            "rank_label": attrs.get("rank_label"),
            "magnitude_label": attrs.get("magnitude_label"),
            "restore": memory.stats()["restore"],
        }
    raise ValueError(mode)


def main():
    if len(sys.argv) == 5 and sys.argv[1] == "--child":
        mode, store, payload = sys.argv[2], Path(sys.argv[3]), json.loads(sys.argv[4])
        print(json.dumps(child(mode, store, payload), sort_keys=True))
        return

    import substrate_rs as sr
    from domains.long_term_memory import LongTermMemory

    records, queries = build_records_and_queries()
    worker_records = []
    with tempfile.TemporaryDirectory(prefix="substrate-memory-quality-") as temp:
        store = Path(temp) / "records"
        store.mkdir()
        s = sr.Substrate()
        memory = LongTermMemory(str(store), hot_window=1)
        for i, rec in enumerate(records):
            nid = s.add_node("MemoryRecord", rec["attrs"])
            memory.consolidate(s, rec["key"], nid, i + 1)
        shuffle_result = memory.shuffle(s, 10000)
        evicted = shuffle_result["evicted_clusters"]
        resident_after_shuffle = sum(1 for _ in s.nodes(type="MemoryRecord"))
        if resident_after_shuffle != 0:
            raise AssertionError("fixture records were not fully paged out")
        files = sorted(p.name for p in store.glob("*.json"))
        if len(files) != len(records):
            raise AssertionError("durable record count differs from fixture count")

        env = dict(os.environ)
        env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
        for query in queries:
            for mode in ("shape", "exact"):
                proc = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()), "--child",
                     mode, str(store), json.dumps(query, sort_keys=True)],
                    cwd=ROOT, env=env, text=True, capture_output=True, check=True)
                worker_records.append(json.loads(proc.stdout.strip()))

    by_query = {}
    for row in worker_records:
        by_query.setdefault(row["query_id"], {})[row["mode"]] = row
    scored = []
    for query in queries:
        pair = by_query[query["query_id"]]
        shape, exact = pair["shape"], pair["exact"]
        candidates = shape["candidates"]
        rank_hits = sum(label == query["rank_label"] for _, label, _ in candidates)
        magnitude_hits = sum(label == query["magnitude_label"] for _, _, label in candidates)
        shape_rank_precision = rank_hits / len(candidates) if candidates else 0.0
        shape_magnitude_precision = magnitude_hits / len(candidates) if candidates else 0.0
        exact_correct = (exact["found"] and exact["record_key"] == query["exact_key"] and
                         exact["rank_label"] == query["rank_label"] and
                         exact["magnitude_label"] == query["magnitude_label"])
        scored.append({
            "query_id": query["query_id"], "expected_rank_label": query["rank_label"],
            "expected_magnitude_label": query["magnitude_label"],
            "shape_cluster_id": (shape["shape_result"] or {}).get("cluster_id"),
            "shape_candidate_count": len(candidates),
            "shape_rank_precision": shape_rank_precision,
            "shape_magnitude_precision": shape_magnitude_precision,
            "shape_recall_all_records_in_rank_cluster": rank_hits == 6 and len(candidates) == 6,
            "exact_key_correct": bool(exact_correct),
            "shape_bind_ns": shape["bind_ns"], "shape_recall_ns": shape["recall_ns"],
            "exact_bind_ns": exact["bind_ns"], "exact_recall_ns": exact["recall_ns"],
            "shape_restore": shape["restore"], "exact_restore": exact["restore"],
        })

    source_files = [
        Path(__file__).resolve(), ROOT / "domains/long_term_memory.py",
        ROOT / "runners/dsl/src/memory.rs", ROOT / "runners/dsl/src/py.rs",
        ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
        ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
        ROOT / "runners/dsl/Cargo.lock",
    ]
    payload = {
        "schema_version": 1,
        "run_id": "substrate-memory-shape-quality-pilot-20260925-v1",
        "scope": "fresh-process durable long-term shape recall on a controlled six-rank-class dataset with low/high magnitude labels",
        "claim_boundary": "Synthetic adapter-level retrieval pilot. Rank labels are deliberately aligned with the ordinal-shape feature representation; magnitude labels are deliberately not. It is not natural-task memory utility, retrieval against learned semantics, or broad long-term-memory efficacy.",
        "configuration": {"rank_classes": 6, "magnitude_classes_per_rank": 2,
                          "stored_replicates_per_class": REPLICATES,
                          "stored_record_count": len(records), "queries": len(queries),
                          "arms": ["shape_recall", "exact_key_control"],
                          "writer_shuffle_evicted_clusters": len(evicted),
                          "resident_records_after_shuffle": resident_after_shuffle},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor()},
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in source_files},
        "checks": {
            "all_shape_queries_return_six_records": all(r["shape_candidate_count"] == 6 for r in scored),
            "rank_shape_recall_is_exact": all(r["shape_recall_all_records_in_rank_cluster"] for r in scored),
            "magnitude_collision_is_observed": all(abs(r["shape_magnitude_precision"] - 0.5) < 1e-12
                                                   for r in scored),
            "all_exact_key_queries_correct": all(r["exact_key_correct"] for r in scored),
            "all_readers_reindex_all_records": all(r["shape_restore"]["indexed"] == len(records) and
                                                    r["exact_restore"]["indexed"] == len(records)
                                                    for r in scored),
            "all_written_records_paged_out": resident_after_shuffle == 0 and
                len(evicted) == 6 and len(files) == len(records),
        },
        "summary": {
            "query_count": len(scored),
            "rank_shape_precision_mean": statistics.mean(r["shape_rank_precision"] for r in scored),
            "magnitude_precision_mean": statistics.mean(r["shape_magnitude_precision"] for r in scored),
            "exact_key_accuracy": statistics.mean(r["exact_key_correct"] for r in scored),
            "median_shape_bind_ms": statistics.median(r["shape_bind_ns"] for r in scored) / 1e6,
            "median_shape_recall_ms": statistics.median(r["shape_recall_ns"] for r in scored) / 1e6,
            "median_exact_bind_ms": statistics.median(r["exact_bind_ns"] for r in scored) / 1e6,
            "median_exact_recall_ms": statistics.median(r["exact_recall_ns"] for r in scored) / 1e6,
        },
        "queries": scored,
        "dataset_record_metadata": [
            {k: v for k, v in rec.items() if k != "attrs"} for rec in records
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"queries": len(scored), "checks": payload["checks"],
                      "summary": payload["summary"], "output": str(OUT)}, indent=2))
    if not all(payload["checks"].values()):
        raise SystemExit("memory shape-quality invariant failed")


if __name__ == "__main__":
    main()
