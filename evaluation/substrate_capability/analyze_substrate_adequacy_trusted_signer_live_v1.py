#!/usr/bin/env python3
"""Independent checks for trusted-signer live-route adequacy capture."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_trusted_signer_live_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_trusted_signer_live_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_trusted_signer_live_v1_analysis_20261002.json"


def main():
    lock = json.loads(LOCK.read_text()); capture = json.loads(RAW.read_text())
    spec = importlib.util.spec_from_file_location("trusted_signer_runner",
        ROOT / "evaluation/substrate_capability/substrate_adequacy_trusted_signer_live_v1.py")
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    workers = capture["workers"]
    checks = [
        ("capture_matches_lock", capture["lock"] == lock),
        ("current_lock_matches", runner.frozen_payload() == lock),
        ("no_source_drift", capture["source_stable"] and capture["post_lock"] == lock and
         all(row["active_after"] == lock["active"] for row in workers)),
        ("six_fresh_workers", len(workers) == 6 and len({row["pid"] for row in workers}) == 6),
        ("complete_two_arm_schedule", {(r["case"], r["repetition"]) for r in workers} ==
         {(case, rep) for case in ("honest_square", "trusted_wrong_identity")
          for rep in (1, 2, 3)}),
    ]
    honest = [row for row in workers if row["case"] == "honest_square"]
    wrong = [row for row in workers if row["case"] == "trusted_wrong_identity"]
    checks.extend([
        ("honest_provider_adopts_and_generalizes", len(honest) == 3 and all(
            row["provider_auth"]["ok"] and row["receipt_status"] == "accepted" and
            row["shape_delta"] == 1 and row["heldout_correct"] == 3 for row in honest)),
        ("trusted_wrong_label_is_authentic_but_false", len(wrong) == 3 and all(
            row["provider_auth"]["ok"] and row["receipt_status"] == "accepted" and
            row["shape_delta"] == 1 and row["claimed_label"] == 2 and
            row["oracle_label_at_probe"] == 4 and row["heldout_correct"] == 0 and
            "learned the shape" in row["reply"] for row in wrong)),
    ])
    result = {"schema": "SubstrateAdequacyTrustedSignerLiveV1Analysis",
        "checks": [{"name": name, "pass": passed} for name, passed in checks],
        "passed": sum(ok for _, ok in checks), "total": len(checks),
        "honest_median_converse_ms": sorted(r["elapsed_ns"] for r in honest)[1] / 1e6,
        "wrong_signer_median_converse_ms": sorted(r["elapsed_ns"] for r in wrong)[1] / 1e6,
        "conclusion": "HMAC establishes configured-key possession; it does not establish that the signed expected value is adequate or truthful.",
        "limits": ["one authored scalar task family", "one host", "test-only key",
                   "adversarially selected false provider label", "no natural provider-error prevalence estimate"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(ok for _, ok in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
