#!/usr/bin/env python3
"""Capture vocabulary-enabled MetaShape filing calls from actor-goal helpers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["OZMA_SEED_PERSIST_DISABLED"] = "1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_tree_digest() -> str:
    h = hashlib.sha256()
    for path in sorted((ROOT / "seeds").glob("*.json")):
        h.update(path.relative_to(ROOT).as_posix().encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def main() -> None:
    import substrate_rs
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    import domains.actor_goals as actor_goals
    import domains.teach as teach_module

    before_seeds = seed_tree_digest()
    original = teach_module.categorise_by_shape
    active_helper = ""
    observations = []

    def recorded_categorise(agent, type_, attrs):
        result = original(agent, type_, attrs)
        observations.append({
            "helper": active_helper,
            "type": type_,
            "attrs": attrs,
            "result": result,
        })
        return result

    teach_module.categorise_by_shape = recorded_categorise
    wa = WorldAdapter()
    vocabulary_manifest = manifest_for("shape_vocabulary")
    wa.inner.load_seed_manifest(vocabulary_manifest, wa.agent)
    helpers = [
        ("seed_epistemic_codebook", lambda: actor_goals.seed_epistemic_codebook(
            wa, forced_choices=[])),
        ("seed_class_baseline_codebook", lambda: actor_goals.seed_class_baseline_codebook(wa)),
        ("seed_legal_hedging_codebook", lambda: actor_goals.seed_legal_hedging_codebook(wa)),
    ]
    completion = []
    for name, call in helpers:
        active_helper = name
        call()
        completion.append(name)
    after_seeds = seed_tree_digest()
    native_path = Path(substrate_rs.__file__).resolve()
    source_paths = [
        ROOT / "domains" / "teach.py",
        ROOT / "domains" / "actor_goals.py",
        ROOT / "substrate" / "world_adapter.py",
        Path(__file__).resolve(),
    ]
    output = {
        "schema": "substrate_metashape_default_filing_runtime_v1_1",
        "protocol": "docs/research/engine_substrate/SUBSTRATE_METASHAPE_DEFAULT_FILING_RUNTIME_V1_1_AMENDMENT_20260926.md",
        "condition": "default_world_adapter_plus_shape_vocabulary",
        "loaded_vocabulary_manifest_sha256": hashlib.sha256(
            json.dumps(vocabulary_manifest, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "seed_persist_disabled": os.environ.get("OZMA_SEED_PERSIST_DISABLED") == "1",
        "seed_tree_sha256_before": before_seeds,
        "seed_tree_sha256_after": after_seeds,
        "seed_tree_unchanged": before_seeds == after_seeds,
        "helpers_completed": completion,
        "loaded_metashape_count": len(wa.s.nodes("MetaShape")),
        "categorise_by_shape_calls": len(observations),
        "observations": observations,
        "source_sha256": {p.relative_to(ROOT).as_posix(): digest(p) for p in source_paths},
        "native_artifact": {"path": native_path.name, "sha256": digest(native_path)},
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
