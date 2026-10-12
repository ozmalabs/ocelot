#!/usr/bin/env python3
"""Check source lock, graph/native gate registration, and expected verdicts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/self_verification_adapter_gate_v1/capture.json"
LOCK = ROOT / "evaluation/substrate_capability/self_verification_adapter_gate_v1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/self_verification_adapter_gate_v1/analysis.json"


def main() -> None:
    cap, lock = json.loads(CAPTURE.read_text()), json.loads(LOCK.read_text())
    assert cap["input_lock"] == lock == cap["post_run_input_lock"]
    cases = cap["cases"]
    assert len(cases) == 6
    rows = []
    for item in cases:
        result = item.get("result") or item["outcome"]["verified"]
        state = item["gate_state"]
        attrs, probe = state["claim_attrs"], state["probe_attrs"]
        expected = item["kind"] == "composed_pipeline"
        readback = {
            "g_discriminates": attrs.get("g_discriminates"),
            "g_no_regression": attrs.get("g_no_regression"),
            "g_grounded": attrs.get("g_grounded"), "verdict": attrs.get("verdict"),
            "probe_real_pass": probe.get("real_pass"), "probe_twin_pass": probe.get("twin_pass"),
            "claim_no_regression_input": attrs.get("no_regression"),
            "claim_grounded_input": attrs.get("grounded"),
        }
        assert state["graph_gate_rule_count"] == 1
        assert state["native_gate_rule_count"] == 1
        assert "verdict" in attrs and result["accepted"] is expected
        assert (float(attrs["verdict"]) >= 0.5) is expected
        assert (float(attrs["g_discriminates"]) >= 0.5) is expected
        if expected:
            assert all(float(attrs[key]) >= 0.5 for key in
                       ("g_no_regression", "g_grounded"))
            assert probe["real_pass"] == 1.0 and probe["twin_pass"] == 0.0
        else:
            assert probe["real_pass"] == 0.0 and probe["twin_pass"] == 0.0
            assert float(attrs["g_no_regression"]) >= 0.5
            assert float(attrs["g_grounded"]) >= 0.5
        rows.append({"kind": item["kind"], "replicate": item["replicate"],
                     "accepted": result["accepted"], "gate_readback": readback,
                     "rule_registration": {"graph": state["graph_gate_rule_count"],
                                            "native": state["native_gate_rule_count"]},
                     "elapsed_seconds": item["elapsed_seconds"]})
    out = {"schema_version": 1,
           "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
           "pre_post_lock_match": True, "case_count": len(rows),
           "positive_count": sum(r["kind"] == "composed_pipeline" for r in rows),
           "negative_count": sum(r["kind"] == "known_fake" for r in rows),
           "all_verdicts_match_graph_readback": True,
           "gate_rule_registered_once_in_each_graph_and_native_registry": True,
           "cases": rows,
           "claim_boundary": "Three repeats per arm validate this WorldAdapter integration fixture; no general verifier soundness claim follows."}
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "cases": len(rows),
                      "positive": out["positive_count"], "negative": out["negative_count"]}, indent=2))


if __name__ == "__main__":
    main()
