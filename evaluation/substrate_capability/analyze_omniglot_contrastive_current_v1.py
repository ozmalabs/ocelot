#!/usr/bin/env python3
"""Independent analysis of the source-locked current Omniglot paired capture."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[2]
CAPTURE_DIR = ROOT / "evaluation/reports/omniglot_contrastive_current_v1_capture"
CAPTURE_PATH = CAPTURE_DIR / "capture.json"
LOCK_PATH = ROOT / "evaluation/substrate_capability/omniglot_contrastive_current_v1_lock_20260928.json"
BASELINE_PATH = ROOT / "results/run26_checkpoints/eval_baseline.json"
OUT_PATH = ROOT / "evaluation/reports/omniglot_contrastive_current_v1_independent_analysis.json"


def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float]:
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [center - half, center + half]


def keyed(records: list[dict], name: str) -> dict[tuple, dict]:
    out = {}
    for row in records:
        key = (row["alph"], row["r"], row["true"])
        if key in out:
            raise ValueError(f"duplicate {name} episode key: {key!r}")
        out[key] = row
    return out


def main() -> None:
    capture = json.loads(CAPTURE_PATH.read_text())
    locked = json.loads(LOCK_PATH.read_text())
    baseline = json.loads(BASELINE_PATH.read_text())
    raw_eval = json.loads((CAPTURE_DIR / "eval_run37a.json").read_text())
    rows = capture["evaluation"]["records"]
    base = keyed(baseline["records"], "baseline")
    current = keyed(rows, "current")
    if len(rows) != 400 or len(current) != 400 or len(base) != 400:
        raise ValueError("expected exactly 400 unique rows in current and baseline panels")

    keys_match = set(base) == set(current)
    baseline_match = keys_match and all(
        current[key]["pred_full"] == base[key]["pred_full"] for key in base
    )
    global_k = sum(r["pred_full"] == r["true"] for r in rows)
    contrastive_k = sum(r["pred_contrastive"] == r["true"] for r in rows)
    fixed_rows = [r for r in rows if r["pred_full"] != r["true"] and r["pred_contrastive"] == r["true"]]
    broken_rows = [r for r in rows if r["pred_full"] == r["true"] and r["pred_contrastive"] != r["true"]]
    fixed, broken = len(fixed_rows), len(broken_rows)
    exact_p = float(binomtest(fixed, fixed + broken, p=0.5, alternative="two-sided").pvalue)
    per_alphabet = {}
    for alphabet in sorted({r["alph"] for r in rows}):
        subset = [r for r in rows if r["alph"] == alphabet]
        per_alphabet[alphabet] = {
            "n": len(subset),
            "global_correct": sum(r["pred_full"] == r["true"] for r in subset),
            "contrastive_correct": sum(r["pred_contrastive"] == r["true"] for r in subset),
            "fixed": sum(r in fixed_rows for r in subset),
            "broken": sum(r in broken_rows for r in subset),
        }
    rank_counts = {}
    for r in rows:
        if r["pred_full"] != r["true"]:
            rank = r.get("true_rank")
            rank_counts[str(rank)] = rank_counts.get(str(rank), 0) + 1
    posthoc = {}
    for field in ("cv_decision", "cv_kind", "cv_single_stroke", "cv_count_mismatch"):
        strata = {}
        for label in sorted({str(r.get(field)) for r in rows}):
            subset = [r for r in rows if str(r.get(field)) == label]
            strata[label] = {
                "n": len(subset),
                "global_correct": sum(r["pred_full"] == r["true"] for r in subset),
                "contrastive_correct": sum(r["pred_contrastive"] == r["true"] for r in subset),
                "fixed": sum(r in fixed_rows for r in subset),
                "broken": sum(r in broken_rows for r in subset),
            }
        posthoc[field] = strata
    source_lock_stable = locked == capture["locked_inputs"] == capture["post_run_inputs"]
    runner_path = ROOT / "scripts/substrate_omniglot_contrastive_current_v1.py"
    spec = importlib.util.spec_from_file_location("current_replay_runner", runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load source-lock verifier")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    live_lock = runner.input_lock()
    source_lock_stable = source_lock_stable and live_lock == locked
    raw_matches = raw_eval.get("done") is True and raw_eval.get("records") == rows
    outcome = {
        "schema_version": 1,
        "analysis_method": "independent key join, direct accuracy and discordance counts, Wilson intervals, scipy exact binomial test; benchmark stage_report not called",
        "run_id": capture.get("run_id"),
        "n": len(rows),
        "unique_current_episode_keys": len(current),
        "unique_baseline_episode_keys": len(base),
        "episode_key_sets_match": keys_match,
        "global_predictions_match_locked_baseline_exactly": baseline_match,
        "current_global": {"correct": global_k, "accuracy": global_k / len(rows), "wilson_95": wilson(global_k, len(rows))},
        "current_contrastive": {"correct": contrastive_k, "accuracy": contrastive_k / len(rows), "wilson_95": wilson(contrastive_k, len(rows))},
        "paired": {"fixed": fixed, "broken": broken, "discordant": fixed + broken, "exact_mcnemar_two_sided_p": exact_p},
        "true_rank_among_global_errors": rank_counts,
        "per_alphabet": per_alphabet,
        "posthoc_strata_exploratory_not_confirmatory": posthoc,
        "cv_decisions": {label: sum(r.get("cv_decision") == label for r in rows) for label in sorted({r.get("cv_decision") for r in rows})},
        "integrity": {
            "capture_complete": capture.get("capture_status") == "complete",
            "raw_checkpoint_matches_capture": raw_matches,
            "lock_matches_capture_pre_and_post": source_lock_stable,
            "guard_passed": bool(capture.get("guard", {}).get("guard_ok")),
            "global_matches_preregistered_322": global_k == 322,
            "preregistered_harm_or_wash_stop": broken >= fixed,
            "all_gates_pass": bool(capture.get("capture_status") == "complete" and raw_matches and source_lock_stable and capture.get("guard", {}).get("guard_ok") and keys_match and baseline_match and global_k == 322),
        },
        "claim_boundary": capture.get("claim_boundary"),
    }
    OUT_PATH.write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT_PATH.relative_to(ROOT)), "integrity": outcome["integrity"],
                      "global": outcome["current_global"], "contrastive": outcome["current_contrastive"],
                      "paired": outcome["paired"]}, indent=2))
    if not outcome["integrity"]["all_gates_pass"]:
        raise SystemExit("independent analysis integrity gate failed")


if __name__ == "__main__":
    main()
