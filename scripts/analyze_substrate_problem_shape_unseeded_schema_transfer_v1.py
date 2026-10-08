#!/usr/bin/env python3
"""Independent integrity and outcome analysis for the ProblemShape transfer panel."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/problem_shape_unseeded_schema_transfer_v1_20260927.json"
OUT = ROOT / "evaluation/reports/problem_shape_unseeded_schema_transfer_v1_analysis_20260927.json"


def main():
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    checks = {
        "ten_runs": len(runs) == 10,
        "unique_processes": len({r.get("pid") for r in runs}) == 10,
        "two_replicates_each": all(sum(r["scenario"] == s for r in runs) == 2 for s in (
            "seeded_exact_control", "singleton_controls", "relax_recurrence_transfer",
            "bp_recurrence_transfer", "mixed_family_separation")),
        "locked_sources_match": all(r.get("source_stable") and
            r.get("worker_inputs_before") == raw["locked_inputs"] == r.get("worker_inputs_after")
            for r in runs) and raw["post_run_inputs"] == raw["locked_inputs"],
        "resolved_goals_and_fixed_points": all(
            all(g["status"] == "resolved" for g in r["goal_resolution"]) and
            r["all_post_observe_fixed_point"] for r in runs),
    }
    for scenario in ("seeded_exact_control", "singleton_controls", "relax_recurrence_transfer",
                     "bp_recurrence_transfer", "mixed_family_separation"):
        cells = [r for r in runs if r["scenario"] == scenario]
        key = f"{scenario}_outcomes_match"
        checks[key] = len(cells) == 2 and all(r["worker_returncode"] == 0 for r in cells)
        if scenario == "seeded_exact_control":
            checks[key] &= all(len(r["records"]) == 2 and all(
                x["observation_status_initial"] == x["observation_status_final"] == "recognized"
                for x in r["records"]) and r["total_mints"] == r["total_new_shapes"] == 0 for r in cells)
        elif scenario == "singleton_controls":
            checks[key] &= all(
                [x["observation_status_initial"] for x in r["records"]] == ["residual"] * 2 and
                [x["observation_status_final"] for x in r["records"]] == ["residual"] * 2 and
                len({x["signature_key"] for x in r["records"]}) == 2 and
                r["total_mints"] == r["total_new_shapes"] == 0 for r in cells)
        elif scenario in ("relax_recurrence_transfer", "bp_recurrence_transfer"):
            checks[key] &= all(
                [x["observation_status_initial"] for x in r["records"]] == ["residual", "recognized"] and
                [x["observation_status_final"] for x in r["records"]] == ["recognized"] * 2 and
                r["total_mints"] == r["total_new_shapes"] == 1 and
                len({x["signature_key"] for x in r["records"]}) == 1 for r in cells)
        else:
            checks[key] &= all(len(r["records"]) == 4 and
                r["total_mints"] == r["total_new_shapes"] == 2 and
                [x["observation_status_final"] for x in r["records"]] == ["recognized"] * 4 and
                len({x["signature_key"] for x in r["records"] if x["solver_family"] == "relax"}) == 1 and
                len({x["signature_key"] for x in r["records"] if x["solver_family"] == "bp"}) == 1 and
                {x["signature_key"] for x in r["records"] if x["solver_family"] == "relax"}.isdisjoint(
                    {x["signature_key"] for x in r["records"] if x["solver_family"] == "bp"}) for r in cells)
    work = {}
    for scenario in ("seeded_exact_control", "singleton_controls", "relax_recurrence_transfer",
                     "bp_recurrence_transfer", "mixed_family_separation"):
        rows = [x for r in runs if r["scenario"] == scenario for x in r["records"]]
        work[scenario] = {"observations": len(rows),
            "candidate_pairs_total": sum(x["problem_shape_candidate_pairs"] for x in rows),
            "term_evaluations_total": sum(x["problem_shape_term_evaluations"] for x in rows),
            "mint_events": sum(x["mint_count_delta"] for x in rows),
            "new_shapes": sum(x["problem_shape_count_delta"] for x in rows)}
    result = {"schema_version": 1, "raw_report": str(RAW.relative_to(ROOT)),
        "checks": checks, "all_checks_pass": all(checks.values()), "by_scenario": work,
        "claim_boundary": "Independent consistency check of this preregistered two-schema synthetic CAN panel; not open-ended concept invention or natural novelty prevalence."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "checks": checks,
                      "all_checks_pass": result["all_checks_pass"]}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
