#!/usr/bin/env python3
"""Compare the preserved post-filter and matcher-pushdown CAN frame runs."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "evaluation/reports/substrate_can_boundary_frames_postfilter_baseline_20260924.json"
TREATMENT = ROOT / "evaluation/reports/substrate_can_boundary_frames_20260924.json"
OUT = ROOT / "evaluation/reports/substrate_can_boundary_frames_scope_pushdown_comparison_20260924.json"
POLICIES = {
    "round_robin": ("audit_round_robin_frame_counters", "scoped_round_robin_wall_ns"),
    "dependency_wakeup": ("audit_dependency_wakeup_frame_counters", "dependency_wakeup_wall_ns"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def total(row: dict, field: str, metric: str) -> int:
    return sum(frame.get(metric, 0) for frame in row[field])


def main() -> None:
    baseline = json.loads(BASELINE.read_text())
    treatment = json.loads(TREATMENT.read_text())
    key_fields = ("n", "topology", "mode", "replicate")
    bmap = {tuple(row[k] for k in key_fields): row for row in baseline["workers"]}
    tmap = {tuple(row[k] for k in key_fields): row for row in treatment["workers"]}
    if len(bmap) != 48 or len(tmap) != 48 or bmap.keys() != tmap.keys():
        raise SystemExit("baseline/treatment worker-key mismatch")
    if baseline["provenance"]["benchmark_harness_sha256"] != treatment["provenance"]["script_sha256"]:
        raise SystemExit("baseline and treatment harness hashes differ")

    cases = []
    same_states = {"monolithic": 0, "round_robin": 0, "dependency_wakeup": 0}
    all_correct = True
    for key, old in sorted(bmap.items()):
        new = tmap[key]
        matches = {
            "monolithic": old["monolithic_states"] == new["monolithic_states"],
            "round_robin": old["scoped_states"] == new["scoped_states"],
            "dependency_wakeup": old["dependency_wakeup_states"] == new["dependency_wakeup_states"],
        }
        for policy, same in matches.items():
            same_states[policy] += int(same)
        all_correct &= all(matches.values())
        for worker in (old, new):
            all_correct &= (
                worker["monolithic_fixed_point_residuals"] == 0
                and worker["scoped_fixed_point_residuals"] == 0
                and worker["dependency_wakeup_fixed_point_residuals"] == 0
                and worker["monolithic_terminal_probe"] == 0
                and all(x == 0 for x in worker["scoped_frame_terminal_probes"])
                and all(x == 0 for x in worker["dependency_wakeup_terminal_probes"])
                and worker["audit_monolithic_progress_matches"]
                and worker["audit_monolithic_state_matches"]
                and worker["audit_round_robin_progress_matches"]
                and worker["audit_round_robin_state_matches"]
                and worker["audit_dependency_wakeup_state_matches"]
                and worker["audit_dependency_wakeup_steps_match"]
            )
        record = {k: old[k] for k in key_fields}
        record["all_policy_states_match_between_builds"] = all(matches.values())
        record["policy_state_matches"] = matches
        record["monolithic_candidate_pairs"] = {
            "pre_pushdown": old["audit_monolithic_counters"]["cand_enum"],
            "pushdown": new["audit_monolithic_counters"]["cand_enum"],
        }
        for policy, (counter_field, time_field) in POLICIES.items():
            record[f"{policy}_candidate_pairs"] = {
                "pre_pushdown": total(old, counter_field, "cand_enum"),
                "pushdown": total(new, counter_field, "cand_enum"),
            }
            record[f"{policy}_term_evaluations"] = {
                "pre_pushdown": total(old, counter_field, "term_evals_total"),
                "pushdown": total(new, counter_field, "term_evals_total"),
            }
            record[f"{policy}_wall_time_ns"] = {
                "pre_pushdown": old[time_field], "pushdown": new[time_field],
            }
        cases.append(record)

    groups = []
    for n in (16, 32):
        for policy, (counter_field, time_field) in POLICIES.items():
            rows = [x for x in cases if x["n"] == n]
            ratios = {"candidate_pairs": [], "term_evaluations": [], "wall_time_old_over_new": []}
            candidate_over_mono = {"pre_pushdown": [], "pushdown": []}
            term_over_mono = {"pre_pushdown": [], "pushdown": []}
            for row in rows:
                old = bmap[tuple(row[k] for k in key_fields)]
                new = tmap[tuple(row[k] for k in key_fields)]
                old_cand = total(old, counter_field, "cand_enum")
                new_cand = total(new, counter_field, "cand_enum")
                old_term = total(old, counter_field, "term_evals_total")
                new_term = total(new, counter_field, "term_evals_total")
                ratios["candidate_pairs"].append(old_cand / new_cand if new_cand else 0.0)
                ratios["term_evaluations"].append(old_term / new_term if new_term else 0.0)
                ratios["wall_time_old_over_new"].append(
                    old[time_field] / new[time_field] if new[time_field] else 0.0
                )
                old_mono = old["audit_monolithic_counters"]
                new_mono = new["audit_monolithic_counters"]
                candidate_over_mono["pre_pushdown"].append(old_cand / old_mono["cand_enum"])
                candidate_over_mono["pushdown"].append(new_cand / new_mono["cand_enum"])
                term_over_mono["pre_pushdown"].append(old_term / old_mono["term_evals_total"])
                term_over_mono["pushdown"].append(new_term / new_mono["term_evals_total"])
            groups.append({
                "n": n, "policy": policy, "paired_cases": len(rows),
                "median_candidate_pairs_old_over_new": statistics.median(ratios["candidate_pairs"]),
                "median_term_evaluations_old_over_new": statistics.median(ratios["term_evaluations"]),
                "median_candidate_pairs_over_monolithic": {
                    k: statistics.median(v) for k, v in candidate_over_mono.items()
                },
                "median_term_evaluations_over_monolithic": {
                    k: statistics.median(v) for k, v in term_over_mono.items()
                },
                "median_wall_time_old_over_new_descriptive_only": statistics.median(ratios["wall_time_old_over_new"]),
            })

    payload = {
        "run_id": "substrate-can-boundary-scope-pushdown-comparison-20260924",
        "question": "Does guarded has_concept scope prebinding reduce frame-scoped candidate and term work without changing outputs?",
        "measurement_note": "The baseline and treatment batches were run sequentially (treatment then baseline), not counterbalanced. Wall-time ratios are descriptive only; operation-count reductions and state parity are the primary result.",
        "correctness": {"all_policy_states_match_between_builds": all(v == 48 for v in same_states.values()),
                        "identical_state_case_counts": same_states,
                        "all_full_graph_fixed_points_terminal_probes_and_audit_parity": all_correct},
        "builds": {
            "pre_pushdown_native_extension_sha256": baseline["provenance"]["native_extension_sha256"],
            "pushdown_native_extension_sha256": treatment["provenance"]["native_extension_sha256"],
            "pre_pushdown_build_source_hashes": baseline["provenance"]["native_extension_build_source_sha256"],
            "pushdown_source_hashes": {k: treatment["provenance"][k] for k in (
                "script_sha256", "substrate_source_sha256", "rewrite_source_sha256", "term_source_sha256"
            )},
        },
        "inputs": {"baseline_json_sha256": sha(BASELINE), "treatment_json_sha256": sha(TREATMENT),
                   "comparison_script_sha256": sha(Path(__file__).resolve())},
        "summaries": groups,
        "cases": cases,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"cases": len(cases), "groups": len(groups),
                      "correctness": payload["correctness"], "output": str(OUT)}, indent=2))
    if not all_correct or same_states != {k: 48 for k in same_states}:
        raise SystemExit("pushdown comparison correctness gate failed")


if __name__ == "__main__":
    main()
