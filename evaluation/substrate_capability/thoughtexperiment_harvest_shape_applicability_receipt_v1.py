#!/usr/bin/env python3
"""Check whether receipt-selected owner metadata changes structural firing."""
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
OUT = ROOT / "evaluation/reports/thoughtexperiment_harvest_shape_applicability_receipt_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_HARVEST_SHAPE_APPLICABILITY_RECEIPT_V1_PREREG_20261001.md"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_HARVEST_SHAPE_APPLICABILITY_RECEIPT_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_harvest_shape_applicability_receipt_v1.py",
    "substrate/boot_all.py", "substrate/boot_core.py", "substrate/world_adapter.py",
    "domains/implication_harvester.py", "domains/order_n_postulates.py",
    "runners/dsl/src/graph.rs", "runners/dsl/src/persist.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)
WORKERS = 3
NAME = "batch_normalization"
KIND = "scale_cancellation"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    seed_paths = sorted((ROOT / "seeds").glob("*.json"))
    digest = hashlib.sha256()
    for path in seed_paths:
        digest.update(path.name.encode())
        digest.update(bytes.fromhex(sha(path)))
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "seed_count": len(seed_paths), "seed_digest": digest.hexdigest()}


def worker() -> dict:
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from substrate_rs import NodeID
    from domains.implication_harvester import harvest_shapes
    from domains.order_n_postulates import differentiate

    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    primary = adapter.s
    graph = primary.graph_to_dict()
    nodes = {n["id"]: n for n in graph["nodes"]}
    rows = [e for e in graph["edges"] if e["type"] == "has_concept"
            and nodes.get(e["tgt"], {}).get("attrs", {}).get("name") == NAME]
    targets, owners = sorted({e["tgt"] for e in rows}), sorted({e["src"] for e in rows})
    if len(targets) != 2 or len(owners) != 2:
        raise RuntimeError("unexpected batch_normalization ownership fixture")
    revision, snapshot = primary.experiment_graph_rule_revision(), primary.snapshot()
    direct, branch = snapshot.fork(), snapshot.fork()
    branch.begin_experiment_delta_journal()
    rewired = [(owners[1], targets[0]), (owners[0], targets[1])]
    for edge in rows:
        direct.remove_edge(NodeID(edge["src"]), "has_concept", NodeID(edge["tgt"]))
        branch.remove_edge(NodeID(edge["src"]), "has_concept", NodeID(edge["tgt"]))
    for owner, target in rewired:
        direct.add_edge_unchecked(NodeID(owner), "has_concept", NodeID(target), {})
        branch.add_edge_unchecked(NodeID(owner), "has_concept", NodeID(target), {})
    receipt = branch.finish_experiment_delta_journal()["conclusions"]
    primary.apply_experiment_graph_delta(revision, receipt)

    direct_shape = next(s for s in harvest_shapes(direct) if s.get("kind") == KIND)
    receipt_shape = next(s for s in harvest_shapes(primary) if s.get("kind") == KIND)
    postulate_lineage = {"machine_learning", owners[0]}
    postulate_hops = {"machine_learning": 0, owners[0]: 0}
    direct_derived = differentiate("", shapes=[direct_shape], substrate=direct,
        postulate_mt_lineage=postulate_lineage, substantive_structural=True,
        postulate_mt_hops=postulate_hops, structural_max_hops=0)
    receipt_derived = differentiate("", shapes=[receipt_shape], substrate=primary,
        postulate_mt_lineage=postulate_lineage, substantive_structural=True,
        postulate_mt_hops=postulate_hops, structural_max_hops=0)
    canonical = lambda g: sorted((e["src"], e["type"], e["tgt"],
        json.dumps(e.get("attrs", {}), sort_keys=True)) for e in g["edges"])
    direct_graph, receipt_graph = direct.graph_to_dict(), primary.graph_to_dict()
    return {"pid": os.getpid(), "boot_loaded": boot.get("loaded"),
        "boot_failed_count": len(boot.get("failed", [])), "owner_ids": owners,
        "owner_names": {i:nodes[i].get("attrs",{}).get("name") for i in owners},
        "direct_shape": direct_shape, "receipt_shape": receipt_shape,
        "direct_derived": direct_derived, "receipt_derived": receipt_derived,
        "canonical_graph_equal": canonical(direct_graph) == canonical(receipt_graph)}


def main() -> None:
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(), sort_keys=True))
        return
    before = fingerprint()
    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    rows = []
    for _ in range(WORKERS):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
            cwd=ROOT, env=env, check=True, text=True, capture_output=True)
        rows.append(json.loads(proc.stdout))
    after = fingerprint()
    result = {"protocol": PROTOCOL.name,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "source_stable": before == after,
        "source_before": before, "source_after": after, "workers": rows,
        "gates": {
            "three_fresh_pids": len({r["pid"] for r in rows}) == WORKERS,
            "canonical_graph_equal": all(r["canonical_graph_equal"] for r in rows),
            "direct_fires_scale_cancellation": all(any(
                x["via_shape"] == r["direct_shape"]["name"] for x in r["direct_derived"])
                for r in rows),
            "receipt_does_not_fire_for_ml_lineage": all(not any(
                x["via_shape"] == r["receipt_shape"]["name"] for x in r["receipt_derived"])
                for r in rows),
            "direct_and_receipt_owner_differ": all(
                r["direct_shape"]["source_mt_id"] != r["receipt_shape"]["source_mt_id"]
                for r in rows),
            "source_stable": before == after,
        }}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
        "direct_derived_count": len(rows[0]["direct_derived"]),
        "receipt_derived_count": len(rows[0]["receipt_derived"]),
        "worker_count": len(rows)}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("harvest shape applicability gate failed")


if __name__ == "__main__":
    main()
