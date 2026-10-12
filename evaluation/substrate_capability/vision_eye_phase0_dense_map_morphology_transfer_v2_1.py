#!/usr/bin/env python3
"""Second-site-grid, larger-patch replication of the phase-0 map panel."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import assert_measuring_engine

BASE_PATH = ROOT / "evaluation/substrate_capability/vision_eye_phase0_dense_map_morphology_transfer_v1.py"
SPEC = importlib.util.spec_from_file_location("phase0_morphology_v1", BASE_PATH)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BASE)

RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_vision_eye_phase0_dense_map_morphology_transfer_v2_1.py"
BASE_ANALYZER = ROOT / "evaluation/substrate_capability/analyze_vision_eye_phase0_dense_map_morphology_transfer_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_EYE_PHASE0_DENSE_MAP_MORPHOLOGY_TRANSFER_V2_1_PREREG_20261005.md"
LOCK = ROOT / "evaluation/substrate_capability/vision_eye_phase0_dense_map_morphology_transfer_v2_1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_20261005.json"
PRIOR_CAPTURE = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v1_20261005.json"
PRIOR_ANALYSIS = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v1_analysis_20261005.json"
SEEDS = (30, 31, 32, 33, 34, 35)
MORPHOLOGIES = ("square", "cross")
TRAIN_SITES = tuple((y, x) for y in (2, 7, 13) for x in (2, 7, 13))
HELDOUT_SITES = tuple((y, x) for y in (4, 5, 9, 10) for x in (4, 5, 9, 10))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest() -> dict:
    provenance = assert_measuring_engine()
    return {
        "runner_sha256": sha(RUNNER), "analyzer_sha256": sha(ANALYZER),
        "base_analyzer_sha256": sha(BASE_ANALYZER),
        "protocol_sha256": sha(PROTOCOL), "base_runner_sha256": sha(BASE_PATH),
        "prior_capture_sha256": sha(PRIOR_CAPTURE),
        "prior_analysis_sha256": sha(PRIOR_ANALYSIS),
        "native_sha256": sha(Path(BASE._native.__file__).resolve()),
        "engine_fingerprint": provenance["source_fingerprint"],
        "seed_sha256": {name: sha(ROOT / "seeds" / name) for name in BASE.SEEDS},
        "sources": {name: sha(ROOT / name) for name in BASE.SOURCES},
    }


def prepare_base():
    BASE.TRAIN_SITES = TRAIN_SITES
    BASE.HELDOUT_SITES = HELDOUT_SITES
    BASE.ALL_SITES = TRAIN_SITES + HELDOUT_SITES

    def larger_mask(site, morphology):
        y, x = site
        if morphology == "square":
            offsets = tuple((dy, dx) for dy in range(-2, 3) for dx in range(-2, 3))
        else:
            offsets = ((0, 0),) + tuple(
                offset for radius in (1, 2)
                for offset in ((0, -radius), (0, radius), (-radius, 0), (radius, 0))
            )
        return {(y + dy) * BASE.W + x + dx for dy, dx in offsets}

    BASE.mask = larger_mask


def worker(seed: int, morphology: str, frozen: dict) -> dict:
    before = manifest()
    if before != frozen:
        raise RuntimeError("worker inputs differ from source lock")
    prepare_base()
    result = BASE.run_case(seed, morphology)
    after = manifest()
    return {"pid": os.getpid(), "source_before": before, "source_after": after,
            "source_stable": before == after, "result": result}


def main() -> int:
    if sys.argv[1:2] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite v2.1 morphology-transfer artifacts")
        value = {"schema": "VisionEyeDenseMapMorphologyTransferV2_1Lock",
                 "inputs": manifest(), "seeds": list(SEEDS),
                 "morphologies": list(MORPHOLOGIES),
                 "train_sites": [list(x) for x in TRAIN_SITES],
                 "heldout_sites": [list(x) for x in HELDOUT_SITES],
                 "active_cells": {"square": 25, "cross": 9},
                 "exposures_per_site": BASE.EXPOSURE,
                 "probes_per_location": BASE.REPEATS}
        LOCK.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT).as_posix())
        return 0
    if sys.argv[1:2] == ["--worker"]:
        seed, morphology = int(sys.argv[2]), sys.argv[3]
        frozen = json.loads(LOCK.read_text())["inputs"]
        print(json.dumps(worker(seed, morphology, frozen), sort_keys=True))
        return 0

    if not LOCK.exists():
        raise SystemExit("missing v2.1 source lock; run --lock after protocol/runner are final")
    locked = json.loads(LOCK.read_text())
    if locked["inputs"] != manifest():
        raise SystemExit("stale v2.1 source lock")
    jobs = [(seed, morphology) for seed in SEEDS for morphology in MORPHOLOGIES]
    random.Random(20261007).shuffle(jobs)
    env = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"}
    def launch(job):
        seed, morphology = job
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(seed), morphology],
                              cwd=ROOT, env=env, text=True, capture_output=True)
        try:
            payload = json.loads(proc.stdout)
        except Exception:
            payload = None
        failure = None
        if proc.returncode:
            failure = {"seed": seed, "morphology": morphology, "returncode": proc.returncode,
                       "stderr_tail": proc.stderr[-2000:]}
        if payload is None:
            failure = failure or {"seed": seed, "morphology": morphology,
                                  "returncode": proc.returncode, "stdout_tail": proc.stdout[-2000:],
                                  "stderr_tail": proc.stderr[-2000:]}
        return ({"seed": seed, "morphology": morphology, "worker": payload} if payload else None), failure

    with ThreadPoolExecutor(max_workers=12) as pool:
        launched = list(pool.map(launch, jobs))
    rows = [row for row, _ in launched if row is not None]
    failures = [failure for _, failure in launched if failure is not None]
    prepare_base()
    post = manifest()
    results = [row["worker"]["result"] for row in rows]
    report = {
        "schema": "VisionEyeDenseMapMorphologyTransferV2_1Capture",
        "run_id": "vision-eye-phase0-dense-map-morphology-transfer-v2.1-20261005",
        "lock_path": str(LOCK.relative_to(ROOT)), "lock_sha256": sha(LOCK),
        "locked_inputs": locked["inputs"], "post_run_inputs": post,
        "worker_order": [[s, m] for s, m in jobs], "rows": rows,
        "process_failures": failures,
        "checks": {
            "source_stable": post == locked["inputs"] and all(x["worker"]["source_stable"] for x in rows),
            "twelve_workers": len(rows) == 12,
            "six_paired_seeds": len({x["seed"] for x in rows}) == 6 and all(sum(y["seed"] == s for y in rows) == 2 for s in SEEDS),
            "distinct_worker_pids": len({x["worker"]["pid"] for x in rows}) == len(rows),
            "correct_site_grid": all(x["worker"]["result"]["sites"] == [list(p) for p in TRAIN_SITES] and x["worker"]["result"]["heldout_sites"] == [list(p) for p in HELDOUT_SITES] for x in rows),
            "larger_masks_exact": all(all(p["active_count"] == (25 if x["morphology"] == "square" else 9) for p in x["worker"]["result"]["probes"]) for x in rows),
            "steps_and_exposures_exact": all(r["steps"] == 36000 and r["exposures_per_site"] == [4000] * 9 and r["switches"] == 8 for r in results),
            "probe_matrix_exact": all(len(r["probes"]) == 75 and all(sum(p["site_index"] == i for p in r["probes"]) == 3 for i in range(25)) for r in results),
            "unique_winners_and_frozen_weights": all(all(len(p["winners"]) == 1 for p in r["probes"]) and r["freeze_value"] == 1.0 and r["learned_fields"] == r["post_probe_fields"] for r in results),
            "expected_training_writes_and_progress": all(r["train_input_writes"] == BASE.expected_writes(r["morphology"]) and r["progress"] > 0 for row in rows for r in [row["worker"]["result"]]),
            "source_lock_current": not failures and post == locked["inputs"],
        },
    }
    report["passed"] = all(report["checks"].values())
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": report["passed"], "checks": report["checks"],
                      "workers": len(rows), "failures": len(failures),
                      "output": OUT.relative_to(ROOT).as_posix()}))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
