#!/usr/bin/env python3
"""Independent recomputation and outcome analysis for selected-probe v1."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_selected_probe_adoption_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_selected_probe_adoption_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_selected_probe_adoption_v1_analysis_20261002.json"
CASES = ("honest_selected_square", "alias_zero_entropy",
         "distinguishing_identity_truth", "selected_wrong_signer")


def main():
    lock = json.loads(LOCK.read_text()); capture = json.loads(RAW.read_text())
    spec = importlib.util.spec_from_file_location("selected_probe_runner",
        ROOT / "evaluation/substrate_capability/substrate_adequacy_selected_probe_adoption_v1.py")
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    from domains import independent_adequacy as ia
    from domains.adequacy_probe_selection import select_disagreement_probe
    from domains.adequacy_provider_auth import verify_signed_audit_evidence
    import substrate_rs
    native = substrate_rs._native.Substrate()
    workers = capture["workers"]
    checks = [
        ("capture_matches_lock", capture["lock"] == lock),
        ("current_lock_matches", runner.frozen_payload() == lock),
        ("source_stable", capture["source_stable"] and capture["post_lock"] == lock and
         all(row["active_after"] == lock["active"] for row in workers)),
        ("12_fresh_workers", len(workers) == 12 and len({row["pid"] for row in workers}) == 12),
        ("complete_schedule", {(row["case"], row["repetition"]) for row in workers} ==
         {(case, rep) for case in CASES for rep in (1, 2, 3)}),
    ]
    selection_replays = []
    auth_replays = []
    receipt_replays = []
    for row in workers:
        context = row["selection_context"]
        selected = select_disagreement_probe(row["request"]["candidate_id"],
            row["candidate_term"], context["challenger_terms"], context["acquisition_rows"],
            context["admissible_inputs"], lambda term, env: native.evaluate(term, env),
            seed=context["seed"])
        selection_replays.append(selected == context["selection"] and
            selected["input"] == row["request"]["probes"][0]["inputs"] and
            row["request"]["seed"] == selected["selection_id"] and
            row["selection_entropy_bits"] == selected["prediction_entropy_bits"])
        auth_replays.append(verify_signed_audit_evidence(row["request"],
            row["audit_rows"], row["receipt"], {runner.PROVIDER: runner.KEY})["ok"])
        receipt = ia.adjudicate_audit_receipt(row["request"],
            row["request"]["candidate_id"], row["candidate_term"], row["audit_rows"],
            lambda term, env: native.evaluate(term, env),
            acquisition_source_ids=context["acquisition_source_ids"])
        receipt_replays.append(receipt == row["receipt"])
    checks.extend([
        ("selection_records_recompute_and_bind", all(selection_replays)),
        ("provider_signatures_reverify", all(auth_replays)),
        ("core_receipts_recompute", all(receipt_replays)),
    ])
    expected = {
        "honest_selected_square": ("accepted", 1, 3, True),
        "alias_zero_entropy": ("accepted", 0, 0, False),
        "distinguishing_identity_truth": ("rejected", 0, 0, False),
        "selected_wrong_signer": ("accepted", 1, 0, True),
    }
    for case, (status, adoption, heldout, learned_reply) in expected.items():
        rows = [row for row in workers if row["case"] == case]
        if case == "alias_zero_entropy":
            entropy_ok = all(row["selection_entropy_bits"] == 0 for row in rows)
            refusal_ok = all("no valid discriminating adequacy probe" in row["reply"] for row in rows)
        else:
            entropy_ok = all(row["selection_entropy_bits"] > 0 for row in rows)
            refusal_ok = all(("learned the shape" in row["reply"]) == learned_reply for row in rows)
        checks.append((f"{case}_outcome", len(rows) == 3 and all(
            row["receipt"]["status"] == status and row["shape_delta"] == adoption and
            row["heldout_correct"] == heldout for row in rows) and entropy_ok and refusal_ok))
    result = {"schema": "SubstrateAdequacySelectedProbeAdoptionV1Analysis",
        "checks": [{"name": name, "pass": ok} for name, ok in checks],
        "passed": sum(ok for _, ok in checks), "total": len(checks),
        "summary": {case: {"n": 3, "receipt_status": expected[case][0],
            "adoption_per_run": expected[case][1], "heldout_correct_per_run": expected[case][2],
            "selection_entropy_bits": next(row["selection_entropy_bits"] for row in workers
                                             if row["case"] == case)} for case in CASES},
        "limits": ["caller supplies challenger set and admissible domain",
            "positive entropy proves separation only from the supplied challengers",
            "trusted wrong labels still pass when consistent with candidate at selected input",
            "one authored scalar family and one host"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(ok for _, ok in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
