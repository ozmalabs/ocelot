#!/usr/bin/env python3
"""Independent activation and held-out transfer analysis for phase-0 v2."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_20261005.json"
ANALYSIS = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_analysis_20261005.json"
LOCK = ROOT / "evaluation/substrate_capability/vision_eye_phase0_dense_map_morphology_transfer_v2_lock_20261005.json"
BASE_ANALYZER = ROOT / "evaluation/substrate_capability/analyze_vision_eye_phase0_dense_map_morphology_transfer_v1.py"
SPEC = importlib.util.spec_from_file_location("phase0_morphology_analyzer_v1", BASE_ANALYZER)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BASE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    before = sha(Path(__file__).resolve())
    capture = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    workers, all_probe_checks = [], []
    for row in capture["rows"]:
        result = row["worker"]["result"]
        sites = [tuple(site) for site in result["sites"]]
        fields = result["learned_fields"]
        reconstructed = []
        for field in fields:
            center, spread = BASE.center_spread(field["weights"])
            reconstructed.append({"unit": field["unit"], "center": center, "spread": spread,
                                  "localized_to_training_region": spread < 3 and min(math.dist(center, site) for site in sites) < 1,
                                  "nearest_site_regions": BASE.nearest_regions(center, sites)})
        probes = []
        for probe in result["probes"]:
            activations = [sum(field["weights"][idx] for idx in probe["mask"]) for field in fields]
            winner = probe["winners"][0] if len(probe["winners"]) == 1 else None
            true_regions = BASE.nearest_regions(tuple(probe["site"]), sites)
            winner_regions = reconstructed[winner]["nearest_site_regions"] if winner is not None else []
            activation_match = all(abs(a - b) < 1e-6 for a, b in zip(activations, probe["acts"]))
            argmax_match = winner is not None and activations[winner] >= max(activations) - 1e-9
            probe_row = {
                "site": probe["site"], "site_index": probe["site_index"],
                "location_status": probe["location_status"], "winner": winner,
                "nearest_region_correct": bool(set(winner_regions) & set(true_regions)),
                "exact_coordinate_localization": winner is not None and reconstructed[winner]["spread"] < 3 and math.dist(reconstructed[winner]["center"], probe["site"]) < 1,
                "center_distance": math.dist(reconstructed[winner]["center"], probe["site"]) if winner is not None else None,
                "activation_reconstructs": activation_match, "argmax_reconstructs": argmax_match,
            }
            all_probe_checks.append(activation_match and argmax_match)
            probes.append(probe_row)
        workers.append({
            "seed": row["seed"], "morphology": row["morphology"],
            "active_cells_per_probe": 25 if row["morphology"] == "square" else 9,
            "trained_sites_covered_by_fields": len({i for f in reconstructed if f["localized_to_training_region"] for i in f["nearest_site_regions"]}),
            "train_closure_ns": result["train_closure_ns"],
            "probe_closure_ns": result["probe_closure_ns"],
            "probes": probes,
        })

    groups = []
    for morphology in ("square", "cross"):
        for status in ("trained", "heldout"):
            selected = [p for w in workers if w["morphology"] == morphology
                        for p in w["probes"] if p["location_status"] == status]
            groups.append({
                "morphology": morphology, "location_status": status,
                "worker_count": sum(w["morphology"] == morphology for w in workers),
                "probe_count": len(selected),
                "nearest_region_correct": sum(p["nearest_region_correct"] for p in selected),
                "exact_coordinate_localization": sum(p["exact_coordinate_localization"] for p in selected),
                "median_center_distance": statistics.median(p["center_distance"] for p in selected),
                "median_probe_closure_ns_per_worker": statistics.median(
                    w["probe_closure_ns"] for w in workers if w["morphology"] == morphology
                ),
            })
    paired = []
    for seed in range(30, 36):
        conditions = []
        for morphology in ("square", "cross"):
            worker = next(w for w in workers if w["seed"] == seed and w["morphology"] == morphology)
            held = [p for p in worker["probes"] if p["location_status"] == "heldout"]
            conditions.append({"morphology": morphology,
                               "heldout_correct": sum(p["nearest_region_correct"] for p in held),
                               "heldout_total": len(held)})
        paired.append({"seed": seed, "conditions": conditions,
                       "cross_minus_square": conditions[1]["heldout_correct"] - conditions[0]["heldout_correct"]})

    checks = {
        "capture_passed": capture.get("passed") and all(capture["checks"].values()),
        "source_lock_matches_capture": capture["locked_inputs"] == lock["inputs"] == capture["post_run_inputs"],
        "analyzer_stable": before == sha(Path(__file__).resolve()),
        "twelve_workers_and_six_pairs": len(workers) == 12 and len(paired) == 6,
        "all_900_activations_and_winners_reconstruct": len(all_probe_checks) == 900 and all(all_probe_checks),
        "all_workers_cover_all_nine_training_regions": all(w["trained_sites_covered_by_fields"] == 9 for w in workers),
        "all_workers_have_75_probes": all(len(w["probes"]) == 75 for w in workers),
    }
    prior = json.loads((ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v1_analysis_20261005.json").read_text())
    analysis = {
        "schema": "VisionEyeDenseMapMorphologyTransferV2Analysis",
        "run_id": "vision-eye-phase0-dense-map-morphology-transfer-v2-analysis-20261005",
        "capture_sha256": sha(CAPTURE), "lock_sha256": sha(LOCK),
        "analyzer_sha256": before,
        "checks": checks, "passed": all(checks.values()),
        "groups": groups, "paired_seed_comparison": paired, "workers": workers,
        "v1_reference": {
            "analysis_sha256": sha(ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v1_analysis_20261005.json"),
            "heldout_nearest_region": {g["morphology"]: g["nearest_region_correct_count"] for g in prior["groups"] if g["location_status"] == "heldout"},
            "heldout_total_per_morphology": 288,
        },
        "claim_limit": "One authored phase-0 learner on one shifted 3x3 site grid and one larger patch span. Morphology and active-cell count change together; a result cannot isolate which caused transfer. It is not semantic or natural-image vision evidence.",
    }
    ANALYSIS.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": analysis["passed"], "checks": checks,
                      "groups": groups, "paired": paired,
                      "output": ANALYSIS.relative_to(ROOT).as_posix()}))
    return 0 if analysis["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
