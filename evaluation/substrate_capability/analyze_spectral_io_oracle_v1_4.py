#!/usr/bin/env python3
"""Cross-check spectral builders against independent I/O and DFT oracles."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/spectral_io_oracle_v1_4/capture.json"
LOCK = ROOT / "evaluation/substrate_capability/spectral_io_oracle_v1_4_lock_20260929.json"
OUT = ROOT / "evaluation/reports/spectral_io_oracle_v1_4/analysis.json"
ARMS = ("faculty", "faculty_plus_operations")


def main() -> None:
    cap, lock = json.loads(CAPTURE.read_text()), json.loads(LOCK.read_text())
    assert cap["input_lock"] == lock == cap["post_run_input_lock"]
    rows = cap["cases"]
    assert len(rows) == 12
    indexed = {(x["arm"], x["case"]["label"], x["case"]["replicate"]): x for x in rows}
    summaries = []
    for arm in ARMS:
        for replicate in (1, 2, 3):
            b = indexed[(arm, "B", replicate)]
            c = indexed[(arm, "C", replicate)]
            bres, cres = b["result"], c["result"]
            b_forward = all(x["passed"] for x in b["independent_forward_oracle"].values())
            c_forward = all(x["passed"] for x in c["independent_forward_oracle"].values())
            same_term = bres.get("term_tree") == cres.get("term_tree")
            output_len = len(next(iter(c["independent_forward_oracle"].values())).get("actual", []))
            io_names = set(c["returned_term_vars"])
            false_accept = (
                cres.get("outcome") == "built_primitive" and
                cres.get("accepted") is True and cres.get("name") == "recover_signal" and
                same_term and "magnitude_spectrum" not in io_names and
                "recovered_signal" not in io_names and
                output_len != c["gap_attrs"]["n_samples"])
            summaries.append({
                "arm": arm, "replicate": replicate,
                "B": {"outcome": bres.get("outcome"), "accepted": bres.get("accepted"),
                      "primitive_name": bres.get("name"), "forward_oracle_pass": b_forward,
                      "max_error": max((v["max_abs_error"] for v in b["independent_forward_oracle"].values()), default=None)},
                "C": {"outcome": cres.get("outcome"), "accepted": cres.get("accepted"),
                      "primitive_name": cres.get("name"), "forward_oracle_pass": c_forward,
                      "same_term_tree_as_B": same_term,
                      "term_variables": c["returned_term_vars"],
                      "declared_inputs": c["gap_attrs"]["inputs"],
                      "declared_outputs": c["gap_attrs"]["outputs"],
                      "expected_output_values": c["gap_attrs"]["n_samples"],
                      "one_sided_output_values": output_len,
                      "semantic_false_accept": false_accept,
                      "max_forward_error": max((v["max_abs_error"] for v in c["independent_forward_oracle"].values()), default=None)},
            })
    witness = cap["inverse_nonidentifiability_witness"]
    witness_pass = (witness["x_not_equal_y"] and
                    witness["max_abs_magnitude_difference"] <= 1e-10)
    assert witness_pass
    assert all(x["B"]["forward_oracle_pass"] for x in summaries)
    assert all(x["C"]["forward_oracle_pass"] for x in summaries)
    assert all(x["C"]["semantic_false_accept"] for x in summaries)
    assert all(x["C"]["same_term_tree_as_B"] for x in summaries)
    analysis = {
        "schema_version": 1,
        "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
        "pre_post_lock_match": True, "case_count": len(rows),
        "forward_cases": 6, "inverse_contract_cases": 6,
        "independent_forward_oracle_passes": sum(x["B"]["forward_oracle_pass"] for x in summaries),
        "inverse_magnitude_nonidentifiability_witness": {
            "different_signals": witness["x_not_equal_y"],
            "max_magnitude_difference": witness["max_abs_magnitude_difference"],
            "passed": witness_pass},
        "semantic_false_accept_count": sum(x["C"]["semantic_false_accept"] for x in summaries),
        "same_forward_term_reused_for_inverse": all(x["C"]["same_term_tree_as_B"] for x in summaries),
        "cases": summaries,
        "claim_boundary": ("This panel establishes the named magnitude-only inverse counterexample and the forward implementation's numeric fit "
                           "on three deterministic signals. It does not estimate general semantic error rates."),
    }
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "cases": len(rows),
                      "forward_oracle_passes": analysis["independent_forward_oracle_passes"],
                      "semantic_false_accepts": analysis["semantic_false_accept_count"],
                      "inverse_witness_error": witness["max_abs_magnitude_difference"]}, indent=2))


if __name__ == "__main__":
    main()
