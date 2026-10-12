#!/usr/bin/env python3
"""Independent invariant checks for the locked live runtime rule-set census."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/live_runtime_closure_counters_v1_6_20261004.json.gz"
PARENT_ANALYSIS = ROOT / "evaluation/reports/live_runtime_closure_counters_v1_6_analysis_20261004.json"
LOCK = ROOT / "evaluation/substrate_capability/live_runtime_ruleset_census_v1_lock_20261004.json"
PROFILE = ROOT / "evaluation/reports/live_runtime_ruleset_census_v1_20261004.json"
OUT = ROOT / "evaluation/reports/live_runtime_ruleset_census_v1_analysis_20261004.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []

    def req(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    locked = json.loads(LOCK.read_text())["locked_inputs"]
    req(json.loads(PARENT_ANALYSIS.read_text()).get("passed") is True, "parent v1.6 analysis did not pass")
    with gzip.open(RAW, "rt", encoding="utf-8") as stream:
        raw = json.load(stream)
    profile = json.loads(PROFILE.read_text())
    req(profile.get("locked_inputs") == locked, "profile source lock differs from lock manifest")
    req(profile.get("post_run_inputs") == locked and profile.get("source_stable") is True, "profile inputs changed during census")
    req(raw.get("source_stable") is True and raw.get("all_checks_pass") is True, "parent capture integrity failed")
    req(profile.get("sample", {}).get("baseline_rule_count") == 2357, "baseline definition count changed")
    req(profile.get("sample", {}).get("graph_nodes") == 25065, "fixed graph node count changed")
    req(profile.get("sample", {}).get("graph_edges") == 11543, "fixed graph edge count changed")
    req(profile.get("sample", {}).get("replicate") == 0 and profile.get("sample", {}).get("audit_mode") == "on", "wrong fixed sample")

    run_matches = [r for r in raw.get("runs", []) if r.get("replicate") == 0 and r.get("audit_mode") == "on"]
    req(len(run_matches) == 1, "fixed raw run is not unique")
    if len(run_matches) == 1:
        run = run_matches[0]
        req(len(run.get("native_exported_rules", [])) == 2357, "raw baseline rule count mismatch")
        req(len(run.get("native_counter_observations", [])) == 2, "expected two request counter observations")
        req([o.get("prompt") for o in run.get("native_counter_observations", [])] == [p.get("prompt") for p in profile.get("per_prompt", [])], "prompt order or count mismatch")

    rules = profile.get("rules", [])
    req(len(rules) == 2357, "census does not retain every baseline rule")
    uids = [r.get("rule_uid") for r in rules]
    req(len(uids) == len(set(uids)), "baseline RuleUIDs are not unique")
    statuses: dict[str, int] = {}
    prompt_names = [p.get("prompt") for p in profile.get("per_prompt", [])]
    for row in rules:
        status = row.get("finite_key_status")
        statuses[status] = statuses.get(status, 0) + 1
        req(status in {"accepted", "rejected", "outside_fragment_condition"}, "rule lacks explicit checker classification")
        req(set(row.get("work_by_prompt", {})) == set(prompt_names), "rule work not reported for each prompt")
        req(set(row.get("counter_identity_observed_by_prompt", {})) == set(prompt_names), "identity visibility not reported for each prompt")
        req(all(set(row["work_by_prompt"][prompt]) == {"candidate_pairs", "candidate_tests", "term_evaluations"} for prompt in prompt_names), "rule work metrics incomplete")
    req(statuses == profile.get("finite_key_status_counts"), "classification totals do not reconcile")
    req(sum(statuses.values()) == 2357, "classification is not exhaustive")
    req(statuses.get("accepted") == 2, "accepted-rule count differs from preregistered fixed result")

    prompts = profile.get("per_prompt", [])
    req(len(prompts) == 2, "profile must contain two prompt rows")
    for row in prompts:
        categories = row.get("source_categories", {})
        sums = {key: sum(int(c.get(key, 0)) for c in categories.values()) for key in ("candidate_pairs", "candidate_tests", "term_evaluations")}
        global_counts = row.get("global", {})
        req(sums["candidate_pairs"] == int(global_counts.get("cand_enum", -1)), "candidate pairs do not conserve for " + str(row.get("prompt")))
        req(sums["candidate_tests"] == int(global_counts.get("cand_tested", -1)), "candidate tests do not conserve for " + str(row.get("prompt")))
        req(sums["term_evaluations"] + int(global_counts.get("term_evals_unattributed_host_api", 0)) == int(global_counts.get("term_evals_total", -1)), "Term evaluations do not conserve for " + str(row.get("prompt")))
        req(int(global_counts.get("term_evals_unattributed_no_rule", -1)) == 0 and int(global_counts.get("term_evals_unattributed_ambiguous", -1)) == 0, "unresolved Term work found for " + str(row.get("prompt")))
        req(0 < row.get("primary_definition_matches", 0) <= 2357, "invalid primary definition crosswalk for " + str(row.get("prompt")))
        observed = {r.get("local_rule_index") for r in rules if r.get("counter_identity_observed_by_prompt", {}).get(row.get("prompt")) is True}
        req(len(observed) == row.get("primary_definition_matches"), "per-rule identity visibility does not reconcile for " + str(row.get("prompt")))
        candidates = profile.get("primary_store_rule_crosswalk_candidates", {}).get(str(row.get("prompt")), {})
        req(candidates.get(str(row.get("primary_store_id"))) == row.get("primary_definition_matches"), "primary store candidate count mismatch for " + str(row.get("prompt")))
        req(sum(count == max(candidates.values(), default=-1) for count in candidates.values()) == 1, "primary store candidate is not uniquely maximal for " + str(row.get("prompt")))
        req(sum(r.get("term_evaluations", 0) for r in row.get("primary_post_boot_no_body_rows", [])) >= 0, "invalid post-boot body coverage")

    accepted = [row for row in rules if row.get("finite_key_status") == "accepted"]
    for row in accepted:
        req(all(all(int(value) == 0 for value in row["work_by_prompt"][p].values()) for p in prompt_names), "accepted fragment rule has nonzero measured route work")
    passed = not errors and profile.get("all_checks_pass") is True
    result = {
        "schema": "LiveRuntimeRulesetCensusV1Analysis",
        "passed": passed,
        "errors": errors,
        "profile_sha256": sha(PROFILE),
        "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK),
        "baseline_rule_count": len(rules),
        "finite_key_status_counts": statuses,
        "prompt_count": len(prompts),
        "term_partition_conserved": not any("Term evaluations do not conserve" in error for error in errors),
        "claim_boundary": "One authored full-seed two-request route; static checker classification is not runtime replay, natural prevalence, or a termination proof.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": passed, "errors": errors, "baseline_rule_count": len(rules), "classifications": statuses}, indent=2))
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())
