#!/usr/bin/env python3
"""Source-locked post-hoc numerical and tie analysis of the v1 live capture."""
from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evaluation/reports/vision_eye_corruption_live_replay_v1_3_analysis_20261005.json"
LOCK = ROOT / "evaluation/substrate_capability/vision_eye_corruption_live_replay_v1_3_analysis_lock_20261005.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_EYE_CORRUPTION_LIVE_REPLAY_V1_3_POSTHOC_ANALYSIS_PROTOCOL_20261005.md"
SCRIPT = Path(__file__).resolve()
FILES = {
    "capture": ROOT / "evaluation/reports/vision_eye_corruption_live_replay_v1_20261005.json",
    "capture_lock": ROOT / "evaluation/substrate_capability/vision_eye_corruption_live_replay_v1_lock_20261005.json",
    "v2_capture": ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_20261005.json",
    "v2_analysis": ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_analysis_20261005.json",
    "offline_reference": ROOT / "evaluation/reports/vision_eye_corruption_replay_posthoc_v1_2_20261005.json",
    "runner": ROOT / "evaluation/substrate_capability/vision_eye_corruption_live_replay_v1.py",
    "original_analyzer_current": ROOT / "evaluation/substrate_capability/analyze_vision_eye_corruption_live_replay_v1.py",
    "original_protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_EYE_CORRUPTION_LIVE_REPLAY_V1_PREREG_20261005.md",
    "original_amendment": ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_EYE_CORRUPTION_LIVE_REPLAY_V1_AMENDMENT_20261005.md",
}
MORPHOLOGIES = ("square", "cross")
CONDITIONS = ("drop_active_25pct", "drop_active_50pct", "drop_active_75pct",
              "add_background_25pct", "add_background_50pct")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest() -> dict:
    return {"analyzer_sha256": sha(SCRIPT), "protocol_sha256": sha(PROTOCOL),
            "files": {key: sha(path) for key, path in FILES.items()}}


def nearest(point, sites):
    distances = [math.dist(point, site) for site in sites]
    best = min(distances)
    return {i for i, d in enumerate(distances) if abs(d - best) < 1e-9}


def center(weights):
    mass = sum(weights)
    return (sum((i // 16) * value for i, value in enumerate(weights)) / mass,
            sum((i % 16) * value for i, value in enumerate(weights)) / mass)


def scores(fields, mask):
    return [sum(field["weights"][i] for i in mask) for field in fields]


def recreate_corruption(original, condition, fraction, seed_material):
    seed = int.from_bytes(hashlib.sha256(seed_material.encode()).digest()[:8], "big")
    rng = random.Random(seed)
    observed = set(original)
    if condition.startswith("drop_active"):
        count = max(1, round(len(original) * fraction))
        observed.difference_update(rng.sample(sorted(original), count))
    else:
        count = math.ceil(len(original) * fraction)
        inactive = sorted(set(range(256)) - original)
        observed.update(rng.sample(inactive, count))
    return observed


def analyze(lock):
    if manifest() != lock["inputs"]:
        raise SystemExit("post-hoc analysis inputs changed after lock")
    capture = json.loads(FILES["capture"].read_text())
    original_lock = json.loads(FILES["capture_lock"].read_text())
    v2 = json.loads(FILES["v2_capture"].read_text())
    v2a = json.loads(FILES["v2_analysis"].read_text())
    offline = json.loads(FILES["offline_reference"].read_text())
    if capture.get("lock_sha256") != sha(FILES["capture_lock"]):
        raise SystemExit("live capture does not match original lock")
    if capture.get("locked_inputs") != original_lock["inputs"] or capture.get("post_run_inputs") != original_lock["inputs"]:
        raise SystemExit("live capture source manifests differ")
    if not all(x.get("passed") for x in (capture, v2, v2a, offline)):
        raise SystemExit("a prerequisite capture/analysis did not pass")

    v2rows = {(int(r["seed"]), r["morphology"]): r["worker"]["result"] for r in v2["rows"]}
    live_rows = {(int(r["seed"]), r["morphology"]): r["worker"]["result"] for r in capture["rows"]}
    offline_rows = {(int(r["seed"]), r["morphology"], int(r["probe_index"]), r["condition"]): r
                    for r in offline["samples"]}
    checks = {"all_prerequisite_reports_pass": True,
              "original_capture_lock_matches": True,
              "capture_runner_was_source_locked": capture["locked_inputs"]["runner_sha256"] == sha(FILES["runner"]),
              "12_unique_workers_and_six_pairs": len(capture["rows"]) == 12 and len({r["worker"]["pid"] for r in capture["rows"]}) == 12 and set(live_rows) == set(v2rows),
              "weights_match_v2_1_exactly": True,
              "clean_outputs_match_v2_1_exactly": True,
              "all_3456_masks_match_offline": True,
              "all_3456_rows_join": True,
              "weights_unchanged_after_freeze": True,
              "activation_reconstruction_within_tolerance": True,
              "native_winners_within_one_ulp": True}
    groups = defaultdict(list)
    max_abs = max_rel = 0.0
    exact_native_max_count = 0
    native_single_vs_set_valued_disagreement = 0
    for key, live in live_rows.items():
        base = v2rows[key]
        checks["weights_match_v2_1_exactly"] &= live["learned_fields"] == base["learned_fields"]
        checks["weights_unchanged_after_freeze"] &= live["freeze_value"] == 1.0 and live["learned_fields"] == live["post_probe_fields"]
        checks["clean_outputs_match_v2_1_exactly"] &= len(live["clean_probes"]) == 75 and all(
            p["acts"] == base["probes"][int(p["probe_index"])]["acts"] and
            p["winners"] == base["probes"][int(p["probe_index"])]["winners"] and
            p["mask"] == base["probes"][int(p["probe_index"])]["mask"] for p in live["clean_probes"])
        region_by_unit = {int(f["unit"]): nearest(center(f["weights"]), live["sites"]) for f in live["learned_fields"]}
        checks["all_3456_rows_join"] &= len(live["corrupted_probes"]) == 240
        for row in live["corrupted_probes"]:
            ref = offline_rows.get((key[0], key[1], int(row["probe_index"]), row["condition"]))
            if ref is None:
                checks["all_3456_rows_join"] = False
                continue
            checks["all_3456_masks_match_offline"] &= hashlib.sha256(json.dumps(row["mask"]).encode()).hexdigest() == ref["scorer_input_mask_sha256"]["frozen_weight_readout"]
            clean_probe = base["probes"][int(row["probe_index"])]
            fraction = {"drop_active_25pct": 0.25, "drop_active_50pct": 0.50,
                        "drop_active_75pct": 0.75, "add_background_25pct": 0.25,
                        "add_background_50pct": 0.50}[row["condition"]]
            reconstructed_set = recreate_corruption(set(clean_probe["mask"]), row["condition"], fraction,
                f"phase0-v2.1|{key[0]}|{key[1]}|{row['probe_index']}|{row['condition']}")
            if sorted(reconstructed_set) != row["mask"]:
                checks["all_3456_masks_match_offline"] = False
            expected = scores(live["learned_fields"], reconstructed_set)
            tolerance_ok = len(expected) == len(row["acts"])
            for actual, calc in zip(row["acts"], expected):
                error = abs(actual - calc)
                max_abs = max(max_abs, error)
                rel = error / max(abs(actual), abs(calc)) if max(actual, calc) else 0.0
                max_rel = max(max_rel, rel)
                tolerance_ok &= error <= max(1e-300, 2e-15 * max(abs(actual), abs(calc)))
            checks["activation_reconstruction_within_tolerance"] &= tolerance_ok
            best = max(expected)
            exact = {i for i, score in enumerate(expected) if score == best}
            exact_native_max_count += int(bool(row["winners"]) and set(row["winners"]) <= exact)
            within_one_ulp = {i for i, score in enumerate(expected) if best - score <= math.ulp(best)}
            checks["native_winners_within_one_ulp"] &= bool(row["winners"]) and set(row["winners"]) <= within_one_ulp
            native_correct = bool(set().union(*(region_by_unit[i] for i in row["winners"])) & nearest(row["site"], live["sites"])) if row["winners"] else False
            exact_unit_correct = {i: bool(region_by_unit[i] & nearest(row["site"], live["sites"])) for i in exact}
            tie_ambiguous = len(set(exact_unit_correct.values())) > 1
            set_valued_correct = any(exact_unit_correct.values())
            native_single_vs_set_valued_disagreement += int(native_correct != ref["model_region_correct"])
            groups[(key[1], row["condition"])].append({"native_correct": native_correct,
                "set_valued_correct": set_valued_correct, "tie_ambiguous": tie_ambiguous,
                "exact_max_count": len(exact), "native_exact_max": bool(row["winners"]) and set(row["winners"]) <= exact})
    summaries = []
    for morphology in MORPHOLOGIES:
        for condition in CONDITIONS:
            rows = groups[(morphology, condition)]
            summaries.append({"morphology": morphology, "condition": condition, "probe_count": len(rows),
                "native_single_winner_correct": sum(x["native_correct"] for x in rows),
                "exact_max_set_valued_correct": sum(x["set_valued_correct"] for x in rows),
                "tie_ambiguous_probes": sum(x["tie_ambiguous"] for x in rows),
                "exact_max_tie_probes": sum(x["exact_max_count"] > 1 for x in rows),
                "native_exact_max_probes": sum(x["native_exact_max"] for x in rows)})
            checks["all_3456_rows_join"] &= len(rows) == 288
    return {"schema": "VisionEyeCorruptionLiveReplayV1_3PosthocAnalysis",
        "run_id": "vision-eye-corruption-live-replay-v1.3-posthoc-analysis-20261005",
        "analysis_lock_sha256": sha(LOCK), "inputs": lock["inputs"], "checks": checks,
        "passed": all(checks.values()), "confirmatory": False,
        "original_exact_max_gate": {"native_exact_max_probes": exact_native_max_count, "total_probes": 3456,
                                     "passed": exact_native_max_count == 3456},
        "max_activation_absolute_error": max_abs, "max_activation_relative_error": max_rel,
        "native_single_vs_offline_set_valued_disagreements": native_single_vs_set_valued_disagreement,
        "groups": summaries,
        "interpretation_boundary": "Post-hoc source-locked analysis of an existing live replay on synthetic absolute-position-coded masks. It characterizes numeric and tie semantics and is exploratory, not an independent robustness, semantic vision, or self-improvement result."}


def main():
    if sys.argv[1:2] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite post-hoc analysis artifacts")
        record = {"schema": "VisionEyeCorruptionLiveReplayV1_3PosthocAnalysisLock",
                  "inputs": manifest(), "policy": "post-hoc numerical and tie analysis; no new engine run"}
        LOCK.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT).as_posix())
        return 0
    if not LOCK.exists():
        raise SystemExit("missing analysis lock; run --lock first")
    lock = json.loads(LOCK.read_text())
    result = analyze(lock)
    if manifest() != lock["inputs"]:
        raise SystemExit("analysis sources changed during run")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": result["checks"],
        "exact_max": result["original_exact_max_gate"], "max_abs_error": result["max_activation_absolute_error"],
        "max_rel_error": result["max_activation_relative_error"],
        "native_vs_set_valued_disagreements": result["native_single_vs_offline_set_valued_disagreements"],
        "output": OUT.relative_to(ROOT).as_posix()}))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
