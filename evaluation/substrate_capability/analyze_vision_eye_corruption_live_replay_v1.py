#!/usr/bin/env python3
"""Independent parity analysis for the live phase-0 corruption replay."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import assert_measuring_engine

RUNNER = ROOT / "evaluation/substrate_capability/vision_eye_corruption_live_replay_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/vision_eye_corruption_live_replay_v1_lock_20261005.json"
CAPTURE = ROOT / "evaluation/reports/vision_eye_corruption_live_replay_v1_20261005.json"
V2_CAPTURE = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_20261005.json"
V2_ANALYSIS = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_analysis_20261005.json"
OFFLINE = ROOT / "evaluation/reports/vision_eye_corruption_replay_posthoc_v1_2_20261005.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_EYE_CORRUPTION_LIVE_REPLAY_V1_PREREG_20261005.md"
OUT = ROOT / "evaluation/reports/vision_eye_corruption_live_replay_v1_analysis_20261005.json"
SCRIPT = Path(__file__).resolve()
MORPHOLOGIES = ("square", "cross")
CONDITIONS = ("drop_active_25pct", "drop_active_50pct", "drop_active_75pct",
              "add_background_25pct", "add_background_50pct")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nearest_regions(point, sites):
    distances = [math.dist(point, site) for site in sites]
    best = min(distances)
    return {i for i, d in enumerate(distances) if abs(d - best) < 1e-9}


def expected_acts(fields, mask):
    return [sum(field["weights"][i] for i in mask) for field in fields]


def receptive_center(weights):
    mass = sum(weights)
    return (sum((i // 16) * w for i, w in enumerate(weights)) / mass,
            sum((i % 16) * w for i, w in enumerate(weights)) / mass)


def main() -> int:
    analyzer_sha = sha(SCRIPT)
    lock = json.loads(LOCK.read_text())
    capture = json.loads(CAPTURE.read_text())
    v2 = json.loads(V2_CAPTURE.read_text())
    v2_analysis = json.loads(V2_ANALYSIS.read_text())
    offline = json.loads(OFFLINE.read_text())
    sources_valid = bool(capture.get("passed") and v2.get("passed") and
                         v2_analysis.get("passed") and offline.get("passed"))
    if not sources_valid:
        raise SystemExit("a prerequisite capture or analysis did not pass")
    if capture.get("lock_sha256") != sha(LOCK):
        raise SystemExit("capture does not identify current source lock")
    if capture.get("locked_inputs") != lock["inputs"] or capture.get("post_run_inputs") != lock["inputs"]:
        raise SystemExit("capture source manifest mismatch")
    provenance = assert_measuring_engine()
    if provenance["source_fingerprint"] != lock["inputs"]["engine_fingerprint"]:
        raise SystemExit("engine fingerprint differs from locked source")

    original = {(int(r["seed"]), r["morphology"]): r["worker"]["result"] for r in v2["rows"]}
    live_rows = {(int(r["seed"]), r["morphology"]): r["worker"]["result"] for r in capture["rows"]}
    offline_samples = {(int(s["seed"]), s["morphology"], int(s["probe_index"]), s["condition"]): s
                       for s in offline["samples"]}
    checks = {
        "prerequisite_captures_valid": sources_valid,
        "twelve_unique_worker_processes": len(capture["rows"]) == 12 and len({r["worker"]["pid"] for r in capture["rows"]}) == 12,
        "complete_seed_morphology_pairs": set(live_rows) == set(original) and len(live_rows) == 12,
        "capture_runner_source_locked": lock["inputs"]["runner_sha256"] == sha(RUNNER),
        "analyzer_source_stable": analyzer_sha == sha(SCRIPT),
        "worker_source_stable": all(r["worker"]["source_stable"] for r in capture["rows"]),
        "training_schedule_exact": all(r["steps"] == 36000 and r["exposures_per_site"] == [4000] * 9 and r["switches"] == 8 for r in live_rows.values()),
        "weights_match_v2_1": True,
        "clean_live_readout_matches_v2_1": True,
        "live_acts_match_weight_sums": True,
        "live_winners_within_exact_max_set": True,
        "corruption_masks_match_offline": True,
        "weights_unchanged_after_frozen_probes": all(r["learned_fields"] == r["post_probe_fields"] and r["freeze_value"] == 1.0 for r in live_rows.values()),
        "all_corruption_probe_rows_joined": True,
    }
    groups = defaultdict(list)
    max_activation_abs_error = 0.0
    native_winner_one_ulp_cases = 0
    native_vs_set_valued_region_disagreements = 0
    for key, live in live_rows.items():
        base = original[key]
        checks["weights_match_v2_1"] &= live["learned_fields"] == base["learned_fields"]
        if len(live["clean_probes"]) != 75 or len(live["corrupted_probes"]) != 240:
            checks["all_corruption_probe_rows_joined"] = False
        for clean in live["clean_probes"]:
            expected = base["probes"][int(clean["probe_index"])]
            checks["clean_live_readout_matches_v2_1"] &= (clean["mask"] == expected["mask"] and
                clean["winners"] == expected["winners"] and clean["acts"] == expected["acts"])
        field_regions = {int(f["unit"]): nearest_regions(receptive_center(f["weights"]), live["sites"])
                         for f in live["learned_fields"]}
        for row in live["corrupted_probes"]:
            idx = int(row["probe_index"])
            cond = row["condition"]
            expected = offline_samples.get((key[0], key[1], idx, cond))
            if expected is None:
                checks["all_corruption_probe_rows_joined"] = False
                continue
            digest = hashlib.sha256(json.dumps(row["mask"]).encode()).hexdigest()
            checks["corruption_masks_match_offline"] &= digest == expected["scorer_input_mask_sha256"]["frozen_weight_readout"]
            scores = expected_acts(live["learned_fields"], row["mask"])
            err = max((abs(a - b) for a, b in zip(row["acts"], scores)), default=0.0)
            max_activation_abs_error = max(max_activation_abs_error, err)
            checks["live_acts_match_weight_sums"] &= len(row["acts"]) == len(scores) and err <= 1e-9
            best = max(scores)
            exact_max = {i for i, score in enumerate(scores) if score == best}
            checks["live_winners_within_exact_max_set"] &= bool(row["winners"]) and set(row["winners"]) <= exact_max
            if row["winners"] and any(best - scores[i] == math.ulp(best) for i in row["winners"]):
                native_winner_one_ulp_cases += 1
            regions = set().union(*(field_regions[i] for i in row["winners"])) if row["winners"] else set()
            true_regions = nearest_regions(row["site"], live["sites"])
            correct = bool(regions & true_regions)
            native_vs_set_valued_region_disagreements += correct != expected["model_region_correct"]
            groups[(key[1], cond)].append({"correct": correct, "tie": len(row["winners"]) > 1,
                                           "seed": key[0], "probe_index": idx})
    summaries = []
    for morphology in MORPHOLOGIES:
        for condition in CONDITIONS:
            rows = groups[(morphology, condition)]
            summaries.append({"morphology": morphology, "condition": condition,
                "probe_count": len(rows), "region_correct": sum(x["correct"] for x in rows),
                "tied_winner_probes": sum(x["tie"] for x in rows)})
            checks["all_corruption_probe_rows_joined"] &= len(rows) == 288
    checks["runner_capture_claims_pass"] = bool(capture.get("passed"))
    result = {"schema": "VisionEyeCorruptionLiveReplayV1Analysis", "run_id": "vision-eye-corruption-live-replay-v1-analysis-20261005",
        "capture_sha256": sha(CAPTURE), "lock_sha256": sha(LOCK), "analyzer_sha256": analyzer_sha,
        "locked_analyzer_sha256": lock["inputs"]["analyzer_sha256"],
        "analysis_amended_after_capture": lock["inputs"]["analyzer_sha256"] != analyzer_sha,
        "protocol_sha256": sha(PROTOCOL), "checks": checks, "passed": all(checks.values()),
        "max_activation_absolute_error": max_activation_abs_error,
        "diagnostics": {"native_winner_one_ulp_cases": native_winner_one_ulp_cases,
                        "native_vs_offline_set_valued_region_disagreements": native_vs_set_valued_region_disagreements},
        "groups": summaries,
        "interpretation_boundary": "Live Rust graph-rule replay of deterministic corruption masks for the frozen v2.1 synthetic retinotopy map. This checks live scheduler/readout parity and does not establish independent robustness, online adaptation, natural-image recognition, or semantic vision."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": checks, "max_activation_absolute_error": max_activation_abs_error,
                      "groups": summaries, "output": OUT.relative_to(ROOT).as_posix()}))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
