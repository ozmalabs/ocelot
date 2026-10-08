#!/usr/bin/env python3
"""Exploratory, source-locked order-1 open-gap screen for computer vision."""
from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evaluation/reports/thoughtexperiment_open_gap_discovery_cv_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_OPEN_GAP_DISCOVERY_CV_V1_20261001.md"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_OPEN_GAP_DISCOVERY_CV_V1_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_open_gap_discovery_cv_v1.py",
    "domains/order_n_postulates.py", "domains/implication_harvester.py",
    "domains/harvester_shape.py", "domains/speech_science.py",
    "substrate/boot_all.py", "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    # Boot's ordinary seed loader consumes top-level manifests; recursive globbing
    # also walks the large generated fixture/archive tree and is not this corpus.
    seed_paths = sorted((ROOT / "seeds").glob("*.json"))
    seed_hash = hashlib.sha256()
    for path in seed_paths:
        seed_hash.update(str(path.relative_to(ROOT)).encode())
        seed_hash.update(bytes.fromhex(sha(path)))
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "seed_file_count": len(seed_paths), "seed_digest": seed_hash.hexdigest()}


def main() -> None:
    import sys
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from domains.order_n_postulates import (
        _covered_keywords, _resolve_shapes, harvest_postulates, synthesize_gaps)

    before = fingerprint()
    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    substrate = adapter.s
    posts = harvest_postulates(substrate, mt_name="computer_vision")
    covered = _covered_keywords(substrate)
    shapes, mode = _resolve_shapes(substrate, None)
    rows = []
    for _, name, text in posts:
        gaps = synthesize_gaps(substrate, name, max_order=1, record=False,
            prune=True, shapes=shapes, covered_keywords=covered)
        rows.append({"postulate": name, "postulate_text": text,
            "retained_open_gaps": gaps})
    after = fingerprint()
    result = {"protocol": PROTOCOL.name,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "scope": "computer_vision",
        "mode": "exploratory_candidate_discovery_not_confirmatory",
        "max_order": 1, "selector_prune": True, "record": False,
        "shape_mode": mode, "shape_count": len(shapes),
        "covered_keyword_count": len(covered), "postulate_count": len(posts),
        "boot": {"loaded": boot.get("loaded"),
                 "failed_count": len(boot.get("failed", []))},
        "source_before": before, "source_after": after,
        "source_stable": before == after, "postulates": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    candidates = [{"postulate": row["postulate"],
        "gaps": [{"capability_keys": gap.get("capability_keys"),
                  "via_shapes": gap.get("via_shapes"),
                  "source_concepts": gap.get("source_concepts", [])}
                 for gap in row["retained_open_gaps"]]}
        for row in rows if row["retained_open_gaps"]]
    print(json.dumps({"output": str(OUT.relative_to(ROOT)),
        "boot_loaded": boot.get("loaded"),
        "boot_failed_count": len(boot.get("failed", [])),
        "postulates": len(posts), "shapes": len(shapes), "shape_mode": mode,
        "candidate_postulates": len(candidates), "source_stable": before == after,
        "candidates": candidates}, sort_keys=True))
    if before != after:
        raise SystemExit("source or seed files changed during discovery")


if __name__ == "__main__":
    main()
