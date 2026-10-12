#!/usr/bin/env python3
"""Two-process probe for durable attribute recall across substrate restart."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners/dsl/python"))
from domains.long_term_memory import LongTermMemory  # noqa: E402
from substrate_rs import Substrate  # noqa: E402

KEY = "probe-record-001"
ATTRS = {"new_signs": 3, "utts": 7, "round": 11, "label": "durable-probe"}


def child(mode: str, store: Path) -> dict:
    s = Substrate()
    memory = LongTermMemory(str(store), hot_window=1)
    if mode == "writer":
        anchor = s.add_node("Anchor", {"name": "writer-anchor"})
        record = s.add_node("MemoryRecord", ATTRS)
        s.add_edge_unchecked(anchor, "contains_memory", record, {})
        memory.consolidate(s, KEY, record, 11)
        shuffled = memory.shuffle(s, 30)
        return {"mode": mode, "pid": os.getpid(), "shuffled": shuffled,
                "node_count_after_shuffle": s.node_count(),
                "edge_count_after_shuffle": s.edge_count(),
                "record_files": sorted(p.name for p in store.glob("*.json"))}
    if mode in ("reader-key", "reader-shape"):
        memory._bind(s)
        findable_before_recall = memory.findable(KEY)
        if mode == "reader-key":
            nid = memory.recall(s, KEY, 31)
        else:
            memory.recall_by_shape(s, ATTRS, 31)
            nid = s.memory_recall_by_key(KEY, 31)
        record = s.node(nid) if nid is not None else None
        record_attrs = record.get("attrs") if record is not None else None
        return {"mode": mode, "pid": os.getpid(),
                "findable_before_recall": findable_before_recall,
                "clusters": s.memory_index_clusters(),
                "node_count": s.node_count(), "edge_count": s.edge_count(),
                "record_attrs": record_attrs}
    raise ValueError(mode)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", choices=("writer", "reader-key", "reader-shape"))
    parser.add_argument("--store", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.child:
        print(json.dumps(child(args.child, args.store), sort_keys=True))
        return

    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="ocelot-memory-restart-") as temp:
        store = Path(temp) / "records"
        store.mkdir()
        runs = []
        for mode in ("writer", "reader-key", "reader-shape"):
            t0 = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--child", mode,
                 "--store", str(store)], cwd=ROOT, text=True,
                capture_output=True, check=True,
            )
            runs.append({"elapsed_seconds": time.perf_counter() - t0,
                         "result": json.loads(proc.stdout.strip())})
    payload = {"probe": "substrate-memory-restart-recall-v1",
               "wall_seconds": time.perf_counter() - start, "runs": runs}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
