#!/usr/bin/env python3
"""Compare the current MBPP Arc 3 recheck to its historical Arc 3 artifact."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "evaluation/reports/substrate_mbpp_arc3_current_recheck_20260925.json"
HISTORICAL = ROOT / "results/mbpp_arc3_endgame.json"
SEED = ROOT / "seeds/program_synthesis.json"
OUT = ROOT / "evaluation/reports/substrate_mbpp_arc3_recheck_analysis_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    current = json.loads(CURRENT.read_text(encoding="utf-8"))
    historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    arms = {}
    for name in ("full_r3", "no_retrieval", "official_r3"):
        old = historical["arms"][name]
        new = current["arms"][name]
        old_pass = {r["task_id"] for r in old["runnable_rows"] if r["outcome"] == "pass"}
        new_pass = {r["task_id"] for r in new["runnable_rows"] if r["outcome"] == "pass"}
        arms[name] = {
            "historical_measured_at": historical["measured_at"],
            "historical_seed_stack": historical["condition"]["arms"][name],
            "historical_pass_count": len(old_pass),
            "current_pass_count": len(new_pass),
            "gained_task_ids": sorted(new_pass - old_pass),
            "lost_task_ids": sorted(old_pass - new_pass),
            "current_outcome_taxonomy": current["arms"][name]["outcome_taxonomy"],
            "current_deterministic": current["arms"][name]["determinism"]["identical"],
            "interpretation": "Known-task recheck across materially different source/seed generations; changed task outcomes cannot be attributed to one component.",
        }

    full = {r["task_id"]: r for r in current["arms"]["full_r3"]["runnable_rows"]}
    no_ret = {r["task_id"]: r for r in current["arms"]["no_retrieval"]["runnable_rows"]}
    transitions = Counter((full[t]["outcome"], no_ret[t]["outcome"]) for t in full.keys() & no_ret.keys())
    payload = {
        "schema_version": 1,
        "analysis_id": "substrate-mbpp-arc3-recheck-analysis-20260925-v1",
        "scope": "Pass-identity version drift plus current paired full-retrieval/no-retrieval outcome transitions; no rerun of synthesis.",
        "current_report_sha256": sha(CURRENT),
        "historical_report_sha256": sha(HISTORICAL),
        "current_seed": {"id": seed["id"], "version": seed["version"], "sha256": sha(SEED)},
        "split_counts": current["split_counts"],
        "current_pair": {
            "full_minus_no_retrieval": current["hr1"]["delta_full_r3_minus_no_retrieval"],
            "net_passes": current["hr1"]["net_passes"],
            "gains": current["hr1"]["gains_full_r3_over_no_retrieval"],
            "losses": current["hr1"]["losses_no_retrieval_over_full_r3"],
            "full_vs_no_retrieval_outcome_transition_counts": {
                f"{a} -> {b}": n for (a, b), n in sorted(transitions.items())
            },
        },
        "version_drift": arms,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "current_seed": payload["current_seed"],
                      "version_drift": {a: {"historical_pass_count": v["historical_pass_count"],
                                            "current_pass_count": v["current_pass_count"],
                                            "gains": len(v["gained_task_ids"]),
                                            "losses": len(v["lost_task_ids"])}
                                         for a, v in arms.items()},
                      "paired_transition_counts": payload["current_pair"]["full_vs_no_retrieval_outcome_transition_counts"]},
                     indent=2))


if __name__ == "__main__":
    main()
