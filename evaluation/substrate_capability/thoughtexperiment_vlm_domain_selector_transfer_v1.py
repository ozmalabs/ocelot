#!/usr/bin/env python3
"""Replay the VLM fusion transfer with derivation and domain-wide openness gates."""
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
OUT = ROOT / "evaluation/reports/thoughtexperiment_vlm_domain_selector_transfer_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_VLM_DOMAIN_SELECTOR_TRANSFER_V1_PREREG_20261001.md"
WORKERS = 3
POSTULATE = "vision_language_model"
SHAPE_TAG = "reliability_weighted_fusion__from__Kalman_filter"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_VLM_DOMAIN_SELECTOR_TRANSFER_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_vlm_domain_selector_transfer_v1.py",
    "domains/order_n_postulates.py", "domains/implication_harvester.py",
    "domains/harvester_shape.py", "domains/speech_science.py",
    "domains/combinatorial_recognizer.py", "substrate/boot_all.py",
    "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    domains = sorted((ROOT / "domains").glob("*.py"))
    domain_digest = hashlib.sha256()
    for path in domains:
        domain_digest.update(path.name.encode())
        domain_digest.update(bytes.fromhex(sha(path)))
    seeds = sorted((ROOT / "seeds").glob("*.json"))
    seed_digest = hashlib.sha256()
    for path in seeds:
        seed_digest.update(path.name.encode())
        seed_digest.update(bytes.fromhex(sha(path)))
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "domain_file_count": len(domains), "domain_digest": domain_digest.hexdigest(),
            "seed_file_count": len(seeds), "seed_digest": seed_digest.hexdigest()}


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
    from domains import order_n_postulates as onp

    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    substrate = adapter.s
    posts = {name: (cid, text) for cid, name, text in onp.harvest_postulates(substrate)}
    if POSTULATE not in posts:
        raise RuntimeError("held VLM postulate missing from full boot")
    coverage = onp._covered_keywords(substrate)
    shapes, shape_mode = onp._resolve_shapes(substrate, None)
    scan_globs = tuple(f"domains/{p.name}" for p in sorted((ROOT / "domains").glob("*.py")))
    onp._SPEECH_GLOBS_OVERRIDE = scan_globs
    before = canonical_graph(substrate)
    common = {"max_order": 1, "record": False, "shapes": shapes,
              "covered_keywords": coverage}
    derived = onp.synthesize_gaps(substrate, POSTULATE, prune=False, **common)
    opened = onp.synthesize_gaps(substrate, POSTULATE, prune=True, **common)
    target = [g for g in derived if SHAPE_TAG in g.get("via_shapes", [])]
    target_keys = target[0].get("capability_keys", []) if target else []
    selector = onp.is_gap(substrate, {"name_keys": target_keys}, coverage, ROOT, prune=True) \
        if target_keys else {"is_gap": None, "reason": "target derivation absent", "covered_by": None}
    pruned_target = [g for g in opened if SHAPE_TAG in g.get("via_shapes", [])]
    after = canonical_graph(substrate)
    return {"pid": os.getpid(), "boot_loaded": boot.get("loaded"),
        "boot_failed_count": len(boot.get("failed", [])),
        "postulate_id": int(getattr(posts[POSTULATE][0], "value", posts[POSTULATE][0])),
        "shape_mode": shape_mode, "shape_count": len(shapes),
        "scan_file_count": len(scan_globs), "graph_before": before,
        "graph_after": after, "graph_unchanged": before == after,
        "derived_gaps": derived, "open_gaps": opened,
        "target_derivation": target, "target_selector_verdict": selector,
        "target_pruned_gaps": pruned_target}


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
            "three_fresh_pids": len({r["pid"] for r in rows}) == WORKERS,
            "stable_postulate_and_source_mode": len({(r["postulate_id"],
                r["shape_mode"], r["shape_count"], r["scan_file_count"])
                for r in rows}) == 1,
            "target_derived_in_every_worker": all(bool(r["target_derivation"]) for r in rows),
            "all_domain_match_is_combinatorial_recognizer": all(
                r["target_selector_verdict"].get("covered_by", "").endswith(
                    "domains/combinatorial_recognizer.py") for r in rows),
            "target_removed_by_normal_pruning": all(not r["target_pruned_gaps"] for r in rows),
            "graph_unchanged": all(r["graph_unchanged"] for r in rows),
            "source_stable": before == after}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
        "workers": WORKERS,
        "target_gap_count": len(rows[0]["target_derivation"]),
        "total_derived": len(rows[0]["derived_gaps"]),
        "total_open": len(rows[0]["open_gaps"]),
        "selector": rows[0]["target_selector_verdict"]}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("VLM domain selector transfer gate failed")


if __name__ == "__main__":
    main()
