#!/usr/bin/env python3
"""Describe name-level ownership ambiguity in the ordinary full seed boot."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
OUT = ROOT / "evaluation/reports/thoughtexperiment_ownership_order_census_v1_raw_20261001.json"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_OWNERSHIP_ORDER_CENSUS_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_ownership_order_census_v1.py",
    "substrate/boot_all.py", "substrate/boot_core.py", "substrate/world_adapter.py",
    "domains/implication_harvester.py", "runners/dsl/python/substrate_rs/_native.abi3.so",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    seed_paths = sorted((ROOT / "seeds").glob("*.json"))
    seed_hash = hashlib.sha256()
    for path in seed_paths:
        seed_hash.update(path.name.encode())
        seed_hash.update(bytes.fromhex(sha(path)))
    return {
        "files": {name: sha(ROOT / name) for name in SOURCES},
        "seed_file_count": len(seed_paths),
        "seed_json_sha256": seed_hash.hexdigest(),
    }


def main() -> None:
    before = fingerprint()
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    graph = adapter.s.graph_to_dict()
    nodes = {row["id"]: row for row in graph["nodes"]}
    by_id: dict[tuple[str, int], set[int]] = defaultdict(set)
    by_name: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"owners": set(), "targets": set(), "edge_count": 0})
    ownership_edges = 0
    for edge in graph["edges"]:
        edge_type = edge["type"]
        if edge_type not in ("has_concept", "has_rule"):
            continue
        ownership_edges += 1
        source, target = edge["src"], edge["tgt"]
        by_id[(edge_type, target)].add(source)
        child = nodes.get(target, {})
        name = str(child.get("attrs", {}).get("name", "") or "")
        if name:
            group = by_name[(edge_type, name)]
            group["owners"].add(source)
            group["targets"].add(target)
            group["edge_count"] += 1
    ambiguous = {key: row for key, row in by_name.items()
                 if len(row["owners"]) > 1}
    ordered = sorted(ambiguous.items(), key=lambda item: item[0])
    examples = []
    for (edge_type, name), row in ordered[:25]:
        owner_ids = sorted(row["owners"])
        examples.append({
            "edge_type": edge_type, "name": name,
            "owner_ids": owner_ids,
            "owner_names": [nodes.get(i, {}).get("attrs", {}).get("name")
                            for i in owner_ids],
            "target_node_count": len(row["targets"]),
            "edge_count": row["edge_count"],
        })
    after = fingerprint()
    result = {
        "protocol": "THOUGHTEXPERIMENT_OWNERSHIP_ORDER_CENSUS_V1_PREREG_20261001",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "pid": __import__("os").getpid(), "platform": platform.platform(),
        "source_stable": before == after, "source_before": before,
        "source_after": after,
        "boot": {"loaded": boot.get("loaded"),
                 "failed_count": len(boot.get("failed", [])),
                 "failed": boot.get("failed", [])},
        "graph": {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]),
                  "ownership_edges": ownership_edges,
                  "distinct_target_type_pairs": len(by_id),
                  "multiply_owned_target_type_pairs": sum(
                      len(owners) > 1 for owners in by_id.values()),
                  "named_groups": len(by_name),
                  "multiply_owned_named_groups": len(ambiguous),
                  "groups_with_duplicate_same_owner_edges": sum(
                      row["edge_count"] > len(row["owners"])
                      for row in by_name.values()),
                  "ambiguous_examples_first_25": examples},
        "limits": ["authored seed corpus only", "11 seed failures reported",
                   "name collision is not proof of semantic ambiguity",
                   "does not measure downstream task impact"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)),
                      "source_stable": result["source_stable"],
                      "boot": result["boot"], "graph": result["graph"]},
                     sort_keys=True))
    if not result["source_stable"]:
        raise SystemExit("source changed during census")


if __name__ == "__main__":
    main()
