#!/usr/bin/env python3
"""Identify the selector branch that prunes the held-out scale gap."""
from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evaluation/reports/thoughtexperiment_heldout_selector_reason_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_HELDOUT_SELECTOR_REASON_V1_PREREG_20261001.md"
PANEL = ROOT / "evaluation/reports/thoughtexperiment_heldout_postulate_selector_v2_raw_20261001.json"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_HELDOUT_SELECTOR_REASON_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_heldout_selector_reason_v1.py",
    "domains/order_n_postulates.py", "domains/speech_science.py",
    "domains/implication_harvester.py", "substrate/boot_all.py",
    "substrate/world_adapter.py", "runners/dsl/python/substrate_rs/_native.abi3.so",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    paths = sorted((ROOT / "seeds").glob("*.json"))
    seed_digest = hashlib.sha256()
    for path in paths:
        seed_digest.update(path.name.encode())
        seed_digest.update(bytes.fromhex(sha(path)))
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "seed_count": len(paths), "seed_digest": seed_digest.hexdigest()}


def main() -> None:
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from domains.order_n_postulates import _covered_keywords, is_gap

    before = fingerprint()
    panel = json.loads(PANEL.read_text())
    captured_hashes = panel["source_before"]["files"]
    # The v2 panel fingerprinted order_n_postulates but did not list
    # speech_science; this run fingerprints both before/after independently.
    relevant_paths = ("domains/order_n_postulates.py",)
    panel_source_matches = all(before["files"][p] == captured_hashes.get(p)
                               for p in relevant_paths)
    derivation = panel["workers"][0]["direct_structural_gaps"][0]
    keys = derivation["capability_keys"]
    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    covered = _covered_keywords(adapter.s)
    verdict = is_gap(adapter.s, {"name_keys": keys}, covered, ROOT, prune=True)
    matched_coverage = {}
    generic = {"formant", "formants", "speaker", "model", "boundary", "context",
        "removal", "coding", "internal", "probability", "mixture", "clustering",
        "cluster", "segmentation", "prediction", "predictive", "normalization",
        "normalisation", "synthesiser", "synthesizer", "synthesis", "forward"}
    for key in keys:
        toks = [t for t in __import__("re").split(r"[\s_/-]+", key.lower())
                if len(t) > 2 and t not in generic]
        matched_coverage[key] = {token: sorted(cw for cw in covered
            if token == cw or token in cw) for token in toks}
    after = fingerprint()
    result = {"protocol": PROTOCOL.name,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "panel_input": PANEL.name,
        "panel_source_hashes_match": panel_source_matches,
        "source_stable": before == after, "source_before": before,
        "source_after": after,
        "boot": {"loaded": boot.get("loaded"),
                 "failed_count": len(boot.get("failed", [])),
                 "failed": boot.get("failed", [])},
        "candidate": {"postulate": "sift", "keys": keys,
                      "gap": derivation["gap"],
                      "matched_coverage": matched_coverage,
                      "verdict": verdict},
        "gates": {"panel_source_hashes_match": panel_source_matches,
            "full_boot_returned": boot.get("loaded") is not None,
            "determinate_verdict": verdict.get("reason") in (
                "already covered (science/impl)", "already in speech codebase",
                "follows by transfer + un-realized + new capability axis"),
            "source_stable": before == after}}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
        "verdict": verdict, "boot_loaded": boot.get("loaded"),
        "boot_failed": len(boot.get("failed", []))}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("selector reason diagnostic gate failed")


if __name__ == "__main__":
    main()
