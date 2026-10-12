#!/usr/bin/env python3
"""Independent outcome checks for provider agreement/domain capture."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_provider_agreement_domain_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_provider_agreement_domain_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_provider_agreement_domain_v1_analysis_20261002.json"
CASES = ("honest_single", "conflicting_two", "correlated_wrong_two",
         "aliased_honest_two", "distinguishing_honest_two")


def main():
    lock = json.loads(LOCK.read_text()); capture = json.loads(RAW.read_text())
    spec = importlib.util.spec_from_file_location("provider_agreement_runner",
        ROOT / "evaluation/substrate_capability/substrate_adequacy_provider_agreement_domain_v1.py")
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    workers = capture["workers"]
    checks = [
        ("capture_matches_lock", capture["lock"] == lock),
        ("current_lock_matches", runner.frozen_payload() == lock),
        ("source_stable", capture["source_stable"] and capture["post_lock"] == lock and
         all(row["active_after"] == lock["active"] for row in workers)),
        ("15_fresh_workers", len(workers) == 15 and len({row["pid"] for row in workers}) == 15),
        ("complete_schedule", {(row["case"], row["repetition"]) for row in workers} ==
         {(case, rep) for case in CASES for rep in (1, 2, 3)}),
    ]
    expected = {
        "honest_single": ("accepted", 1, 3),
        "conflicting_two": ("ambiguous", 0, 0),
        "correlated_wrong_two": ("accepted", 1, 0),
        "aliased_honest_two": ("accepted", 1, 0),
        "distinguishing_honest_two": ("rejected", 0, 0),
    }
    for case, (status, adoption, holdout) in expected.items():
        rows = [row for row in workers if row["case"] == case]
        checks.append((f"{case}_outcome", len(rows) == 3 and all(
            row["provider_auth"]["ok"] and row["receipt_status"] == status and
            row["shape_delta"] == adoption and row["heldout_correct"] == holdout
            for row in rows)))
    result = {"schema": "SubstrateAdequacyProviderAgreementDomainV1Analysis",
        "checks": [{"name": name, "pass": ok} for name, ok in checks],
        "passed": sum(ok for _, ok in checks), "total": len(checks),
        "summary": {case: {"n": sum(row["case"] == case for row in workers),
            "receipt_status": expected[case][0], "adopted_per_run": expected[case][1],
            "heldout_correct_per_run": expected[case][2]} for case in CASES},
        "limits": ["two provider IDs do not prove independent operators",
                   "aliasing domain is intentionally inadequate", "one scalar task family",
                   "does not estimate natural provider-correlation prevalence"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(ok for _, ok in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
