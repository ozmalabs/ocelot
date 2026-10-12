#!/usr/bin/env python3
"""Exercise receipt-order owner attribution on a full-boot corpus collision."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
OUT = ROOT / "evaluation/reports/thoughtexperiment_real_collision_receipt_attribution_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_REAL_COLLISION_RECEIPT_ATTRIBUTION_V1_PREREG_20261001.md"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_REAL_COLLISION_RECEIPT_ATTRIBUTION_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_real_collision_receipt_attribution_v1.py",
    "substrate/boot_all.py", "substrate/boot_core.py", "substrate/world_adapter.py",
    "domains/implication_harvester.py", "runners/dsl/src/graph.rs",
    "runners/dsl/src/persist.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)
WORKERS = 3


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    seed_paths = sorted((ROOT / "seeds").glob("*.json"))
    seed_hash = hashlib.sha256()
    for path in seed_paths:
        seed_hash.update(path.name.encode())
        seed_hash.update(bytes.fromhex(sha(path)))
    return {"files": {name: sha(ROOT / name) for name in SOURCES},
            "seed_file_count": len(seed_paths),
            "seed_json_sha256": seed_hash.hexdigest()}


def worker() -> dict:
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from substrate_rs import NodeID
    from domains.implication_harvester import _owning_mt_map

    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    primary = adapter.s
    graph = primary.graph_to_dict()
    nodes = {row["id"]: row for row in graph["nodes"]}
    grouped = defaultdict(list)
    for edge in graph["edges"]:
        if edge["type"] != "has_concept":
            continue
        child = nodes.get(edge["tgt"], {})
        name = str(child.get("attrs", {}).get("name", "") or "")
        if name:
            grouped[name].append(edge)
    candidates = []
    for name, rows in grouped.items():
        targets = sorted({row["tgt"] for row in rows})
        owners = sorted({row["src"] for row in rows})
        if len(targets) == 2 and len(owners) == 2 and all(
                nodes.get(owner, {}).get("type") == "Microtheory" for owner in owners):
            candidates.append((name, targets, owners, rows))
    if not candidates:
        raise RuntimeError("full boot contains no eligible two-owner has_concept collision")
    name, targets, owners, original_rows = sorted(candidates, key=lambda row: row[0])[0]
    owner_by_id = {owner: nodes[owner].get("attrs", {}).get("name") for owner in owners}
    target_for_owner = {owners[0]: targets[0], owners[1]: targets[1]}
    rewired = [(owners[1], targets[0]), (owners[0], targets[1])]
    revision = primary.experiment_graph_rule_revision()
    snapshot = primary.snapshot()

    direct = snapshot.fork()
    branch = snapshot.fork()
    branch.begin_experiment_delta_journal()
    for row in original_rows:
        direct.remove_edge(NodeID(row["src"]), "has_concept", NodeID(row["tgt"]))
        branch.remove_edge(NodeID(row["src"]), "has_concept", NodeID(row["tgt"]))
    for owner, target in rewired:
        direct.add_edge_unchecked(NodeID(owner), "has_concept", NodeID(target), {})
        branch.add_edge_unchecked(NodeID(owner), "has_concept", NodeID(target), {})
    receipt = branch.finish_experiment_delta_journal()["conclusions"]
    primary.apply_experiment_graph_delta(revision, receipt)

    canonical = lambda g: sorted((e["src"], e["type"], e["tgt"],
                                  json.dumps(e.get("attrs", {}), sort_keys=True))
                                 for e in g["edges"])
    direct_graph = direct.graph_to_dict()
    adopted_graph = primary.graph_to_dict()
    direct_owner = _owning_mt_map(direct).get(name)
    adopted_owner = _owning_mt_map(primary).get(name)
    return {
        "pid": os.getpid(), "boot_loaded": boot.get("loaded"),
        "boot_failed_count": len(boot.get("failed", [])),
        "selected_name": name, "target_ids": targets, "owner_ids": owners,
        "owner_names": owner_by_id,
        "original_rows": sorted((r["src"], r["tgt"]) for r in original_rows),
        "rewired_direct_write_order": rewired,
        "receipt_added_order": [(r["src"], r["tgt"]) for r in receipt["edges_added"]],
        "direct_owner_attribution": direct_owner,
        "adopted_owner_attribution": adopted_owner,
        "canonical_graph_equal": canonical(direct_graph) == canonical(adopted_graph),
    }


def main() -> None:
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(), sort_keys=True))
        return
    before = fingerprint()
    workers = []
    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    for _ in range(WORKERS):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
                              cwd=ROOT, env=env, check=True, text=True, capture_output=True)
        workers.append(json.loads(proc.stdout))
    after = fingerprint()
    result = {
        "protocol": PROTOCOL.name, "captured_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "source_stable": before == after,
        "source_before": before, "source_after": after, "workers": workers,
        "gates": {
            "three_fresh_pids": len({row["pid"] for row in workers}) == WORKERS,
            "deterministic_fixture": len({row["selected_name"] for row in workers}) == 1,
            "two_target_two_owner_fixture": all(
                len(row["target_ids"]) == 2 and len(row["owner_ids"]) == 2
                for row in workers),
            "receipt_additions_sorted_by_edge_key": all(
                row["receipt_added_order"] == sorted(row["receipt_added_order"])
                for row in workers),
            "canonical_graph_equality": all(row["canonical_graph_equal"] for row in workers),
            "receipt_owner_attribution_differs": all(
                row["direct_owner_attribution"] != row["adopted_owner_attribution"]
                for row in workers),
            "source_stable": before == after,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
                      "selected_name": workers[0]["selected_name"],
                      "worker_count": len(workers)}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("real-collision receipt attribution gate failed")


if __name__ == "__main__":
    main()
