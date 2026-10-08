#!/usr/bin/env python3
"""Independent checks for generated experiment-jugde semantic replay v1."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/generated_experiment_judge_semantics_v1_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/generated_experiment_judge_semantics_v1_lock_20260928.json"
RUNNER = ROOT / "scripts/substrate_generated_experiment_judge_semantics_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_EXPERIMENT_JUDGE_SEMANTICS_V1_PREREG_20260928.md"
OUT = ROOT / "evaluation/reports/generated_experiment_judge_semantics_v1_analysis_20260928.json"
EXPECTED_CASES = [
    ("positive", "done", 3.0, 3.0),
    ("negative", "done", -2.0, 2.0),
    ("zero", "done", 0.0, 3.0),
    ("nonterminal_control", "running", 3.0, 3.0),
]
SIGNATURE = [["pairwise", "PARTS"], ["judge", "TRIAL", "by", "RESULT"]]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle(run_status: str, score: float, frames: float):
    if run_status != "done":
        return None
    rate = score / frames if frames else 0.0
    return "supported" if rate > 0 else "refuted" if rate < 0 else "inconclusive"


def main() -> None:
    raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    runs = raw.get("runs", [])
    checks = {
        "complete_capture_no_errors": raw.get("capture_status") == "complete" and not raw.get("errors"),
        "parent_lock_stable": raw.get("locked_inputs") == lock == raw.get("post_run_inputs"),
        "runner_hash_matches_lock": lock.get("runner_sha256") == sha(RUNNER),
        "protocol_hash_matches_lock": lock.get("protocol_sha256") == sha(PROTOCOL),
        "two_fresh_workers": len(runs) == 2 and len({r.get("pid") for r in runs}) == 2,
        "worker_source_locks_stable": all(r.get("inputs_stable") and r.get("inputs_before") == lock == r.get("inputs_after") for r in runs),
        "worker_boots_and_no_errors": all(r.get("boot_loaded", 0) > 0 and r.get("action_error") is None and r.get("teacher_calls") == 0 for r in runs),
        "concern_minted_and_grounded": all(r.get("action", {}).get("route") == "concern_authored" and r.get("action", {}).get("concern", {}).get("minted") is True and r.get("action", {}).get("concern", {}).get("grounded") is True for r in runs),
        "exact_concern_signature": all(r.get("action", {}).get("concern", {}).get("signature") == SIGNATURE for r in runs),
        "generated_judge_rule_matches_concern_key": all(
            len(r.get("generated_judge_rule_names", [])) == 1
            and r["generated_judge_rule_names"][0] == "judge_experiment_outcome_" + r.get("action", {}).get("concern", {}).get("key", "")
            for r in runs),
        "case_inventory_exact": all([(c.get("case"), c.get("run_status"), c.get("score"), c.get("frames")) for c in r.get("cases", [])] == EXPECTED_CASES for r in runs),
        "independent_score_sign_oracle": all(c.get("observed_outcome") == oracle(c.get("run_status"), c.get("score"), c.get("frames")) for r in runs for c in r.get("cases", [])),
        "completed_runs_marked_analysed": all(c.get("analysed_run_ids") == [c.get("run_id")] and c.get("conclusion_ready") is True and c.get("progress_steps", 0) > 0 for r in runs for c in r.get("cases", []) if c.get("run_status") == "done"),
        "nonterminal_run_untouched": all(not c.get("analysed_run_ids") and c.get("observed_outcome") is None and c.get("conclusion_ready") is None and c.get("progress_steps") == 0 for r in runs for c in r.get("cases", []) if c.get("run_status") != "done"),
        "all_closure_calls_succeeded": all(c.get("run_rules_error") is None for r in runs for c in r.get("cases", [])),
        "exact_repeat_outcomes": len(runs) == 2 and [[c.get("observed_outcome") for c in r.get("cases", [])] for r in runs] == [["supported", "refuted", "inconclusive", None]] * 2,
    }
    cases = {}
    if runs:
        for c in runs[0].get("cases", []):
            matching = [rr["cases"][runs[0]["cases"].index(c)] for rr in runs if len(rr.get("cases", [])) == len(runs[0]["cases"])]
            cases[c["case"]] = {
                "expected": oracle(c["run_status"], c["score"], c["frames"]),
                "observed_by_worker": [m.get("observed_outcome") for m in matching],
                "progress_steps": [m.get("progress_steps") for m in matching],
                "wall_ms": [m.get("settle_wall_ns", 0) / 1e6 for m in matching],
            }
    result = {
        "schema_version": 1,
        "analysis_id": "generated-experiment-judge-semantics-v1-independent-analysis",
        "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK),
        "analyzer_sha256": sha(Path(__file__)),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "case_summary": cases,
        "claim_boundary": "The generated judge rule matches a four-case independent sign/status oracle in two workers. Scores and trial graphs are synthetic; concern correctness on real tasks and child-run provenance are untested.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "checks": checks, "all_checks_pass": result["all_checks_pass"]}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("independent semantic or integrity gate failed")


if __name__ == "__main__":
    main()
