#!/usr/bin/env python3
"""Independent transfer checks for selected-probe adoption across parity/clamp."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_selected_probe_transfer_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_selected_probe_transfer_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_selected_probe_transfer_v1_analysis_20261002.json"
CASES = ("parity_correct_broad", "parity_alias_wrong", "parity_distinguish_wrong",
         "clamp_correct_broad", "clamp_alias_wrong", "clamp_distinguish_wrong")


def main():
    lock = json.loads(LOCK.read_text()); capture = json.loads(RAW.read_text())
    spec = importlib.util.spec_from_file_location("selected_probe_transfer_runner",
        ROOT / "evaluation/substrate_capability/substrate_adequacy_selected_probe_transfer_v1.py")
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    from domains import independent_adequacy as ia
    from domains.adequacy_probe_selection import select_disagreement_probe
    from domains.adequacy_provider_auth import verify_signed_audit_evidence
    from independent_codewrite_oracles import label as oracle_label
    import substrate_rs
    native = substrate_rs._native.Substrate()
    workers = capture["workers"]
    checks = [
        ("capture_matches_lock", capture["lock"] == lock),
        ("current_lock_matches", runner.frozen_payload() == lock),
        ("source_stable", capture["source_stable"] and capture["post_lock"] == lock and
         all(row["active_after"] == lock["active"] for row in workers)),
        ("18_fresh_workers", len(workers) == 18 and len({row["pid"] for row in workers}) == 18),
        ("complete_schedule", {(row["case"], row["repetition"]) for row in workers} ==
         {(case, rep) for case in CASES for rep in (1, 2, 3)}),
    ]
    selection_ok, auth_ok, receipt_ok, oracle_ok = [], [], [], []
    for row in workers:
        context = row["selection_context"]
        chosen = select_disagreement_probe(row["request"]["candidate_id"], row["candidate_term"],
            context["challenger_terms"], context["acquisition_rows"], context["admissible_inputs"],
            lambda term, env: native.evaluate(term, env), seed=context["seed"])
        selection_ok.append(chosen == context["selection"]
            and chosen["input"] == row["request"]["probes"][0]["inputs"]
            and row["request"]["seed"] == chosen["selection_id"]
            and chosen["selection_id"] != "")
        auth_ok.append(verify_signed_audit_evidence(row["request"], row["audit_rows"],
            row["receipt"], {runner.PROVIDER: runner.KEY})["ok"])
        receipt = ia.adjudicate_audit_receipt(row["request"], row["request"]["candidate_id"],
            row["candidate_term"], row["audit_rows"], lambda term, env: native.evaluate(term, env),
            acquisition_source_ids=context["acquisition_source_ids"])
        receipt_ok.append(receipt == row["receipt"])
        oracle_ok.append(all(item["expected"] == oracle_label(row["task"], item["inputs"])
            and item["prediction"] == native.evaluate(row["candidate_term"], item["inputs"])
            and item["match"] == (item["prediction"] == item["expected"])
            for item in row["heldout"]))
    checks.extend([
        ("selection_records_recompute", all(selection_ok)),
        ("provider_signatures_reverify", all(auth_ok)),
        ("receipts_recompute", all(receipt_ok)),
        ("heldout_oracle_rows_recompute", all(oracle_ok)),
    ])
    for case in CASES:
        rows = [row for row in workers if row["case"] == case]
        if case.endswith("correct_broad"):
            outcome = all(row["receipt"]["status"] == "accepted" and row["shape_delta"] == 1
                and row["heldout_correct"] == row["heldout_count"]
                and row["selection_entropy_bits"] > 0
                and "learned the shape" in row["reply"] for row in rows)
        elif case.endswith("alias_wrong"):
            outcome = all(row["receipt"]["status"] == "accepted" and row["shape_delta"] == 0
                and row["heldout_correct"] < row["heldout_count"]
                and row["selection_entropy_bits"] == 0
                and "no valid discriminating adequacy probe" in row["reply"] for row in rows)
        else:
            outcome = all(row["receipt"]["status"] == "rejected" and row["shape_delta"] == 0
                and row["heldout_correct"] < row["heldout_count"]
                and row["selection_entropy_bits"] > 0
                and "learned the shape" not in row["reply"] for row in rows)
        checks.append((f"{case}_transfer_outcome", len(rows) == 3 and outcome))
    result = {"schema": "SubstrateAdequacySelectedProbeTransferV1Analysis",
        "checks": [{"name": name, "pass": ok} for name, ok in checks],
        "passed": sum(ok for _, ok in checks), "total": len(checks),
        "summary": {case: {"n": 3,
            "receipt_status": next(row["receipt"]["status"] for row in workers if row["case"] == case),
            "selection_entropy_bits": next(row["selection_entropy_bits"] for row in workers if row["case"] == case),
            "adopted_per_run": next(row["shape_delta"] for row in workers if row["case"] == case),
            "heldout_correct_per_run": next(row["heldout_correct"] for row in workers if row["case"] == case),
            "heldout_count": next(row["heldout_count"] for row in workers if row["case"] == case)}
            for case in CASES},
        "limits": ["two authored task families", "one host", "caller-supplied challenger/domain",
            "independent oracle is a bundled fixed implementation", "no natural prevalence estimate"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(ok for _, ok in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
