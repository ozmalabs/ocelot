#!/usr/bin/env python3
"""Independent integrity and route analysis for concern wording diagnostic v1."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/concern_prompt_grounding_diagnostic_v1_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/concern_prompt_grounding_diagnostic_v1_lock_20260928.json"
OUT = ROOT / "evaluation/reports/concern_prompt_grounding_diagnostic_v1_analysis_20260928.json"
RUNNER = ROOT / "scripts/substrate_concern_prompt_grounding_diagnostic_v1.py"
ARMS = {
    "baseline_two": "Compare where the two letters differ and judge the trial on that region.",
    "pair_paraphrase": "Compare where the pair of letters differs and judge the trial on that region.",
    "explicit_referents": "Compare where letter A and letter B differ and judge the trial on that region.",
}
SCHEDULE = [[arm, rep] for rep in (0, 1) for arm in ARMS]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(RAW.read_text())
    frozen = json.loads(LOCK.read_text())
    runs = raw.get("runs", [])
    checks = {
        "complete_capture_no_worker_errors": raw.get("capture_status") == "complete" and not raw.get("errors"),
        "parent_lock_stable": raw.get("locked_inputs") == frozen == raw.get("post_run_inputs"),
        "runner_hash_matches_lock": frozen.get("runner_sha256") == sha(RUNNER),
        "six_workers_and_schedule": len(runs) == 6 and raw.get("schedule") == SCHEDULE,
        "unique_fresh_processes": len({r.get("pid") for r in runs}) == 6,
        "two_workers_per_arm": all(sum(r.get("diagnostic_arm") == arm for r in runs) == 2 for arm in ARMS),
        "worker_locks_stable": all(r.get("diagnostic_inputs_stable") and r.get("diagnostic_inputs_before") == frozen == r.get("diagnostic_inputs_after") for r in runs),
        "prompt_schedule_matches": all(r.get("diagnostic_prompt") == ARMS.get(r.get("diagnostic_arm")) and [r.get("diagnostic_arm"), r.get("replicate")] in SCHEDULE for r in runs),
        "one_complete_turn_per_worker": all(r.get("error") is None and len(r.get("turns", [])) == 1 for r in runs),
    }
    outcomes = {}
    for arm in ARMS:
        arm_runs = [r for r in runs if r.get("diagnostic_arm") == arm]
        outcomes[arm] = {
            "repeats": len(arm_runs),
            "replies": [r.get("reply") for r in arm_runs],
            "clarification_route_count": sum(bool(r.get("turns")) and r["turns"][0].get("communication_route") == "ask_back" for r in arm_runs),
            "unresolved_dependency_count": sum(bool(r.get("turns")) and r["turns"][0].get("interpretation", {}).get("arbitration_basis") == "typed_unresolved_action_dependency" for r in arm_runs),
            "goal_count_values": [r["turns"][0].get("goal_count") for r in arm_runs if r.get("turns")],
            "concern_action_count": sum(any(a.get("route") == "concern_authored" and a.get("concern") is not None for a in r.get("action_results", [])) for r in arm_runs),
            "teacher_call_values": [r.get("teacher_calls") for r in arm_runs],
            "median_task_wall_ms": sorted(r.get("task_wall_ns", 0) for r in arm_runs)[len(arm_runs)//2] / 1e6 if arm_runs else None,
        }
    checks["every_arm_has_two_complete_workers"] = all(v["repeats"] == 2 for v in outcomes.values())
    checks["no_arm_reaches_concern_action"] = all(v["concern_action_count"] == 0 for v in outcomes.values())
    result = {
        "schema_version": 1,
        "analysis_id": "substrate-concern-prompt-grounding-diagnostic-v1-independent-analysis",
        "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK),
        "analyzer_sha256": sha(Path(__file__)),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "outcomes_by_arm": outcomes,
        "interpretation": "All arms preserve the pre-action unresolved-dependency clarification route on this task snapshot. The clarified token changes with wording. The concern action is not reached, so concern-faculty capability remains untested.",
        "claim_boundary": "Six fresh workers over three authored prompt variants; descriptive wording diagnostic only, with no population, general language, or concern-faculty capability claim.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "checks": checks, "all_checks_pass": result["all_checks_pass"]}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("independent integrity/analysis gate failed")


if __name__ == "__main__":
    main()
