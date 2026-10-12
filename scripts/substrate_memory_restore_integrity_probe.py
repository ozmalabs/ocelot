#!/usr/bin/env python3
"""Probe duplicate-key refusal and malformed-record skipping on adapter restore."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.long_term_memory import LongTermMemory  # noqa: E402
from substrate_rs import Substrate  # noqa: E402


def child(mode: str, store: Path) -> dict:
    if mode == "writer":
        s = Substrate()
        m = LongTermMemory(str(store))
        dup_attrs = {"new_signs": 1, "utts": 2, "round": 3, "label": "first"}
        unique_attrs = {"new_signs": 3, "utts": 2, "round": 1, "label": "unique"}
        dup_node = s.add_node("MemoryRecord", dup_attrs)
        unique_node = s.add_node("MemoryRecord", unique_attrs)
        m.consolidate(s, "ambiguous-key", dup_node, 3)
        m.consolidate(s, "unique-key", unique_node, 4)
        dup_path = store / "ambiguous-key.json"
        duplicate = json.loads(dup_path.read_text())
        duplicate["attrs"] = {**duplicate["attrs"], "new_signs": 3,
                              "utts": 2, "round": 1, "label": "conflict"}
        (store / "zz-conflict.json").write_text(json.dumps(duplicate))
        (store / "bad-json.json").write_text("{broken")
        (store / "missing-attrs.json").write_text(json.dumps({"key": "broken", "round": 0}))
        return {"mode": mode, "pid": os.getpid(),
                "files": sorted(p.name for p in store.glob("*.json"))}

    s = Substrate()
    m = LongTermMemory(str(store))
    m._bind(s)
    duplicate = m.recall(s, "ambiguous-key", 10)
    unique = m.recall(s, "unique-key", 10)
    unique_attrs = s.node(unique)["attrs"] if unique is not None else None
    return {"mode": mode, "pid": os.getpid(),
            "known_unique": m.findable("unique-key"),
            "known_ambiguous": m.findable("ambiguous-key"),
            "duplicate_recall_is_none": duplicate is None,
            "unique_attrs_match": unique_attrs == {
                "new_signs": 3, "utts": 2, "round": 1, "label": "unique"},
            "stats": m.stats(), "nodes": s.node_count(), "edges": s.edge_count()}


def main() -> None:
    results = []
    with tempfile.TemporaryDirectory(prefix="ocelot-memory-integrity-") as temp:
        store = Path(temp) / "records"
        store.mkdir()
        for mode in ("writer", "reader"):
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                                   "--child", mode, "--store", str(store)],
                                  cwd=ROOT, text=True, capture_output=True,
                                  check=True)
            results.append(json.loads(proc.stdout))
    print(json.dumps({"probe": "substrate-memory-restore-integrity-v1",
                      "results": results}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        print(json.dumps(child(sys.argv[2], Path(sys.argv[4]))))
    else:
        main()
