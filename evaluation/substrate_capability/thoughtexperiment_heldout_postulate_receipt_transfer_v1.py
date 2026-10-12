#!/usr/bin/env python3
"""Transfer corrected harvested shape to a held-out same-domain postulate."""
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
OUT = ROOT / "evaluation/reports/thoughtexperiment_heldout_postulate_receipt_transfer_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_HELDOUT_POSTULATE_RECEIPT_TRANSFER_V1_PREREG_20261001.md"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_HELDOUT_POSTULATE_RECEIPT_TRANSFER_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_heldout_postulate_receipt_transfer_v1.py",
    "substrate/boot_all.py", "substrate/boot_core.py", "substrate/world_adapter.py",
    "domains/implication_harvester.py", "domains/order_n_postulates.py",
    "runners/dsl/src/graph.rs", "runners/dsl/src/persist.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)
WORKERS = 3
SOURCE_NAME = "batch_normalization"
POSTULATE = "sift"
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
    from domains.order_n_postulates import (harvest_postulates, synthesize_gaps,
        _mt_lineage_of_concept)

    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    primary = adapter.s
    graph = primary.graph_to_dict()
    nodes = {n["id"]: n for n in graph["nodes"]}
    owner_rows = [e for e in graph["edges"] if e["type"] == "has_concept"
        and nodes.get(e["tgt"], {}).get("attrs", {}).get("name") == SOURCE_NAME]
    source_targets = sorted({e["tgt"] for e in owner_rows})
    source_owners = sorted({e["src"] for e in owner_rows})
    postulates = [(cid, name, text) for cid, name, text in harvest_postulates(primary)
                  if name == POSTULATE]
    if len(source_targets) != 2 or len(source_owners) != 2 or len(postulates) != 1:
        raise RuntimeError("full-boot source collision or held-out SIFT identity changed")
    post_id, _, post_text = postulates[0]
    post_id_value = int(getattr(post_id, "value", post_id))
    revision, snapshot = primary.experiment_graph_rule_revision(), primary.snapshot()
    direct, branch = snapshot.fork(), snapshot.fork()
    branch.begin_experiment_delta_journal()
    rewired = [(source_owners[1], source_targets[0]),
               (source_owners[0], source_targets[1])]
    for edge in owner_rows:
        direct.remove_edge(NodeID(edge["src"]), "has_concept", NodeID(edge["tgt"]))
        branch.remove_edge(NodeID(edge["src"]), "has_concept", NodeID(edge["tgt"]))
    for owner, target in rewired:
        direct.add_edge_unchecked(NodeID(owner), "has_concept", NodeID(target), {})
        branch.add_edge_unchecked(NodeID(owner), "has_concept", NodeID(target), {})
    receipt = branch.finish_experiment_delta_journal()["conclusions"]
    primary.apply_experiment_graph_delta(revision, receipt)

    direct_shape = next(s for s in harvest_shapes(direct) if s.get("kind") == KIND)
    receipt_shape = next(s for s in harvest_shapes(primary) if s.get("kind") == KIND)
    direct_lineage = _mt_lineage_of_concept(direct, post_id)
    receipt_lineage = _mt_lineage_of_concept(primary, post_id)
    args = {"max_order": 1, "record": False, "prune": False,
            "structural_max_hops": 0}
    direct_structural = synthesize_gaps(direct, POSTULATE, shapes=[direct_shape],
        substantive_structural=True, **args)
    receipt_structural = synthesize_gaps(primary, POSTULATE, shapes=[receipt_shape],
        substantive_structural=True, **args)
    direct_surface = synthesize_gaps(direct, POSTULATE, shapes=[direct_shape],
        substantive_structural=False, **args)
    receipt_surface = synthesize_gaps(primary, POSTULATE, shapes=[receipt_shape],
        substantive_structural=False, **args)
    canonical = lambda g: sorted((e["src"], e["type"], e["tgt"],
        json.dumps(e.get("attrs", {}), sort_keys=True)) for e in g["edges"])
    has_shape = lambda gaps: any(any(KIND in via for via in row.get("via_shapes", []))
                                  for row in gaps)
    direct_graph, receipt_graph = direct.graph_to_dict(), primary.graph_to_dict()
    return {"pid": os.getpid(), "boot_loaded": boot.get("loaded"),
        "boot_failed_count": len(boot.get("failed", [])),
        "source_targets": source_targets, "source_owners": source_owners,
        "postulate_id": post_id_value, "postulate_text": post_text,
        "postulate_lineage_direct": sorted(map(str, direct_lineage)),
        "postulate_lineage_receipt": sorted(map(str, receipt_lineage)),
        "direct_shape": direct_shape, "receipt_shape": receipt_shape,
        "direct_structural_gaps": direct_structural,
        "receipt_structural_gaps": receipt_structural,
        "direct_surface_gaps": direct_surface, "receipt_surface_gaps": receipt_surface,
        "structural_hit_direct": has_shape(direct_structural),
        "structural_hit_receipt": has_shape(receipt_structural),
        "surface_hit_direct": has_shape(direct_surface),
        "surface_hit_receipt": has_shape(receipt_surface),
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
            "stable_full_boot_identities": len({(tuple(r["source_targets"]),
                tuple(r["source_owners"]), r["postulate_id"]) for r in rows}) == 1,
            "postulate_lineage_contains_computer_vision": all(
                "computer_vision" in r["postulate_lineage_direct"]
                and r["postulate_lineage_direct"] == r["postulate_lineage_receipt"]
                for r in rows),
            "exact_shape_parity_and_one_owner": all(
                r["direct_shape"] == r["receipt_shape"] and
                len(r["direct_shape"].get("source_mt_candidates", [])) == 1
                for r in rows),
            "canonical_graph_parity": all(r["canonical_graph_equal"] for r in rows),
            "heldout_structural_transfer_both_arms": all(
                r["structural_hit_direct"] and r["structural_hit_receipt"] and
                r["direct_structural_gaps"] == r["receipt_structural_gaps"]
                for r in rows),
            "surface_only_control_excludes_shape": all(
                not r["surface_hit_direct"] and not r["surface_hit_receipt"]
                for r in rows),
            "source_stable": before == after,
        }}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
        "postulate": rows[0]["postulate_id"],
        "structural_hit": rows[0]["structural_hit_direct"],
        "surface_hit": rows[0]["surface_hit_direct"], "workers": len(rows)}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("held-out postulate receipt transfer gate failed")


if __name__ == "__main__":
    main()
