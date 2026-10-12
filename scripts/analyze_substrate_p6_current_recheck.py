#!/usr/bin/env python3
"""Derive paired P6 task transitions from current and historical artifacts."""
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "evaluation/reports/substrate_p6_current_recheck_20260925.json"
HISTORICAL = ROOT / "results/prog_synthesis_battery.json"
OUT = ROOT / "evaluation/reports/substrate_p6_recheck_analysis_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def arm_delta(current_rows: list[dict], prior_rows: list[dict]) -> dict:
    cur = {r["task_id"]: r for r in current_rows}
    old = {r["task_id"]: r for r in prior_rows}
    shared = sorted(set(cur) & set(old))
    transition = Counter((old[k]["outcome"], cur[k]["outcome"]) for k in shared)
    prior_pass = {k for k in shared if old[k]["outcome"] == "accepted_holdout_ok"}
    current_pass = {k for k in shared if cur[k]["outcome"] == "accepted_holdout_ok"}
    strata = sorted({cur[k]["stratum"] for k in shared})
    per_stratum = {}
    for stratum in strata:
        ids = [k for k in shared if cur[k]["stratum"] == stratum]
        per_stratum[stratum] = {
            "n": len(ids),
            "prior_passes": sum(old[k]["outcome"] == "accepted_holdout_ok" for k in ids),
            "current_passes": sum(cur[k]["outcome"] == "accepted_holdout_ok" for k in ids),
            "gained_pass_ids": sorted((current_pass - prior_pass) & set(ids)),
            "lost_pass_ids": sorted((prior_pass - current_pass) & set(ids)),
        }
    return {
        "prior_rows": len(old), "current_rows": len(cur), "paired_rows": len(shared),
        "prior_strict_passes": len(prior_pass), "current_strict_passes": len(current_pass),
        "gained_pass_ids": sorted(current_pass - prior_pass),
        "lost_pass_ids": sorted(prior_pass - current_pass),
        "transition_counts_prior_to_current": {
            f"{before} -> {after}": count
            for (before, after), count in sorted(transition.items())
        },
        "per_stratum": per_stratum,
    }


def main() -> None:
    current = json.loads(CURRENT.read_text(encoding="utf-8"))
    historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    analyses = {
        "main_current_vs_historical_main_postfix": arm_delta(
            current["arms"]["main"]["rows"], historical["arms"]["main_postfix"]["rows"]),
        "frozen_current_vs_historical_frozen": arm_delta(
            current["arms"]["frozen"]["rows"], historical["arms"]["frozen"]["rows"]),
        "main_current_vs_frozen_current": arm_delta(
            current["arms"]["main"]["rows"], current["arms"]["frozen"]["rows"]),
    }
    measurement = {
        "current_main_twin_run_deterministic": current["determinism"]["identical"],
        "current_main_twin_run_hashes": [current["determinism"]["outcome_hash_run1"],
                                          current["determinism"]["outcome_hash_run2"]],
        "current_main_minus_frozen_newcombe": current["delta_main_minus_frozen"]["overall"],
        "current_main_strata": current["arms"]["main"]["aggregates"]["per_stratum"],
        "current_frozen_strata": current["arms"]["frozen"]["aggregates"]["per_stratum"],
        "current_main_outcome_taxonomy": current["failure_taxonomy"]["main"],
        "current_frozen_outcome_taxonomy": current["failure_taxonomy"]["frozen"],
        "current_engine_seed_version": json.loads((ROOT / "seeds/program_synthesis.json").read_text())["version"],
        "historical_postfix_seed": historical.get("arms", {}).get("main_postfix", {}).get("provenance", {}).get("seed"),
        "current_live_c_battery": {
            "n": current["c_battery"]["live_pinned_path"].get("n"),
            "n_ok": current["c_battery"]["live_pinned_path"].get("n_ok"),
            "regression_count": len(current["c_battery"]["live_pinned_path"].get("regressions_ok_to_fail", [])),
            "improvement_count": len(current["c_battery"]["live_pinned_path"].get("improvements_fail_to_ok", [])),
        },
    }
    payload = {
        "schema_version": 1,
        "analysis_id": "substrate-p6-current-recheck-analysis-20260925",
        "claim_boundary": "Post-hoc task-identity analysis of an existing current-source replication and historical known-outcome artifacts; no new benchmark instances and no confirmatory claim.",
        "measurement_summary": measurement,
        "paired_transition_analysis": analyses,
        "provenance": {
            "analysis_script_sha256": sha(Path(__file__).resolve()),
            "current_run_report_sha256": sha(CURRENT),
            "historical_result_sha256": sha(HISTORICAL),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUT),
        "main_current_vs_historical_main_postfix": {
            "prior_passes": analyses["main_current_vs_historical_main_postfix"]["prior_strict_passes"],
            "current_passes": analyses["main_current_vs_historical_main_postfix"]["current_strict_passes"],
            "gains": len(analyses["main_current_vs_historical_main_postfix"]["gained_pass_ids"]),
            "losses": len(analyses["main_current_vs_historical_main_postfix"]["lost_pass_ids"]),
        },
        "frozen_current_vs_historical_frozen": {
            "prior_passes": analyses["frozen_current_vs_historical_frozen"]["prior_strict_passes"],
            "current_passes": analyses["frozen_current_vs_historical_frozen"]["current_strict_passes"],
            "gains": len(analyses["frozen_current_vs_historical_frozen"]["gained_pass_ids"]),
            "losses": len(analyses["frozen_current_vs_historical_frozen"]["lost_pass_ids"]),
        },
        "main_minus_frozen": measurement["current_main_minus_frozen_newcombe"],
    }, indent=2))


if __name__ == "__main__":
    main()
