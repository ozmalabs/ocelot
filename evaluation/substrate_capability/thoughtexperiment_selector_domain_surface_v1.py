#!/usr/bin/env python3
"""Test a broad domain-module surface for the order-N open-gap selector."""
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
OUT = ROOT / "evaluation/reports/thoughtexperiment_selector_domain_surface_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_SELECTOR_DOMAIN_SURFACE_V1_PREREG_20261001.md"
PRIOR_PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_SELECTOR_CALIBRATION_V1_PREREG_20261001.md"
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
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_SELECTOR_DOMAIN_SURFACE_V1_PREREG_20261001.md",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_SELECTOR_CALIBRATION_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_selector_domain_surface_v1.py",
    "evaluation/substrate_capability/thoughtexperiment_selector_calibration_v1.py",
    "domains/order_n_postulates.py", "domains/speech_science.py",
    "substrate/boot_all.py", "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    paths = sorted((ROOT / "domains").glob("*.py"))
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(bytes.fromhex(sha(path)))
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "domain_file_count": len(paths), "domain_digest": digest.hexdigest()}


def worker() -> dict:
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from domains import order_n_postulates as onp

    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot = load_all_seeds(adapter)
    coverage = onp._covered_keywords(adapter.s)
    scan_globs = tuple(f"domains/{path.name}" for path in
                       sorted((ROOT / "domains").glob("*.py")))
    onp._SPEECH_GLOBS_OVERRIDE = scan_globs
    verdicts = []
    for case in CASES:
        verdict = onp.is_gap(adapter.s, {"name_keys": case["name_keys"]},
                             coverage, ROOT, prune=True)
        verdicts.append({**case, "verdict": verdict})
    return {"pid": os.getpid(), "boot_loaded": boot.get("loaded"),
        "boot_failed_count": len(boot.get("failed", [])),
        "covered_keyword_count": len(coverage), "scan_file_count": len(scan_globs),
        "scan_includes_combinatorial_recognizer":
            "domains/combinatorial_recognizer.py" in scan_globs,
        "cases": verdicts}


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
            "same_all_domain_surface": all(row["scan_file_count"] == rows[0]["scan_file_count"]
                and row["scan_includes_combinatorial_recognizer"] for row in rows),
            "stable_boot_and_verdicts": len({(row["boot_loaded"],
                row["boot_failed_count"], tuple(c["verdict"]["is_gap"]
                    for c in row["cases"])) for row in rows}) == 1,
            "source_stable": before == after}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
        "case_decisions": [{"case": case["case"], "expected": case["expected"],
            "is_gap": case["verdict"]["is_gap"], "reason": case["verdict"]["reason"],
            "covered_by": case["verdict"]["covered_by"]}
            for case in rows[0]["cases"]],
        "scan_file_count": rows[0]["scan_file_count"]}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("all-domain selector surface reproducibility gate failed")


if __name__ == "__main__":
    main()
