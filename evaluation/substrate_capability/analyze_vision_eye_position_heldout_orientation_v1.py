#!/usr/bin/env python3
"""Independent analysis of position-held-out orientation representation."""
from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/vision_eye_position_heldout_orientation_v1_20261005.json"
LOCK = ROOT / "evaluation/substrate_capability/vision_eye_position_heldout_orientation_v1_lock_20261005.json"
SCRIPT = Path(__file__).resolve()
RUNNER = ROOT / "evaluation/substrate_capability/vision_eye_position_heldout_orientation_v1.py"
OUT = ROOT / "evaluation/reports/vision_eye_position_heldout_orientation_v1_analysis_20261005.json"
SEEDS = (40, 41, 42, 43, 44, 45)
TRAIN_SITES = tuple((y, x) for y in (3, 6, 9, 12) for x in (3, 6, 9, 12)
                    if (y, x) not in ((3, 3), (3, 12), (12, 3), (12, 12)))
HELDOUT = ((3, 3), (3, 12), (12, 3), (12, 12))
LABELS = ("horizontal", "vertical")
W = 16
EXPOSURES = 400
STEPS = len(TRAIN_SITES) * len(LABELS) * EXPOSURES


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mask(site, label):
    y, x = site
    coords = {(y, x + dx) for dx in (-2, -1, 0, 1, 2)} if label == "horizontal" else {
        (y + dy, x) for dy in (-2, -1, 0, 1, 2)}
    return sorted(yy * W + xx for yy, xx in coords)


def centroid(indices):
    return (sum(i // W for i in indices) / len(indices),
            sum(i % W for i in indices) / len(indices))


def reconstruct_schedule(seed):
    schedule = [(site, label) for site in TRAIN_SITES for label in LABELS for _ in range(EXPOSURES)]
    random.Random(610_000 + seed).shuffle(schedule)
    digest = hashlib.sha256()
    for site, label in schedule:
        digest.update(json.dumps([list(site), label], separators=(",", ":")).encode())
    return schedule, digest.hexdigest()


def activation(fields, indices):
    return [sum(field["weights"][i] for i in indices) for field in fields]


def predict_nearest_mean(train, vector):
    means = {}
    for label in LABELS:
        examples = [row["acts"] for row in train if row["label"] == label]
        means[label] = [sum(v[i] for v in examples) / len(examples) for i in range(len(vector))]
    distances = {label: sum((a - b) ** 2 for a, b in zip(vector, means[label])) for label in LABELS}
    return min(LABELS, key=lambda label: (distances[label], LABELS.index(label))), distances


def main():
    capture = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    if capture.get("lock_sha256") != sha(LOCK):
        raise SystemExit("capture does not match the current source lock")
    if capture.get("locked_inputs") != lock["inputs"] or capture.get("post_run_inputs") != lock["inputs"]:
        raise SystemExit("capture source manifest mismatch")
    if not capture.get("passed"):
        raise SystemExit("runtime capture gates did not pass")
    analyzer_sha = sha(SCRIPT)
    rows = []
    checks = {"capture_source_lock_matches": True,
        "six_workers_and_seed_set": len(capture["workers"]) == 6 and sorted(w["result"]["seed"] for w in capture["workers"]) == list(SEEDS),
        "unique_worker_processes": len({w["pid"] for w in capture["workers"]}) == 6,
        "schedule_hash_and_exposure_reconstructed": True,
        "probe_masks_labels_and_centroids_exact": True,
        "position_split_exact_and_disjoint": True,
        "each_seed_has_eight_heldout_probes": True,
        "runner_and_analyzer_hashes_match_lock": capture["locked_inputs"]["runner_sha256"] == sha(RUNNER) and capture["locked_inputs"]["analyzer_sha256"] == sha(SCRIPT),
        "analyzer_source_stable": True}
    all_correct = Counter()
    per_seed = []
    for worker in sorted(capture["workers"], key=lambda w: w["result"]["seed"]):
        r = worker["result"]
        seed = int(r["seed"])
        schedule, expected_hash = reconstruct_schedule(seed)
        checks["schedule_hash_and_exposure_reconstructed"] &= r["schedule_sha256"] == expected_hash and r["steps"] == STEPS
        expected_exposures = Counter({f"{y},{x}:{label}": EXPOSURES for y, x in TRAIN_SITES for label in LABELS})
        checks["schedule_hash_and_exposure_reconstructed"] &= Counter(r["exposures"]) == expected_exposures
        checks["position_split_exact_and_disjoint"] &= tuple(map(tuple, r["train_sites"])) == TRAIN_SITES and tuple(map(tuple, r["heldout_sites"])) == HELDOUT and not (set(map(tuple, r["train_sites"])) & set(map(tuple, r["heldout_sites"])))
        by_label_center = {}
        for p in r["probes"]:
            site, label = tuple(p["site"]), p["label"]
            expected_mask = mask(site, label)
            checks["probe_masks_labels_and_centroids_exact"] &= p["mask"] == expected_mask and p["active_count"] == 5 and len(set(p["mask"])) == 5
            by_label_center[(site, label)] = p
            if site in HELDOUT:
                checks["probe_masks_labels_and_centroids_exact"] &= centroid(expected_mask) == tuple(map(float, site))
        for site in set(tuple(p["site"]) for p in r["probes"]):
            h = by_label_center[(site, "horizontal")]
            v = by_label_center[(site, "vertical")]
            checks["probe_masks_labels_and_centroids_exact"] &= h["active_count"] == v["active_count"] and centroid(h["mask"]) == centroid(v["mask"])
        train_probes = [p for p in r["probes"] if p["split"] == "train"]
        test_probes = [p for p in r["probes"] if p["split"] == "heldout"]
        checks["each_seed_has_eight_heldout_probes"] &= len(train_probes) == 24 and len(test_probes) == 8
        counts = Counter()
        seed_predictions = []
        for p in test_probes:
            pred, distances = predict_nearest_mean(train_probes, p["acts"])
            initial_vector = activation(r["initial_fields"], p["mask"])
            initial_pred, _ = predict_nearest_mean(
                [{**row, "acts": activation(r["initial_fields"], row["mask"])} for row in train_probes], initial_vector)
            template_pred = "horizontal" if len({i // W for i in p["mask"]}) == 1 else "vertical"
            centroid_pred = "horizontal"  # Fixed tie-break; both feature centroids equal the stimulus center.
            count_pred = "horizontal"  # Fixed tie-break; both classes contain exactly five active cells.
            outcomes = {"learned_activation": pred == p["label"], "initial_random_activation": initial_pred == p["label"],
                        "translation_aware_template": template_pred == p["label"],
                        "centroid_only": centroid_pred == p["label"], "active_count_only": count_pred == p["label"]}
            for name, correct in outcomes.items():
                counts[name] += int(correct)
                all_correct[name] += int(correct)
            seed_predictions.append({"site": p["site"], "label": p["label"], "prediction": pred,
                "initial_prediction": initial_pred, "distances": distances, "outcomes": outcomes,
                "native_winners": p["winners"]})
        per_seed.append({"seed": seed, "heldout_count": len(test_probes),
            "correct": dict(counts), "predictions": seed_predictions,
            "train_closure_ns": r["closure_ns"], "input_update_ns": r["input_update_ns"],
            "input_writes": r["input_writes"], "schedule_sha256": r["schedule_sha256"]})
        rows.extend(seed_predictions)
    checks["analyzer_source_stable"] = analyzer_sha == sha(SCRIPT)
    total = len(rows)
    summary = {name: {"correct": all_correct[name], "total": total,
                      "accuracy": all_correct[name] / total if total else None}
               for name in ("learned_activation", "initial_random_activation",
                            "translation_aware_template", "centroid_only", "active_count_only")}
    result = {"schema": "VisionEyePositionHeldoutOrientationV1Analysis",
        "run_id": "vision-eye-position-heldout-orientation-v1-analysis-20261005",
        "analyzer_sha256": analyzer_sha, "capture_sha256": sha(CAPTURE), "lock_sha256": sha(LOCK),
        "checks": checks, "passed": all(checks.values()),
        "readout": "Nearest class mean over WUnit activation vectors, fitted on 24 probes from 12 training positions; evaluated on 8 probes at four excluded corner positions. Labels are external to substrate learning.",
        "summary": summary, "per_seed": per_seed,
        "median_train_closure_ms_per_step": statistics.median(x["train_closure_ns"] / STEPS / 1e6 for x in per_seed),
        "interpretation_boundary": "This measures transfer utility in an unsupervised substrate representation using an external nearest-mean decoder. It does not establish in-substrate classification, natural-image recognition, or general self-improvement."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": checks, "summary": summary,
        "median_train_closure_ms_per_step": result["median_train_closure_ms_per_step"],
        "output": OUT.relative_to(ROOT).as_posix()}))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
