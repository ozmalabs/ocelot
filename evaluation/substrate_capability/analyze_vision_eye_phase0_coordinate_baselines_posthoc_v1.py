#!/usr/bin/env python3
"""Post-hoc coordinate baselines on the two phase-0 morphology captures."""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V1_CAPTURE = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v1_20261005.json"
V1_ANALYSIS = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v1_analysis_20261005.json"
V2_CAPTURE = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_20261005.json"
V2_ANALYSIS = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_analysis_20261005.json"
OUT = ROOT / "evaluation/reports/vision_eye_phase0_coordinate_baselines_posthoc_v1_20261005.json"
SCRIPT = Path(__file__).resolve()
WIDTH = 16


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nearest_sites(point, sites):
    distances = [math.dist(point, site) for site in sites]
    best = min(distances)
    return {i for i, distance in enumerate(distances) if abs(distance - best) < 1e-9}


def pixel_centroid(mask):
    coords = [(int(idx) // WIDTH, int(idx) % WIDTH) for idx in mask]
    return (sum(y for y, _ in coords) / len(coords),
            sum(x for _, x in coords) / len(coords))


def summarize(capture_path, analysis_path, version):
    capture = json.loads(capture_path.read_text())
    analysis = json.loads(analysis_path.read_text())
    if analysis.get("capture_sha256") != sha(capture_path):
        raise SystemExit(f"{version} analysis is stale relative to capture")
    if not capture.get("passed") or not analysis.get("passed"):
        raise SystemExit(f"{version} capture/analysis gates did not pass")
    model_workers = {(int(w["seed"]), str(w["morphology"])): w for w in analysis["workers"]}
    grouped = defaultdict(lambda: {"n": 0, "centroid_region_correct": 0,
                                   "centroid_exact_coordinate": 0,
                                   "mask_nn_region_correct": 0,
                                   "mask_nn_ambiguous": 0,
                                   "mask_nn_total_ties": 0,
                                   "substrate_region_correct": 0,
                                   "substrate_exact_localization": 0})
    rows = []
    raw_rows = capture["rows"]
    for raw in raw_rows:
        if version == "v1":
            seed, morphology = int(raw["seed"]), str(raw["morphology"])
            result = raw
        else:
            seed, morphology = int(raw["seed"]), str(raw["morphology"])
            result = raw["worker"]["result"]
        model = model_workers[(seed, morphology)]
        model_probes = model["probes"]
        sites = [tuple(map(float, xy)) for xy in result["sites"]]
        masks = [set(map(int, p["mask"])) for p in result["probes"]]
        active_counts = {len(m) for m in masks}
        if len(active_counts) != 1:
            raise SystemExit(f"unexpected mixed mask areas in {version}/{seed}/{morphology}")
        # Same-layout training exemplars are generated from the task's declared
        # shape at the nine training coordinates; only input pixels are used.
        exemplar_masks = []
        radius = 1 if version == "v1" else 2
        for y, x in sites:
            y, x = int(y), int(x)
            if morphology == "square":
                offsets = [(dy, dx) for dy in range(-radius, radius + 1)
                           for dx in range(-radius, radius + 1)]
            elif radius == 1:
                offsets = [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]
            else:
                offsets = [(0, 0)] + [point for r in (1, 2)
                                      for point in ((0, -r), (0, r), (-r, 0), (r, 0))]
            exemplar_masks.append({(y + dy) * WIDTH + x + dx for dy, dx in offsets})
        if any(len(mask) != next(iter(active_counts)) for mask in exemplar_masks):
            raise SystemExit(f"baseline exemplar size disagrees with capture in {version}/{seed}/{morphology}")

        for probe, model_probe in zip(result["probes"], model_probes):
            mask = set(map(int, probe["mask"]))
            point = pixel_centroid(mask)
            true_regions = nearest_sites(tuple(map(float, probe["site"])), sites)
            centroid_regions = nearest_sites(point, sites)
            distances = [len(mask ^ exemplar) for exemplar in exemplar_masks]
            best = min(distances)
            nn_regions = {i for i, distance in enumerate(distances) if distance == best}
            key = (version, morphology, str(probe["location_status"]))
            agg = grouped[key]
            agg["n"] += 1
            agg["centroid_region_correct"] += bool(centroid_regions & true_regions)
            agg["centroid_exact_coordinate"] += math.dist(point, probe["site"]) < 1e-9
            agg["mask_nn_region_correct"] += bool(nn_regions & true_regions)
            agg["mask_nn_ambiguous"] += len(nn_regions) > 1
            agg["mask_nn_total_ties"] += len(nn_regions)
            agg["substrate_region_correct"] += bool(model_probe.get("nearest_region_correct", False))
            # v1's analysis calls this exact localization but uses spread < 3
            # and center distance < 1. V2.1 retains that scoring convention.
            exact_key = ("winner_localized_to_probe" if version == "v1"
                         else "exact_coordinate_localization")
            agg["substrate_exact_localization"] += bool(model_probe.get(exact_key, False))
            rows.append({
                "version": version, "seed": seed, "morphology": morphology,
                "location_status": probe["location_status"], "site": list(probe["site"]),
                "active_pixel_count": len(mask), "pixel_centroid": list(point),
                "centroid_coordinate_error": math.dist(point, probe["site"]),
                "centroid_region_correct": bool(centroid_regions & true_regions),
                "mask_nn_min_hamming_distance": best,
                "mask_nn_tied_site_indices": sorted(nn_regions),
                "mask_nn_region_correct": bool(nn_regions & true_regions),
                "substrate_region_correct": bool(model_probe.get("nearest_region_correct", False)),
                "substrate_within_one_cell_localization": bool(model_probe.get(exact_key, False)),
            })
    groups = []
    for (version, morphology, status), values in sorted(grouped.items()):
        groups.append({"version": version, "morphology": morphology,
                       "location_status": status, **values})
    published_groups = {}
    for item in analysis["groups"]:
        if version == "v1":
            model_correct = item["nearest_region_correct_count"]
            model_exact = item["exact_localization_count"]
        else:
            model_correct = item["nearest_region_correct"]
            model_exact = item["exact_coordinate_localization"]
        published_groups[(item["morphology"], item["location_status"])] = (model_correct, model_exact)
    reconciles = all(
        published_groups[(g["morphology"], g["location_status"])]
        == (g["substrate_region_correct"], g["substrate_exact_localization"])
        for g in groups
    )
    return groups, rows, reconciles


def main() -> int:
    before = sha(SCRIPT)
    groups_v1, rows_v1, model_reconciles_v1 = summarize(V1_CAPTURE, V1_ANALYSIS, "v1")
    groups_v2, rows_v2, model_reconciles_v2 = summarize(V2_CAPTURE, V2_ANALYSIS, "v2.1")
    checks = {
        "both_source_locked_panels_pass": True,
        "all_1800_probe_rows_reconciled": len(rows_v1) + len(rows_v2) == 1800,
        "all_centroids_recover_stimulus_coordinates": all(r["centroid_coordinate_error"] < 1e-9 for r in rows_v1 + rows_v2),
        "all_centroid_and_mask_nn_regions_match_geometry": all(r["centroid_region_correct"] and r["mask_nn_region_correct"] for r in rows_v1 + rows_v2),
        "substrate_scores_reconcile_to_published_analyses": model_reconciles_v1 and model_reconciles_v2,
        "analyzer_source_stable": before == sha(SCRIPT),
    }
    result = {
        "schema": "VisionEyeCoordinateBaselinesPosthocV1",
        "run_id": "vision-eye-coordinate-baselines-posthoc-v1-20261005",
        "posthoc": True,
        "inputs": {"v1_capture_sha256": sha(V1_CAPTURE), "v1_analysis_sha256": sha(V1_ANALYSIS),
                   "v2_1_capture_sha256": sha(V2_CAPTURE), "v2_1_analysis_sha256": sha(V2_ANALYSIS),
                   "analyzer_sha256": before},
        "checks": checks, "passed": all(checks.values()),
        "groups": groups_v1 + groups_v2,
        "probe_rows": rows_v1 + rows_v2,
        "baseline_definitions": {
            "active_pixel_centroid": "Compute the mean row and column of active retinal pixels, then assign the nearest trained-site region. This baseline directly exploits absolute pixel position in the stimulus.",
            "training_mask_hamming_nn": "Choose the training-site stimulus mask(s) with minimum symmetric-difference pixel count; score a tied set correct if any tied site belongs to the true nearest-site region.",
        },
        "claim_boundary": "Post-hoc controls on the already measured synthetic retinotopy tasks. The perfect centroid baseline demonstrates that absolute location is directly available in the pixel mask; it does not show general visual recognition or a learned coordinate representation. The Hamming baseline shares the authored mask family. Baselines are not independent natural tasks.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": checks,
                      "groups": groups_v1 + groups_v2,
                      "output": OUT.relative_to(ROOT).as_posix()}))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
