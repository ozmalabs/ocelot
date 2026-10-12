#!/usr/bin/env python3
"""Fresh-process scale envelope for durable long-term memory index restore."""
from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.long_term_memory import LongTermMemory  # noqa: E402
from substrate_rs import Substrate  # noqa: E402

SIZES = (1, 10, 100, 1000, 5000)
REPEATS = 3
PERMUTATIONS = ((1, 2, 3), (1, 3, 2), (2, 1, 3), (2, 3, 1), (3, 1, 2), (3, 2, 1))


def expected_attrs(i: int) -> dict:
    a, b, c = PERMUTATIONS[i % len(PERMUTATIONS)]
    return {"new_signs": a, "utts": b, "round": c, "record_index": i}


def writer(store: Path, count: int) -> dict:
    s = Substrate()
    memory = LongTermMemory(str(store), hot_window=5)
    start = time.perf_counter()
    for i in range(count):
        node = s.add_node("MemoryRecord", expected_attrs(i))
        memory.consolidate(s, f"scale-record-{i:06d}", node, i)
    return {"pid": os.getpid(), "count": count,
            "write_seconds": time.perf_counter() - start,
            "files": len(list(store.glob("*.json"))),
            "bytes": sum(p.stat().st_size for p in store.glob("*.json")),
            "clusters": s.memory_index_clusters()}


def reader(store: Path, count: int) -> dict:
    s = Substrate()
    memory = LongTermMemory(str(store), hot_window=5)
    started = time.perf_counter()
    memory._bind(s)
    bind_seconds = time.perf_counter() - started
    cluster_keys: dict[str, int] = {}
    for i in range(count):
        attrs = expected_attrs(i)
        key = (f"{attrs['new_signs']},{attrs['utts']},{attrs['round']}")
        cluster_keys.setdefault(key, i)
    checks = []
    recall_start = time.perf_counter()
    for i in cluster_keys.values():
        key = f"scale-record-{i:06d}"
        nid = memory.recall(s, key, count + 1)
        attrs = s.node(nid)["attrs"] if nid is not None else None
        checks.append(attrs == expected_attrs(i))
    recall_seconds = time.perf_counter() - recall_start
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"pid": os.getpid(), "count": count,
            "bind_seconds": bind_seconds,
            "recall_seconds_for_one_key_per_shape": recall_seconds,
            "restored_keys": len(memory._known),
            "clusters": s.memory_index_clusters(),
            "representative_recalls": len(checks),
            "all_representative_attrs_match": all(checks),
            "node_count_after_recall": s.node_count(),
            "edge_count_after_recall": s.edge_count(),
            "max_rss_kib": usage}


def run_child(mode: str, store: Path, count: int) -> dict:
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                             "--child", mode, "--store", str(store),
                             "--count", str(count)], cwd=ROOT, text=True,
                            capture_output=True, check=True)
    return json.loads(result.stdout)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        mode = sys.argv[2]
        store = Path(sys.argv[sys.argv.index("--store") + 1])
        count = int(sys.argv[sys.argv.index("--count") + 1])
        print(json.dumps(writer(store, count) if mode == "writer" else reader(store, count)))
        return
    results = []
    total_start = time.perf_counter()
    for count in SIZES:
        for repeat in range(REPEATS):
            with tempfile.TemporaryDirectory(prefix=f"ocelot-memory-scale-{count}-") as temp:
                store = Path(temp) / "records"
                store.mkdir()
                wall_start = time.perf_counter()
                write = run_child("writer", store, count)
                read = run_child("reader", store, count)
                results.append({"count": count, "repeat": repeat + 1,
                                "write": write, "read": read,
                                "two_process_wall_seconds": time.perf_counter() - wall_start})
    payload = {"probe": "substrate-memory-restart-scale-v1",
               "sizes": list(SIZES), "repeats": REPEATS,
               "total_wall_seconds": time.perf_counter() - total_start,
               "results": results}
    out = ROOT / "evaluation/reports/substrate_memory_restart_scale_20260925.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
