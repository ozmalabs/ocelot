#!/usr/bin/env python3
"""Independent semantic, lineage, and cost checks for code-write transfer."""
from __future__ import annotations
import hashlib, json, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(Path(__file__).resolve().parent)]
RAW = ROOT / "evaluation/reports/substrate_independent_adequacy_codewrite_transfer_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_independent_adequacy_codewrite_transfer_v1_analysis_20261002.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze() -> dict:
    import substrate_independent_adequacy_codewrite_transfer_v1 as runner
    from independent_codewrite_oracles import label
    capture = json.loads(RAW.read_text())
    current = runner.lock_payload()
    lock_stable = capture["lock"] == capture["post_lock"] == current
    expected_oracle_sha = capture["lock"]["active"]["oracle"]
    actual_oracle_sha = sha(runner.ORACLE)
    checks = [{"case": "source-lock-stable", "pass": lock_stable},
              {"case": "oracle-source-hash-current", "pass": expected_oracle_sha == actual_oracle_sha}]
    heldout_counts = {"parity": 41, "clamp": 20}
    for worker in capture["workers"]:
        rep = worker["repetition"]
        checks.append({"rep": rep, "case": "starter-codebook-abstains",
                       "pass": all(row.get("ok") is False for row in worker["baselines"].values())})
        neg = worker["negative"]
        checks.append({"rep": rep, "case": "identity-square-rejected-after-known-fit",
                       "pass": neg["receipt_status"] == "rejected" and neg["teach_ok"] is False
                       and neg["contract_passed"] is True and neg["candidate_id_matches"] is True
                       and neg["state_unchanged"] is True})
        evidence_cells = [("square", neg)] + [(task, worker["positive"][task]) for task in ("parity", "clamp")]
        for task, cell in evidence_cells:
            lineage_ok = cell["oracle_source_id"] == f"independent-codewrite-oracle-v1:{expected_oracle_sha}"
            rows_ok = True
            for row in cell["audit_rows"]:
                for lrow in row["labels"]:
                    lineage_ok = lineage_ok and lrow.get("oracle_sha256") == expected_oracle_sha
                    lineage_ok = lineage_ok and lrow.get("source_id") == cell["oracle_source_id"]
                    lineage_ok = lineage_ok and lrow.get("expected") == label(task, row["inputs"])
            checks.append({"rep": rep, "case": f"{task}-audit-label-lineage", "pass": lineage_ok})
            if task == "square":
                continue
            checks.append({"rep": rep, "case": f"{task}-receipt-adopted",
                           "pass": cell["receipt_status"] == "accepted" and cell["teach_ok"] is True
                           and cell["contract_passed"] is True and cell["candidate_id_matches"] is True
                           and cell["epoch_increment"] == 1})
            transfer = cell["transfer"]
            outputs_ok = (transfer["written"]["ok"] is True and transfer["composed_ok"] is True
                          and len(transfer["rows"]) == heldout_counts[task]
                          and all(row["expected"] == label(task, row["inputs"])
                                  and row["native_output"] == row["expected"]
                                  and row["python_output"] == row["expected"]
                                  for row in transfer["rows"]))
            checks.append({"rep": rep, "case": f"{task}-heldout-native-and-python-transfer", "pass": outputs_ok})
        checks.append({"rep": rep, "case": "worker-active-source-stable",
                       "pass": worker["active_after"] == capture["lock"]["active"]})
    boot_ms = [w["boot_ns"]/1e6 for w in capture["workers"]]
    neg_ms = [w["negative"]["wall_ns"]/1e6 for w in capture["workers"]]
    parity_ms = [w["positive"]["parity"]["teach_ns"]/1e6 for w in capture["workers"]]
    clamp_ms = [w["positive"]["clamp"]["teach_ns"]/1e6 for w in capture["workers"]]
    result = {"schema": "SubstrateIndependentAdequacyCodewriteTransferV1Analysis",
              "passed": all(item["pass"] for item in checks), "checks": checks,
              "repetitions": len(capture["workers"]), "positive_tasks": ["parity", "clamp"],
              "negative_controls": ["identity-as-square with one known fit"],
              "heldout_totals": {task: heldout_counts[task]*len(capture["workers"]) for task in heldout_counts},
              "median_full_seed_boot_ms": statistics.median(boot_ms),
              "median_negative_refusal_ms": statistics.median(neg_ms),
              "median_parity_accept_and_teach_ms": statistics.median(parity_ms),
              "median_clamp_accept_and_teach_ms": statistics.median(clamp_ms)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    return result


if __name__ == "__main__":
    result = analyze()
    print(json.dumps({"passed": result["passed"], "checks": len(result["checks"]),
                      "analysis": str(OUT)}, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
