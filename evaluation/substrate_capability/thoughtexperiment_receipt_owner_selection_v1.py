#!/usr/bin/env python3
"""Check whether sorted receipt adoption changes a first-owner consumer."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
OUT = ROOT / "evaluation/reports/thoughtexperiment_receipt_owner_selection_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_RECEIPT_OWNER_SELECTION_V1_PREREG_20261001.md"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_RECEIPT_OWNER_SELECTION_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_receipt_owner_selection_v1.py",
    "domains/implication_harvester.py", "runners/dsl/src/graph.rs",
    "runners/dsl/src/persist.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)
WORKERS = 8


def fingerprint() -> dict:
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in SOURCES}


def worker() -> dict:
    from substrate_rs import Substrate
    from domains.implication_harvester import _owning_mt_map

    primary = Substrate()
    mt_a = primary.add_node("Microtheory", {"name": "mt_a"})
    mt_b = primary.add_node("Microtheory", {"name": "mt_b"})
    concept = primary.add_node("Concept", {"name": "shared_concept"})
    revision = primary.experiment_graph_rule_revision()
    snapshot = primary.snapshot()

    direct = snapshot.fork()
    direct.add_edge_unchecked(mt_b, "has_concept", concept, {})
    direct.add_edge_unchecked(mt_a, "has_concept", concept, {})

    branch = snapshot.fork()
    branch.begin_experiment_delta_journal()
    branch.add_edge_unchecked(mt_b, "has_concept", concept, {})
    branch.add_edge_unchecked(mt_a, "has_concept", concept, {})
    receipt = branch.finish_experiment_delta_journal()["conclusions"]
    primary.apply_experiment_graph_delta(revision, receipt)

    direct_edges = direct.graph_to_dict()["edges"]
    adopted_edges = primary.graph_to_dict()["edges"]
    edge_key = lambda row: (row["src"], row["type"], row["tgt"], row.get("attrs", {}))
    direct_owner = _owning_mt_map(direct).get("shared_concept")
    adopted_owner = _owning_mt_map(primary).get("shared_concept")
    return {
        "pid": os.getpid(), "revision": list(revision),
        "receipt_added": receipt["edges_added"],
        "direct_edge_order": [edge_key(row) for row in direct_edges],
        "adopted_edge_order": [edge_key(row) for row in adopted_edges],
        "canonical_edge_parity": sorted(map(repr, map(edge_key, direct_edges)))
            == sorted(map(repr, map(edge_key, adopted_edges))),
        "direct_owner": direct_owner, "adopted_owner": adopted_owner,
    }


def main() -> None:
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(), sort_keys=True))
        return
    before = fingerprint()
    rows = []
    for _ in range(WORKERS):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
                              cwd=ROOT, env={**os.environ, "PYTHONPATH":
                                             f"{ROOT / 'runners/dsl/python'}:{ROOT}"},
                              check=True, text=True, capture_output=True)
        rows.append(json.loads(proc.stdout))
    after = fingerprint()
    result = {
        "protocol": PROTOCOL.name, "captured_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "source_stable": before == after,
        "source_before": before, "source_after": after, "workers": rows,
        "gates": {
            "eight_fresh_pids": len({row["pid"] for row in rows}) == WORKERS,
            "canonical_edge_parity": all(row["canonical_edge_parity"] for row in rows),
            "two_sorted_receipt_additions": all(
                len(row["receipt_added"]) == 2 and
                [edge["src"] for edge in row["receipt_added"]] == [0, 1]
                for row in rows),
            "owner_changes_direct_to_adopted": all(
                row["direct_owner"] != row["adopted_owner"] for row in rows),
            "source_stable": before == after,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
                      "worker_count": len(rows)}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("receipt owner-selection diagnostic gate failed")


if __name__ == "__main__":
    main()
