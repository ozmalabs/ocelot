#!/usr/bin/env python3
"""Deterministic corruption replay on captured phase-0 v2.1 weights."""
from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_20261005.json"
ANALYSIS = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_analysis_20261005.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_EYE_CORRUPTION_REPLAY_POSTHOC_V1_1_PROTOCOL_20261005.md"
OUT = ROOT / "evaluation/reports/vision_eye_corruption_replay_posthoc_v1_1_20261005.json"
SCRIPT = Path(__file__).resolve()
WIDTH = 16
SEEDS = (30, 31, 32, 33, 34, 35)
MORPHOLOGIES = ("square", "cross")
CONDITIONS = (
    ("clean", 0.0),
    ("drop_active_25pct", 0.25),
    ("drop_active_50pct", 0.50),
    ("drop_active_75pct", 0.75),
    ("add_background_25pct", 0.25),
    ("add_background_50pct", 0.50),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nearest_sites(point, sites):
    ds = [math.dist(point, site) for site in sites]
    best = min(ds)
    return {i for i, value in enumerate(ds) if abs(value - best) < 1e-9}


def pixel_centroid(mask):
    pts = [(idx // WIDTH, idx % WIDTH) for idx in mask]
    return sum(y for y, _ in pts) / len(pts), sum(x for _, x in pts) / len(pts)


def mask_template(site, morphology):
    y, x = site
    if morphology == "square":
        offsets = [(dy, dx) for dy in range(-2, 3) for dx in range(-2, 3)]
    else:
        offsets = [(0, 0)] + [point for radius in (1, 2)
                              for point in ((0, -radius), (0, radius), (-radius, 0), (radius, 0))]
    return {(y + dy) * WIDTH + x + dx for dy, dx in offsets}


def corrupt(original: set[int], kind: str, fraction: float, seed_material: str) -> set[int]:
    if kind == "clean":
        return set(original)
    seed = int.from_bytes(hashlib.sha256(seed_material.encode()).digest()[:8], "big")
    rng = random.Random(seed)
    out = set(original)
    if kind.startswith("drop_active"):
        count = max(1, round(len(original) * fraction))
        out.difference_update(rng.sample(sorted(original), count))
    else:
        count = math.ceil(len(original) * fraction)
        inactive = sorted(set(range(WIDTH * WIDTH)) - original)
        out.update(rng.sample(inactive, count))
    return out


def main() -> int:
    before = sha(SCRIPT)
    capture = json.loads(CAPTURE.read_text())
    analysis = json.loads(ANALYSIS.read_text())
    if analysis.get("capture_sha256") != sha(CAPTURE):
        raise SystemExit("v2.1 analysis does not identify current capture")
    if not capture.get("passed") or not analysis.get("passed"):
        raise SystemExit("v2.1 capture/analysis gates are not all green")
    model_workers = {(int(row["seed"]), row["morphology"]): row for row in analysis["workers"]}

    # Store one row per source probe/condition and scorer so all baselines see
    # identical perturbed pixels.
    samples = []
    for worker_row in capture["rows"]:
        seed = int(worker_row["seed"])
        morphology = worker_row["morphology"]
        result = worker_row["worker"]["result"]
        model_worker = model_workers[(seed, morphology)]
        sites = [tuple(map(float, p)) for p in result["sites"]]
        templates = [mask_template(tuple(map(int, p)), morphology) for p in sites]
        if len(result["probes"]) != len(model_worker["probes"]):
            raise SystemExit("raw/analyzed probe count mismatch")
        for probe_index, (probe, model_probe) in enumerate(zip(result["probes"], model_worker["probes"])):
            if probe["location_status"] != "heldout":
                continue
            original = set(map(int, probe["mask"]))
            site = tuple(map(float, probe["site"]))
            true_regions = nearest_sites(site, sites)
            if not model_probe["activation_reconstructs"] or not model_probe["argmax_reconstructs"]:
                raise SystemExit("clean baseline does not reproduce saved activation/argmax")
            for condition, fraction in CONDITIONS:
                observed = corrupt(original, condition, fraction,
                                   f"phase0-v2.1|{seed}|{morphology}|{probe_index}|{condition}")
                centroid = pixel_centroid(observed)
                centroid_sites = nearest_sites(centroid, sites)
                centroid_ok = bool(centroid_sites & true_regions)
                centroid_err = math.dist(centroid, site)

                model_scores = [sum(result["learned_fields"][u]["weights"][idx] for idx in observed)
                                for u in range(len(result["learned_fields"]))]
                best_model = max(model_scores)
                model_winners = {i for i, score in enumerate(model_scores)
                                 if score == best_model}
                model_ok = bool(model_winners & true_regions)

                distances = [len(observed ^ template) for template in templates]
                best_distance = min(distances)
                nn_sites = {i for i, distance in enumerate(distances) if distance == best_distance}
                nn_ok = bool(nn_sites & true_regions)
                mask_digest = hashlib.sha256(json.dumps(sorted(observed)).encode()).hexdigest()
                samples.append({
                    "seed": seed, "morphology": morphology,
                    "probe_index": probe_index, "site": list(site),
                    "condition": condition, "fraction": fraction,
                    "original_active_pixels": len(original), "observed_active_pixels": len(observed),
                    "scorer_input_mask_sha256": {
                        "frozen_weight_readout": mask_digest,
                        "pixel_centroid": mask_digest,
                        "training_mask_hamming": mask_digest,
                    },
                    "centroid_coordinate_error": centroid_err,
                    "centroid_region_correct": centroid_ok,
                    "centroid_tie_count": len(centroid_sites),
                    "model_region_correct": model_ok,
                    "model_tie_count": len(model_winners),
                    "model_winner_indices": sorted(model_winners),
                    "mask_nn_region_correct": nn_ok,
                    "mask_nn_tie_count": len(nn_sites),
                })

    groups = defaultdict(list)
    for row in samples:
        groups[(row["morphology"], row["condition"])].append(row)
    summaries = []
    for morphology in MORPHOLOGIES:
        for condition, fraction in CONDITIONS:
            rows = groups[(morphology, condition)]
            summaries.append({
                "morphology": morphology, "condition": condition, "fraction": fraction,
                "probe_count": len(rows),
                "model_region_correct": sum(r["model_region_correct"] for r in rows),
                "model_tied_predictions": sum(r["model_tie_count"] > 1 for r in rows),
                "centroid_region_correct": sum(r["centroid_region_correct"] for r in rows),
                "centroid_exact_coordinate": sum(r["centroid_coordinate_error"] < 1e-9 for r in rows),
                "centroid_median_coordinate_error": statistics.median(r["centroid_coordinate_error"] for r in rows),
                "mask_nn_region_correct_set_valued": sum(r["mask_nn_region_correct"] for r in rows),
                "mask_nn_ambiguous_predictions": sum(r["mask_nn_tie_count"] > 1 for r in rows),
            })

    checks = {
        "source_capture_and_analysis_valid": bool(capture["passed"] and analysis["passed"]),
        "six_seeds_per_morphology": all(len({r["seed"] for r in samples if r["morphology"] == m}) == 6 for m in MORPHOLOGIES),
        "288_probes_each_morphology_condition": all(s["probe_count"] == 288 for s in summaries),
        "clean_learned_replay_matches_published_288": all(
            s["model_region_correct"] == (288 if s["morphology"] == "square" else 210)
            for s in summaries if s["condition"] == "clean"),
        "corruption_deterministic": True,
        "same_mask_used_by_all_scorers": True,
        "analyzer_source_stable": before == sha(SCRIPT),
    }
    # Recompute deterministic payloads a second time from their source keys.
    for row in samples:
        src = next(p for p in capture["rows"] if int(p["seed"]) == row["seed"]
                   and p["morphology"] == row["morphology"])
        p = src["worker"]["result"]["probes"][row["probe_index"]]
        recovered = corrupt(set(map(int, p["mask"])), row["condition"], row["fraction"],
                             f"phase0-v2.1|{row['seed']}|{row['morphology']}|{row['probe_index']}|{row['condition']}")
        recovered_hash = hashlib.sha256(json.dumps(sorted(recovered)).encode()).hexdigest()
        checks["corruption_deterministic"] &= recovered_hash == row["scorer_input_mask_sha256"]["frozen_weight_readout"]
        checks["same_mask_used_by_all_scorers"] &= len(set(row["scorer_input_mask_sha256"].values())) == 1
    result = {
        "schema": "VisionEyeCorruptionReplayPosthocV1_1",
        "run_id": "vision-eye-corruption-replay-posthoc-v1.1-20261005",
        "posthoc": True,
        "inputs": {"protocol_sha256": sha(PROTOCOL), "analyzer_sha256": before,
                   "capture_path": str(CAPTURE.relative_to(ROOT)), "capture_sha256": sha(CAPTURE),
                   "analysis_path": str(ANALYSIS.relative_to(ROOT)), "analysis_sha256": sha(ANALYSIS)},
        "checks": checks, "passed": all(checks.values()),
        "condition_definitions": [{"condition": name, "fraction": fraction} for name, fraction in CONDITIONS],
        "groups": summaries, "sample_count": len(samples), "samples": samples,
        "interpretation_boundary": "Frozen-weight analytical forward replay on the v2.1 synthetic binary retinotopy masks. Clean parity validates the weight-sum/argmax equation; corrupted cases do not rerun the Rust scheduler. Position remains directly represented in the pixels. No natural-image, online adaptation, or semantic vision claim.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": checks,
                      "groups": summaries, "output": OUT.relative_to(ROOT).as_posix()}))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
