#!/usr/bin/env python3
"""Source-locked selector calibration on audited present/absent mechanisms."""
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
OUT = ROOT / "evaluation/reports/thoughtexperiment_selector_calibration_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_SELECTOR_CALIBRATION_V1_PREREG_20261001.md"
WORKERS = 3
CASES = (
    {"case": "speaker_scale_normalization", "expected": "covered",
     "name_keys": ["speaker normalization", "formant ratio",
                   "vocal-tract-length normalization", "f2/f1"]},
    {"case": "reliability_weighted_cue_fusion", "expected": "covered",
     "name_keys": ["reliability-weighted cue fusion", "multi-cue integration",
                   "audiovisual fusion estimate"]},
    {"case": "denoising_diffusion_image_generation", "expected": "open",
     "name_keys": ["denoising diffusion image generation",
                   "noise-conditioned image synthesis"]},
    {"case": "variational_autoencoder_latent_image_reconstruction", "expected": "open",
     "name_keys": ["variational autoencoder latent image reconstruction",
                   "probabilistic latent-image decoder"]},
)
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_SELECTOR_CALIBRATION_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_selector_calibration_v1.py",
    "domains/order_n_postulates.py", "domains/speech_science.py",
    "domains/sound_graph.py", "domains/speaker_norm.py",
    "domains/combinatorial_recognizer.py", "substrate/boot_all.py",
    "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    domain_paths = sorted((ROOT / "domains").glob("*.py"))
    domain_digest = hashlib.sha256()
    for path in domain_paths:
        domain_digest.update(path.name.encode())
        domain_digest.update(bytes.fromhex(sha(path)))
    seed_paths = sorted((ROOT / "seeds").glob("*.json"))
    seed_digest = hashlib.sha256()
    for path in seed_paths:
        seed_digest.update(path.name.encode())
        seed_digest.update(bytes.fromhex(sha(path)))
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "domain_source_file_count": len(domain_paths),
            "domain_source_digest": domain_digest.hexdigest(),
            "top_level_seed_file_count": len(seed_paths),
            "top_level_seed_digest": seed_digest.hexdigest()}


def worker() -> dict:
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from domains.order_n_postulates import _covered_keywords, is_gap

    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    coverage = _covered_keywords(adapter.s)
    verdicts = []
    for case in CASES:
        verdict = is_gap(adapter.s, {"name_keys": case["name_keys"]},
                         coverage, ROOT, prune=True)
        verdicts.append({**case, "verdict": verdict})
    return {"pid": os.getpid(), "boot_loaded": boot.get("loaded"),
        "boot_failed_count": len(boot.get("failed", [])),
        "covered_keyword_count": len(coverage), "cases": verdicts}


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
    statuses = lambda row: tuple(case["verdict"]["is_gap"] for case in row["cases"])
    result = {"protocol": PROTOCOL.name,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "source_before": before,
        "source_after": after, "source_stable": before == after,
        "workers": rows,
        "gates": {
            "three_fresh_pids": len({row["pid"] for row in rows}) == WORKERS,
            "stable_boot_and_cases": len({(row["boot_loaded"],
                row["boot_failed_count"], statuses(row)) for row in rows}) == 1,
            "source_stable": before == after}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
        "case_decisions": [{"case": case["case"], "expected": case["expected"],
            "is_gap": case["verdict"]["is_gap"], "reason": case["verdict"]["reason"]}
            for case in rows[0]["cases"]]}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("selector calibration reproducibility gate failed")


if __name__ == "__main__":
    main()
