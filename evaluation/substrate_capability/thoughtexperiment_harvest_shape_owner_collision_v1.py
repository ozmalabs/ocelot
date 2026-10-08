#!/usr/bin/env python3
"""Measure whether current harvested shapes use ambiguous owner names."""
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
OUT = ROOT / "evaluation/reports/thoughtexperiment_harvest_shape_owner_collision_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_HARVEST_SHAPE_OWNER_COLLISION_V1_PREREG_20261001.md"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_HARVEST_SHAPE_OWNER_COLLISION_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_harvest_shape_owner_collision_v1.py",
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
    paths = sorted((ROOT / "seeds").glob("*.json"))
    dig = hashlib.sha256()
    for path in paths:
        dig.update(path.name.encode())
        dig.update(bytes.fromhex(sha(path)))
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "seed_count": len(paths), "seed_digest": dig.hexdigest()}


def worker() -> dict:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.implication_harvester import harvest_shapes

    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    graph = adapter.s.graph_to_dict()
    nodes = {row["id"]: row for row in graph["nodes"]}
    owner_rows = defaultdict(set)
    owner_names = defaultdict(set)
    for edge in graph["edges"]:
        if edge["type"] not in ("has_concept", "has_rule"):
            continue
        name = str(nodes.get(edge["tgt"], {}).get("attrs", {}).get("name", "") or "")
        if name and nodes.get(edge["src"], {}).get("type") == "Microtheory":
            key = (edge["type"], name)
            owner_rows[key].add(edge["src"])
            owner_names[key].update([str(nodes[edge["src"]].get("attrs", {}).get("name", ""))])
    ambiguous = {key: sorted(ids) for key, ids in owner_rows.items() if len(ids) > 1}
    shapes = harvest_shapes(adapter.s)
    selected = [{"kind": row.get("kind"), "source_concept": row.get("source_concept"),
                 "source_mt": row.get("source_mt"), "source_mt_id": row.get("source_mt_id")}
                for row in shapes]
    intersections = []
    for shape in selected:
        name = shape["source_concept"]
        hits = [(kind, ids) for (kind, candidate), ids in ambiguous.items()
                if candidate == name]
        for edge_type, ids in hits:
            intersections.append({**shape, "ownership_edge_type": edge_type,
                "candidate_owners": [{"id": nid, "name": nodes.get(nid, {}).get("attrs", {}).get("name")}
                                     for nid in ids]})
    signature = hashlib.sha256(json.dumps(selected, sort_keys=True,
        separators=(",", ":"), default=str).encode()).hexdigest()
    return {"pid": os.getpid(), "boot_loaded": boot.get("loaded"),
        "boot_failed": boot.get("failed", []), "node_count": len(graph["nodes"]),
        "edge_count": len(graph["edges"]), "ambiguous_owner_name_count": len(ambiguous),
        "selected_shape_count": len(selected), "selected_shapes": selected,
        "selected_ambiguous_sources": intersections, "shape_signature": signature}


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
    signatures = {(row["shape_signature"], json.dumps(row["selected_ambiguous_sources"], sort_keys=True))
                  for row in rows}
    result = {"protocol": PROTOCOL.name,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "source_stable": before == after,
        "source_before": before, "source_after": after, "workers": rows,
        "gates": {"three_fresh_pids": len({row["pid"] for row in rows}) == WORKERS,
            "deterministic_shape_and_collision_output": len(signatures) == 1,
            "source_stable": before == after}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
        "shape_count": rows[0]["selected_shape_count"],
        "ambiguous_owner_names": rows[0]["ambiguous_owner_name_count"],
        "selected_ambiguous_sources": rows[0]["selected_ambiguous_sources"]}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("harvest shape owner collision gate failed")


if __name__ == "__main__":
    main()
