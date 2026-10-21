#!/usr/bin/env python3
"""Analyze P5 reports while preserving nulls and per-item claim boundaries."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from evaluation.substrate_capability.cognition_p5_heldout_v1 import (
    FROZEN_ARTIFACTS, ITEMS, artifact_hashes, verify_hash_manifest,
)


def analyze(report):
    if not isinstance(report, dict) or report.get("protocol") != "cognition_p5_heldout_v1":
        raise ValueError("report protocol mismatch")
    verify_hash_manifest(report.get("artifact_sha256"), expected_paths=FROZEN_ARTIFACTS)
    if set(report.get("items", {})) != set(ITEMS):
        raise ValueError("report omits one or more registered items")
    results = {}
    for item, spec in ITEMS.items():
        payload = report["items"][item]
        rows = payload.get("primary", [])
        controls = payload.get("controls", [])
        nulls = sum(value is None for row in rows for value in row.get("arms", {}).values())
        unsafe = sum(bool(value.get("unsafe_emission")) for row in rows
                     for value in row.get("arms", {}).values() if isinstance(value, dict))
        invalid = []
        for row in rows:
            if set(row.get("arms", {})) != set(spec["arms"]):
                invalid.append("arm set mismatch")
            if row.get("scoring_oracle", {}).get("scoring_only") is not True:
                invalid.append("oracle missing scoring-only boundary")
        coverage = len(rows) == report["end"] - report["first"] and len(controls) == 100
        decision = "NOT_ESTABLISHED"
        if invalid or unsafe:
            decision = "FAIL"
        elif coverage and nulls == 0 and payload.get("adapter_status") == "complete":
            decision = "REQUIRES_ITEM_ANALYSIS"
        results[item] = {"decision": decision,
                         "coverage": {"primary": len(rows), "required_primary": report["end"] - report["first"],
                                      "controls": len(controls), "required_controls": 100,
                                      "complete": coverage},
                         "null_arm_results": nulls, "unsafe_emissions": unsafe,
                         "invalid_results": invalid,
                         "adapter_status": payload.get("adapter_status"),
                         "claim_boundary": "mechanism evidence only; no human cognition claim"}
    return {"protocol": "cognition_p5_analysis_v1", "prereg_hash": report.get("prereg_hash"),
            "items": results,
            "overall_decision": ("FAIL" if any(row["decision"] == "FAIL" for row in results.values())
                                 else "NOT_ESTABLISHED"),
            "nulls_preserved": True,
            "note": "Null arms remain visible and cannot be scored as successes or silently dropped."}


def _self_check():
    from evaluation.substrate_capability.cognition_p5_heldout_v1 import run
    report = run("development", 0, 2, development=True)
    result = analyze(report)
    assert result["overall_decision"] == "NOT_ESTABLISHED"
    assert all(item["null_arm_results"] > 0 for item in result["items"].values())
    hashes = artifact_hashes()
    try:
        verify_hash_manifest({}, expected_paths=tuple(hashes))
    except ValueError:
        pass
    else:
        raise AssertionError("analysis accepted absent hashes")
    altered = dict(hashes)
    altered[next(iter(altered))] = "0" * 64
    try:
        verify_hash_manifest(altered, expected_paths=tuple(hashes))
    except ValueError:
        pass
    else:
        raise AssertionError("analysis accepted altered hashes")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--self-check"]:
        _self_check()
        print("cognition_p5_analysis_v1 self-check passed (development-only)")
        return
    if len(argv) != 1:
        raise SystemExit("usage: cognition_p5_analysis_v1.py <heldout_report.json> | --self-check")
    report = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    result = analyze(report)
    out = Path(argv[0]).with_name(Path(argv[0]).stem + "_analysis.json")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
