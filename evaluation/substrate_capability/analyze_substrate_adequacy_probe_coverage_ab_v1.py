#!/usr/bin/env python3
"""Independent domain-coverage and matched-evidence adoption analysis."""
from __future__ import annotations
import hashlib, json, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(Path(__file__).resolve().parent)]
RAW = ROOT / "evaluation/reports/substrate_adequacy_probe_coverage_ab_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_probe_coverage_ab_v1_analysis_20261002.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze() -> dict:
    import substrate_adequacy_probe_coverage_ab_v1 as runner
    from independent_codewrite_oracles import label as oracle
    capture = json.loads(RAW.read_text())
    lock_ok = capture["lock"] == capture["post_lock"] == runner.lock_payload()
    oracle_sha = sha(runner.ORACLE)
    by_key = {(w["repetition"], w["arm"]): w for w in capture["workers"]}
    checks = [{"case": "source-lock-current", "pass": lock_ok},
              {"case": "oracle-hash-current", "pass": oracle_sha == capture["lock"]["active"]["oracle"]}]
    false_accepts = 0
    for rep in range(1, runner.REPETITIONS+1):
        narrow_g = by_key[(rep, "narrow_gated")]
        narrow_u = by_key[(rep, "narrow_ungated")]
        broad_g = by_key[(rep, "broad_gated")]
        broad_u = by_key[(rep, "broad_ungated")]
        for domain, gated, ungated, expected_status in (
                ("narrow", narrow_g, narrow_u, "accepted"),
                ("broad", broad_g, broad_u, "rejected")):
            same_evidence = (gated["candidate_id"] == ungated["candidate_id"]
                             and gated["receipt"]["request_id"] == ungated["receipt"]["request_id"]
                             and gated["receipt"]["receipt_sha256"] == ungated["receipt"]["receipt_sha256"]
                             and gated["audit_rows"] == ungated["audit_rows"])
            checks.append({"rep": rep, "case": f"{domain}-gated-ungated-identical-evidence", "pass": same_evidence})
            evidence_ok = (gated["receipt"]["status"] == expected_status
                           and ungated["receipt"]["status"] == expected_status
                           and all(label.get("oracle_sha256") == oracle_sha
                                   and label.get("source_id") == f"independent-codewrite-oracle-v1:{oracle_sha}"
                                   and label.get("expected") == oracle("square", row["inputs"])
                                   for row in gated["audit_rows"] for label in row["labels"]))
            checks.append({"rep": rep, "case": f"{domain}-receipt-and-oracle-labels", "pass": evidence_ok})
        for arm_name, row in (("narrow_gated", narrow_g), ("broad_gated", broad_g)):
            domain = arm_name.split("_")[0]
            expected_status = "accepted" if domain == "narrow" else "rejected"
            if domain == "narrow":
                adopted_ok = row["teach_ok"] is True and row["epoch_increment"] == 1 and len(row["state_after"]["node_ids"]) == 1
                outputs_ok = row["written_ok"] is True and all(not item["native_match"] and not item["python_match"] for item in row["transfer_rows"])
                false_accepts += int(adopted_ok and not any(item["native_match"] for item in row["transfer_rows"]))
            else:
                adopted_ok = row["teach_ok"] is False and row["epoch_increment"] == 0 and row["state_before"] == row["state_after"]
                outputs_ok = row["written_ok"] is False and all(item["native_output"] is None and item["python_output"] is None for item in row["transfer_rows"])
            gate_ok = (row["receipt"]["status"] == expected_status and row["strict"] is True
                       and row["baseline_ok"] is False and row["candidate_id_matches"]
                       and row["contract_passed"] is True and adopted_ok and outputs_ok)
            checks.append({"rep": rep, "case": f"{arm_name}-gate-outcome", "pass": gate_ok})
        for arm_name, row in (("narrow_ungated", narrow_u), ("broad_ungated", broad_u)):
            ungated_ok = (row["strict"] is False and row["teach_ok"] is True
                          and row["contract_passed"] is True and row["candidate_id_matches"]
                          and row["epoch_increment"] == 1 and len(row["state_after"]["node_ids"]) == 1
                          and row["written_ok"] is True
                          and all(not item["native_match"] and not item["python_match"]
                                  for item in row["transfer_rows"]))
            checks.append({"rep": rep, "case": f"{arm_name}-ungated-outcome", "pass": ungated_ok})
        checks.append({"rep": rep, "case": "all-worker-source-hashes-stable",
                       "pass": all(row["active_after"] == capture["lock"]["active"]
                                   for row in (narrow_g, narrow_u, broad_g, broad_u))})
    teach_ms = [w["teach_ns"]/1e6 for w in capture["workers"]]
    boot_ms = [w["boot_ns"]/1e6 for w in capture["workers"]]
    gated_ms = [w["teach_ns"]/1e6 for w in capture["workers"] if w["strict"]]
    ungated_ms = [w["teach_ns"]/1e6 for w in capture["workers"] if not w["strict"]]
    result = {"schema": "SubstrateAdequacyProbeCoverageABV1Analysis",
              "passed": all(c["pass"] for c in checks), "checks": checks,
              "repetitions": runner.REPETITIONS, "arms": len(capture["workers"]),
              "narrow_gated_false_accepts": false_accepts,
              "broad_gated_refusals": runner.REPETITIONS,
              "ungated_wrong_adoptions": 2*runner.REPETITIONS,
              "heldout_per_adopted_arm": len(runner.HELDOUT),
              "median_full_seed_boot_ms": statistics.median(boot_ms),
              "median_gated_teach_call_ms": statistics.median(gated_ms),
              "median_ungated_teach_call_ms": statistics.median(ungated_ms),
              "median_all_teach_calls_ms": statistics.median(teach_ms)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    return result


if __name__ == "__main__":
    result = analyze()
    print(json.dumps({"passed": result["passed"], "checks": len(result["checks"]),
                      "analysis": str(OUT)}, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
