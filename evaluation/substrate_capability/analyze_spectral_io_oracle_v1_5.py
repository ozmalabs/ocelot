#!/usr/bin/env python3
"""Verify the post-guard forward and inverse semantic-oracle outcomes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/spectral_io_oracle_v1_5/capture.json"
LOCK = ROOT / "evaluation/substrate_capability/spectral_io_oracle_v1_5_lock_20260929.json"
OUT = ROOT / "evaluation/reports/spectral_io_oracle_v1_5/analysis.json"


def main() -> None:
    cap, lock = json.loads(CAPTURE.read_text()), json.loads(LOCK.read_text())
    assert cap["input_lock"] == lock == cap["post_run_input_lock"]
    rows = cap["cases"]
    assert len(rows) == 12
    summary = []
    for row in rows:
        result = row["result"]
        label = row["case"]["label"]
        forward_pass = bool(row["independent_forward_oracle"]) and all(
            e["passed"] for e in row["independent_forward_oracle"].values())
        if label == "B":
            assert result.get("outcome") == "built_primitive"
            assert result.get("name") == "spectral_value" and result.get("accepted") is True
            assert forward_pass
            assert "spectral_value" in row["graph"]["held_primitive_names"]
            semantic_refusal = False
        else:
            assert result.get("outcome") == "primitive_request"
            assert result.get("accepted") is not True
            assert result.get("term_tree") is None
            assert "recover_signal" not in row["graph"]["held_primitive_names"]
            assert "recover_signal" in row["graph"]["primitive_request_names"]
            semantic_refusal = True
        summary.append({"arm": row["arm"], "fixture": label,
                        "replicate": row["case"]["replicate"],
                        "outcome": result.get("outcome"), "accepted": result.get("accepted"),
                        "independent_forward_oracle_pass": forward_pass,
                        "returned_term_variables": row["returned_term_vars"],
                        "held_primitive_names": row["graph"]["held_primitive_names"],
                        "primitive_request_names": row["graph"]["primitive_request_names"],
                        "semantic_refusal": semantic_refusal})
    witness = cap["inverse_nonidentifiability_witness"]
    witness_pass = (witness["x_not_equal_y"] and
                    witness["max_abs_magnitude_difference"] <= 1e-10)
    assert witness_pass
    forward_rows = [x for x in summary if x["fixture"] == "B"]
    inverse_rows = [x for x in summary if x["fixture"] == "C"]
    assert len(forward_rows) == len(inverse_rows) == 6
    analysis = {"schema_version": 1,
                "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
                "pre_post_lock_match": True, "case_count": len(summary),
                "forward_case_count": len(forward_rows),
                "forward_oracle_pass_count": sum(x["independent_forward_oracle_pass"] for x in forward_rows),
                "inverse_case_count": len(inverse_rows),
                "inverse_honest_refusal_count": sum(x["semantic_refusal"] for x in inverse_rows),
                "inverse_nonidentifiability_witness": {
                    "different_signals": witness["x_not_equal_y"],
                    "max_magnitude_difference": witness["max_abs_magnitude_difference"],
                    "passed": witness_pass},
                "claim_boundary": "The guard preserves forward DFT behavior on three deterministic inputs and refuses this declared, non-identifiable inverse request in both key arms. Other spectral aliases, semantics, and capability rates remain unmeasured.",
                "cases": summary}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "cases": len(summary),
                      "forward_passes": analysis["forward_oracle_pass_count"],
                      "inverse_refusals": analysis["inverse_honest_refusal_count"],
                      "witness_max_error": witness["max_abs_magnitude_difference"]}, indent=2))


if __name__ == "__main__":
    main()
