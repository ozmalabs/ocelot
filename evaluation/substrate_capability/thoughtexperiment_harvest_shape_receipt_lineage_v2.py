#!/usr/bin/env python3
"""Verify node-identity owner provenance is invariant to receipt adoption."""
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
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"),
                str(ROOT / "evaluation/substrate_capability")]
OUT = ROOT / "evaluation/reports/thoughtexperiment_harvest_shape_receipt_lineage_v2_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_HARVEST_SHAPE_RECEIPT_LINEAGE_V2_PREREG_20261001.md"
V1_RUNNER = "evaluation/substrate_capability/thoughtexperiment_harvest_shape_applicability_receipt_v1.py"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_HARVEST_SHAPE_RECEIPT_LINEAGE_V2_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_harvest_shape_receipt_lineage_v2.py",
    V1_RUNNER, "substrate/boot_all.py", "substrate/boot_core.py",
    "substrate/world_adapter.py", "domains/implication_harvester.py",
    "domains/order_n_postulates.py", "runners/dsl/src/graph.rs",
    "runners/dsl/src/persist.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)
WORKERS = 3


def fingerprint() -> dict:
    paths = sorted((ROOT / "seeds").glob("*.json"))
    seed_hash = hashlib.sha256()
    for path in paths:
        seed_hash.update(path.name.encode())
        seed_hash.update(hashlib.sha256(path.read_bytes()).digest())
    files = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES}
    return {"files": files, "seed_count": len(paths),
            "seed_digest": seed_hash.hexdigest()}


def worker() -> dict:
    from thoughtexperiment_harvest_shape_applicability_receipt_v1 import worker as run_panel
    return run_panel()


def main() -> None:
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(), sort_keys=True))
        return
    before = fingerprint()
    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}:{ROOT / 'evaluation/substrate_capability'}"}
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
            "fixture_identity_stable": len({(tuple(r["owner_ids"]),
                r["direct_shape"].get("source_node_id")) for r in rows}) == 1,
            "canonical_graph_equal": all(r["canonical_graph_equal"] for r in rows),
            "direct_and_receipt_shapes_equal": all(r["direct_shape"] == r["receipt_shape"] for r in rows),
            "direct_and_receipt_transfers_equal_nonempty": all(
                r["direct_derived"] == r["receipt_derived"] and bool(r["direct_derived"])
                for r in rows),
            "one_exact_owner_candidate": all(
                r["direct_shape"].get("source_mt_candidates") == [{
                    "id": r["direct_shape"]["source_mt_id"],
                    "name": r["direct_shape"]["source_mt"]}]
                for r in rows),
            "source_stable": before == after,
        }}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
        "shape": rows[0]["direct_shape"],
        "derived_count": len(rows[0]["direct_derived"]),
        "worker_count": len(rows)}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("harvest lineage v2 gate failed")


if __name__ == "__main__":
    main()
