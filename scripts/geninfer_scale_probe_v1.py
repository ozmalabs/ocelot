#!/usr/bin/env python3
"""Locked repeated scale probe for direct 2-D GenInfer calls."""
from __future__ import annotations

import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line

engine_preamble()

from substrate_rs import _native  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_geninfer_scale_probe_v1_20260926.json"
BASE = [["cell", 0, 0, "red"], ["cell", 0, 1, "red"],
        ["cell", 1, 0, "red"], ["cell", 2, 0, "red"]]
SCALES = (1, 2, 3)
REPETITIONS = 5


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def target_for(scale: int) -> tuple[list, list[int]]:
    matrix = [2 * scale, scale, scale, scale]
    target = [[pred, matrix[0] * r + matrix[1] * c,
               matrix[2] * r + matrix[3] * c, value]
              for pred, r, c, value in BASE]
    return target, matrix


def main() -> None:
    sub = _native.Substrate()
    sub.add_node("ShapeSignature", {
        "name": "base_L", "signature": json.dumps(BASE), "kind": "faculty",
        "faculty": "base_L", "dim_types": ["pred", "coord:r", "coord:c", "val"]})
    terms = {
        scale: {"type": "GenInfer", "goal": {"type": "Lit", "value": target_for(scale)[0]},
                "codebook_type": "ShapeSignature", "max_dims": 2, "field": "matrix"}
        for scale in SCALES}

    # One declared warm-up at the smallest search bound; it is not recorded.
    sub.evaluate(terms[1], {})
    samples = []
    for repetition in range(REPETITIONS):
        for scale in SCALES:
            started = time.perf_counter()
            matrix = [int(x) for x in sub.evaluate(terms[scale], {})]
            elapsed = time.perf_counter() - started
            samples.append({"repetition": repetition + 1, "scale": scale,
                            "bound": 4 * scale, "matrix": matrix,
                            "elapsed_seconds": elapsed})

    counts = {}
    for scale in SCALES:
        checked_term = {**terms[scale], "field": "checked"}
        counts[str(4 * scale)] = int(sub.evaluate(checked_term, {}))

    extension = Path(_native.__file__).resolve()
    source_paths = (
        "scripts/geninfer_scale_probe_v1.py",
        "scripts/analyze_substrate_geninfer_scale_probe_v1.py",
        "docs/research/engine_substrate/SUBSTRATE_GENINFER_SCALE_PREREG_20260926.md",
        "runners/dsl/src/shape_decode.rs", "runners/dsl/src/term.rs",
        "runners/dsl/python/substrate_rs/_native.build.json")
    report = {
        "schema_version": 1,
        "run_id": "substrate-geninfer-scale-probe-v1-20260926",
        "engine": provenance_line(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "protocol": {"scales": list(SCALES), "bounds": [4 * s for s in SCALES],
                     "repetitions": REPETITIONS, "warmup": "one untimed B=4 call",
                     "timed_call": "direct GenInfer evaluation, field=matrix"},
        "provenance": {
            "source_sha256": {rel: sha(ROOT / rel) for rel in source_paths},
            "native_extension_path": str(extension),
            "native_extension_sha256": sha(extension)},
        "candidate_counts_by_bound": counts,
        "samples": samples,
        "claim_boundary": (
            "One positive four-relation, 2-D integer-linear fixture; three bounds "
            "through B=12. No higher-dimensional, noisy, closure, memory, or "
            "natural-task scaling claim."),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"run_id": report["run_id"], "engine": report["engine"],
                      "samples": len(samples), "candidate_counts_by_bound": counts,
                      "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
