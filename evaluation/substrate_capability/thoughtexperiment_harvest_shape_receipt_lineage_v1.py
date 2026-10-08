#!/usr/bin/env python3
"""Compare selected harvested shape lineage across direct and receipt states."""
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
OUT = ROOT / "evaluation/reports/thoughtexperiment_harvest_shape_receipt_lineage_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_HARVEST_SHAPE_RECEIPT_LINEAGE_V1_PREREG_20261001.md"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_HARVEST_SHAPE_RECEIPT_LINEAGE_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_harvest_shape_receipt_lineage_v1.py",
    "substrate/boot_all.py", "substrate/boot_core.py", "substrate/world_adapter.py",
    "domains/implication_harvester.py", "runners/dsl/src/graph.rs",
    "runners/dsl/src/persist.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)
WORKERS = 3
NAME = "batch_normalization"
KIND = "scale_cancellation"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    paths = sorted((ROOT / "seeds").glob("*.json"))
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(bytes.fromhex(sha(path)))
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "seed_count": len(paths), "seed_digest": digest.hexdigest()}


def worker() -> dict:
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from substrate_rs import NodeID
    from domains.implication_harvester import harvest_shapes

    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    primary = adapter.s
    graph = primary.graph_to_dict()
    nodes = {n["id"]: n for n in graph["nodes"]}
    original_rows = [e for e in graph["edges"] if e["type"] == "has_concept"
                     and nodes.get(e["tgt"], {}).get("attrs", {}).get("name") == NAME]
    target_ids = sorted({e["tgt"] for e in original_rows})
    owner_ids = sorted({e["src"] for e in original_rows})
    if len(target_ids) != 2 or len(owner_ids) != 2:
        raise RuntimeError(f"unexpected {NAME} collision: targets={target_ids} owners={owner_ids}")
    owners = {nid: nodes[nid].get("attrs", {}).get("name") for nid in owner_ids}
    rewired = [(owner_ids[1], target_ids[0]), (owner_ids[0], target_ids[1])]
    revision = primary.experiment_graph_rule_revision()
    snapshot = primary.snapshot()
    direct = snapshot.fork()
    branch = snapshot.fork()
    branch.begin_experiment_delta_journal()
    for edge in original_rows:
        direct.remove_edge(NodeID(edge["src"]), "has_concept", NodeID(edge["tgt"]))
        branch.remove_edge(NodeID(edge["src"]), "has_concept", NodeID(edge["tgt"]))
    for owner, target in rewired:
        direct.add_edge_unchecked(NodeID(owner), "has_concept", NodeID(target), {})
        branch.add_edge_unchecked(NodeID(owner), "has_concept", NodeID(target), {})
    receipt = branch.finish_experiment_delta_journal()["conclusions"]
    primary.apply_experiment_graph_delta(revision, receipt)

    canonical = lambda g: sorted((e["src"], e["type"], e["tgt"],
                                  json.dumps(e.get("attrs", {}), sort_keys=True))
                                 for e in g["edges"])
    direct_graph, adopted_graph = direct.graph_to_dict(), primary.graph_to_dict()
    direct_shapes, adopted_shapes = harvest_shapes(direct), harvest_shapes(primary)
    select = lambda shapes: next((s for s in shapes if s.get("kind") == KIND), None)
    direct_shape, adopted_shape = select(direct_shapes), select(adopted_shapes)
    strip_owner = lambda row: {k:v for k,v in row.items() if k not in ("source_mt", "source_mt_id")} if row else None
    shape_signature = lambda shapes: hashlib.sha256(json.dumps(
        [strip_owner(row) for row in shapes], sort_keys=True, separators=(",", ":"),
        default=str).encode()).hexdigest()
    return {
        "pid": os.getpid(), "boot_loaded": boot.get("loaded"),
        "boot_failed_count": len(boot.get("failed", [])),
        "source_name": NAME, "kind": KIND, "target_ids": target_ids,
        "owner_ids": owner_ids, "owner_names": owners,
        "direct_shape_count": len(direct_shapes), "adopted_shape_count": len(adopted_shapes),
        "direct_shape_signature_without_owner": shape_signature(direct_shapes),
        "adopted_shape_signature_without_owner": shape_signature(adopted_shapes),
        "direct_target_shape": direct_shape, "adopted_target_shape": adopted_shape,
        "canonical_graph_equal": canonical(direct_graph) == canonical(adopted_graph),
    }


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
            "fixture_identity_stable": all(r["target_ids"] == rows[0]["target_ids"]
                and r["owner_ids"] == rows[0]["owner_ids"] for r in rows),
            "canonical_graph_equal": all(r["canonical_graph_equal"] for r in rows),
            "same_shape_content_except_owner": all(
                r["direct_shape_signature_without_owner"] == r["adopted_shape_signature_without_owner"]
                for r in rows),
            "shape_owner_flips_between_fixture_owners": all(
                r["direct_target_shape"] is not None and r["adopted_target_shape"] is not None
                and r["direct_target_shape"]["source_mt_id"] != r["adopted_target_shape"]["source_mt_id"]
                and r["direct_target_shape"]["source_mt_id"] in r["owner_ids"]
                and r["adopted_target_shape"]["source_mt_id"] in r["owner_ids"]
                for r in rows),
            "source_stable": before == after,
        }}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
        "direct_owner": rows[0]["direct_target_shape"],
        "adopted_owner": rows[0]["adopted_target_shape"],
        "worker_count": len(rows)}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("harvest shape receipt lineage gate failed")


if __name__ == "__main__":
    main()
