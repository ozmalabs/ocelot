#!/usr/bin/env python3
"""Read-only independent arithmetic check of the archived Omniglot run-37A records."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_OMNIGLOT_CONTRASTIVE_VERDICT_REANALYSIS_V1_PROTOCOL_20260928.md"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/omniglot_contrastive_historical_reanalysis_v1_lock_20260928.json"
OUT = ROOT / "evaluation/reports/omniglot_contrastive_historical_reanalysis_v1_20260928.json"
INPUTS = {
    "raw": ROOT / "results/run37a_checkpoints/eval_run37a.json",
    "summary": ROOT / "results/run37a_checkpoints/report.json",
    "baseline": ROOT / "results/run26_checkpoints/eval_baseline.json",
    "log": ROOT / "results/omniglot_gate_run37a.log",
    "guard": ROOT / "results/run37a_checkpoints/guard.json",
    "arc_record": ROOT / "docs/research/vision/OMNIGLOT_ARC.md",
}
CURRENT_CODE = [
    "scripts/jabberwock_omniglot_run37a_contrastive.py",
    "domains/contrastive_verdict.py",
    "domains/abs_read.py",
    "domains/omniglot_world.py",
    "scripts/jabberwock_omniglot_run25_number.py",
    "scripts/jabberwock_omniglot_run26_homework.py",
    "scripts/jabberwock_omniglot_dynamic_quantization.py",
    "scripts/jabberwock_omniglot_run37c_hygiene.py",
]


def file_record(path: Path) -> dict:
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def input_lock() -> dict:
    return {
        "protocol": file_record(PROTOCOL),
        "runner": file_record(RUNNER),
        "inputs": {k: {"path": str(p.relative_to(ROOT)), **file_record(p)} for k, p in INPUTS.items()},
        "current_code_observed_not_historical_source_proof": {
            p: file_record(ROOT / p) for p in CURRENT_CODE
        },
        "historical_source_claim": "docs/research/vision/OMNIGLOT_ARC.md attributes run 37A to cca938fd; that commit object is not available in this imported checkout.",
    }


def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float]:
    p = k / n
    d = 1 + z*z/n
    center = (p + z*z/(2*n)) / d
    radius = z * math.sqrt((p*(1-p) + z*z/(4*n))/n) / d
    return [center-radius, center+radius]


def mcnemar_exact(fixed: int, broken: int) -> float:
    n = fixed + broken
    if not n:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(fixed, broken)+1)) / (2**n)
    return min(1.0, 2*tail)


def key(record: dict) -> tuple:
    return record.get("alph"), record.get("r"), record.get("true")


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite lock or analysis")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(input_lock(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    if OUT.exists():
        raise SystemExit("refusing to overwrite analysis output")
    lock = json.loads(LOCK.read_text())
    before = input_lock()
    if before != lock:
        raise SystemExit("historical inputs, current-code observation, or protocol changed since lock")

    raw = json.loads(INPUTS["raw"].read_text())
    summary = json.loads(INPUTS["summary"].read_text())
    baseline = json.loads(INPUTS["baseline"].read_text())
    guard = json.loads(INPUTS["guard"].read_text())
    records, baseline_records = raw.get("records", []), baseline.get("records", [])
    checks = {
        "raw_complete_400_records": raw.get("done") is True and raw.get("block_idx") == 20 and len(records) == 400,
        "baseline_complete_400_records": baseline.get("done") is True and len(baseline_records) == 400,
        "guard_passed": guard.get("guard_ok") is True and guard.get("top2_consistency") == guard.get("top2_total") == 20,
        "twenty_way_labels_and_predictions": all(isinstance(x.get(k), int) and 0 <= x[k] < 20 for x in records for k in ("true", "pred_full", "pred_contrastive")),
        "episode_keys_unique": len({key(x) for x in records}) == 400 and len({key(x) for x in baseline_records}) == 400,
        "paired_baseline_keys_match": {key(x) for x in records} == {key(x) for x in baseline_records},
        "global_arm_matches_archived_baseline": all({key(b): b.get("pred_full") for b in baseline_records}.get(key(r)) == r.get("pred_full") for r in records),
        "ten_alphabets_forty_each": len(Counter(x.get("alph") for x in records)) == 10 and set(Counter(x.get("alph") for x in records).values()) == {40},
        "current_inputs_stable_after_analysis": input_lock() == lock,
    }
    global_k = sum(x["pred_full"] == x["true"] for x in records)
    contrast_k = sum(x["pred_contrastive"] == x["true"] for x in records)
    fixed = sum(x["pred_full"] != x["true"] and x["pred_contrastive"] == x["true"] for x in records)
    broken = sum(x["pred_full"] == x["true"] and x["pred_contrastive"] != x["true"] for x in records)
    rank_hist = Counter(str(x.get("true_rank")) for x in records if x["pred_full"] != x["true"])
    cv_counts = Counter(x.get("cv_decision", "missing") for x in records)
    per_alphabet = {}
    for alphabet in sorted({x["alph"] for x in records}):
        group = [x for x in records if x["alph"] == alphabet]
        per_alphabet[alphabet] = {
            "n": len(group),
            "global_correct": sum(x["pred_full"] == x["true"] for x in group),
            "contrastive_correct": sum(x["pred_contrastive"] == x["true"] for x in group),
            "fixed": sum(x["pred_full"] != x["true"] and x["pred_contrastive"] == x["true"] for x in group),
            "broken": sum(x["pred_full"] == x["true"] and x["pred_contrastive"] != x["true"] for x in group),
        }
    pvalue = mcnemar_exact(fixed, broken)
    checks.update({
        "global_metrics_match_archived_summary": global_k == summary.get("global_k") == 322 and abs(global_k/400-summary.get("global_acc", 0)) < 1e-12 and all(abs(a-b) < 1e-10 for a,b in zip(wilson(global_k,400), summary.get("global_ci", []))),
        "contrastive_metrics_match_archived_summary": contrast_k == summary.get("contrastive_k") == 256 and abs(contrast_k/400-summary.get("contrastive_acc", 0)) < 1e-12 and all(abs(a-b) < 1e-10 for a,b in zip(wilson(contrast_k,400), summary.get("contrastive_ci", []))),
        "paired_discordance_and_exact_p_match": fixed == summary.get("n_fixed") == 16 and broken == summary.get("n_broken") == 82 and abs(pvalue-summary.get("mcnemar_p", 1)) < 1e-15,
        "diagnostic_histograms_match": dict(rank_hist) == summary.get("rank_hist") and dict(cv_counts) == summary.get("cv_decisions") and all(
            {k: per_alphabet[a][k] for k in ("n", "fixed", "broken")} == summary.get("per_alphabet", {}).get(a)
            for a in per_alphabet),
        "fixed_case_instruments_match": sum(x["pred_full"] != x["true"] and x["pred_contrastive"] == x["true"] and x.get("cv_single_stroke") for x in records) == summary.get("single_stroke_fixed") and sum(x["pred_full"] != x["true"] and x["pred_contrastive"] == x["true"] and x.get("cv_decision") == "one_sided" for x in records) == summary.get("one_sided_fixed"),
        "rank_two_ceiling_reproduced": sum(v for k,v in rank_hist.items() if k == "2") == summary.get("n_rank2_ceiling") == 33 and fixed <= 33,
    })
    result = {
        "schema_version": 1,
        "analysis_id": "omniglot-contrastive-historical-reanalysis-v1",
        "lock_sha256": hashlib.sha256(LOCK.read_bytes()).hexdigest(),
        "inputs": lock["inputs"],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "n": len(records),
        "global": {"correct": global_k, "accuracy": global_k/400, "wilson_95": wilson(global_k,400)},
        "contrastive": {"correct": contrast_k, "accuracy": contrast_k/400, "wilson_95": wilson(contrast_k,400)},
        "paired": {"fixed": fixed, "broken": broken, "discordant": fixed+broken, "exact_mcnemar_two_sided_p": pvalue},
        "true_rank_histogram_on_global_errors": dict(sorted(rank_hist.items(), key=lambda kv: int(kv[0]))),
        "contrastive_decision_counts": dict(cv_counts),
        "per_alphabet": per_alphabet,
        "source_provenance_limit": "Historical summary attributes run 37A to cca938fd, but the object is unavailable here and the archived raw capture lacks a full source/input lock. This is artifact/statistics reanalysis, not current-source reproduction.",
        "claim_boundary": "The archived run's top-two focused contrastive verdict was substantially harmful on this 400-episode Omniglot panel. This is not evidence about the separate generated experiment-judge rule.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "checks": checks, "all_checks_pass": result["all_checks_pass"]}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("historical reanalysis consistency gate failed")


if __name__ == "__main__":
    main()
