#!/usr/bin/env python3
"""Compare cached and default selector-index paths on frozen CV candidates."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evaluation/reports/thoughtexperiment_coverage_cache_parity_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_COVERAGE_CACHE_PARITY_V1_PREREG_20261001.md"
CANDIDATES = ("diffusion_model_vision", "variational_autoencoder", "vision_language_model")
WORKERS = 3
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_COVERAGE_CACHE_PARITY_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_coverage_cache_parity_v1.py",
    "evaluation/substrate_capability/thoughtexperiment_open_gap_discovery_cv_v1.py",
    "domains/order_n_postulates.py", "domains/implication_harvester.py",
    "domains/harvester_shape.py", "domains/speech_science.py",
    "substrate/boot_all.py", "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    seed_paths = sorted((ROOT / "seeds").glob("*.json"))
    seed_hash = hashlib.sha256()
    for path in seed_paths:
        seed_hash.update(path.name.encode())
        seed_hash.update(bytes.fromhex(sha(path)))
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "seed_file_count": len(seed_paths), "seed_digest": seed_hash.hexdigest()}


def canonical_graph(substrate) -> str:
    graph = substrate.graph_to_dict()
    nodes = sorted((n["id"], n["type"], json.dumps(n.get("attrs", {}), sort_keys=True))
                   for n in graph["nodes"])
    edges = sorted((e["src"], e["type"], e["tgt"],
                    json.dumps(e.get("attrs", {}), sort_keys=True))
                   for e in graph["edges"])
    return hashlib.sha256(json.dumps([nodes, edges], separators=(",", ":"),
                                     sort_keys=True).encode()).hexdigest()


def worker() -> dict:
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from domains.order_n_postulates import (
        _covered_keywords, _resolve_shapes, harvest_postulates, synthesize_gaps)

    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    substrate = adapter.s
    posts = {name: text for _, name, text in harvest_postulates(
        substrate, mt_name="computer_vision")}
    if not all(name in posts for name in CANDIDATES):
        raise RuntimeError("candidate postulate missing after full boot")
    coverage = _covered_keywords(substrate)
    shapes, shape_mode = _resolve_shapes(substrate, None)
    graph_before = canonical_graph(substrate)
    pairs = []
    for name in CANDIDATES:
        start = time.perf_counter()
        default = synthesize_gaps(substrate, name, max_order=1, record=False,
            prune=True, shapes=shapes)
        default_seconds = time.perf_counter() - start
        start = time.perf_counter()
        cached = synthesize_gaps(substrate, name, max_order=1, record=False,
            prune=True, shapes=shapes, covered_keywords=coverage)
        cached_seconds = time.perf_counter() - start
        pairs.append({"postulate": name, "postulate_text": posts[name],
            "default_gaps": default, "cached_gaps": cached,
            "exact_output_equal": default == cached,
            "default_seconds": default_seconds, "cached_seconds": cached_seconds})
    graph_after = canonical_graph(substrate)
    return {"pid": os.getpid(), "boot_loaded": boot.get("loaded"),
        "boot_failed_count": len(boot.get("failed", [])),
        "shape_mode": shape_mode, "shape_count": len(shapes),
        "covered_keyword_count": len(coverage), "graph_before": graph_before,
        "graph_after": graph_after, "graph_unchanged": graph_before == graph_after,
        "pairs": pairs}


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
        "platform": platform.platform(), "source_before": before,
        "source_after": after, "source_stable": before == after,
        "workers": rows,
        "gates": {
            "three_fresh_pids": len({row["pid"] for row in rows}) == WORKERS,
            "stable_boot_and_shape_mode": len({(row["boot_loaded"],
                row["boot_failed_count"], row["shape_mode"], row["shape_count"])
                for row in rows}) == 1,
            "all_complete_outputs_equal": all(pair["exact_output_equal"]
                for row in rows for pair in row["pairs"]),
            "all_graphs_unchanged": all(row["graph_unchanged"] for row in rows),
            "source_stable": before == after}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)),
        "gates": result["gates"], "workers": WORKERS,
        "timing_medians_seconds": {name: {
            "default": sorted(pair["default_seconds"] for row in rows
                for pair in row["pairs"] if pair["postulate"] == name)[1],
            "cached": sorted(pair["cached_seconds"] for row in rows
                for pair in row["pairs"] if pair["postulate"] == name)[1]}
            for name in CANDIDATES}}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("coverage-index parity gate failed")


if __name__ == "__main__":
    main()
