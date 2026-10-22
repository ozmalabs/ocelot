"""P11 scorecard integrity and registered-metric analyzer."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


VALID = {"NOT_RUN", "UNSUPPORTED", "TIMEOUT", "FAILED", "COMPLETED"}


def analyze(payload):
    if payload.get("schema") != "pmb-scorecard-v1":
        raise ValueError("expected pmb-scorecard-v1")
    records = payload.get("records")
    if not isinstance(records, list) or any(r.get("status") not in VALID for r in records):
        raise ValueError("missing or invalid trial status")
    if any(not all(k in r for k in ("family", "seed", "profile", "split")) for r in records):
        raise ValueError("record missing pairing identity")
    groups = defaultdict(list)
    paired = defaultdict(dict)
    for row in records:
        groups[(row["family"], row.get("direction"), row["profile"], row.get("control"))].append(row)
        paired[(row["family"], row.get("direction"), row["seed"], row.get("control"))][row["profile"]] = row
    summaries = {}
    for (family, direction, arm, control), rows in sorted(groups.items(), key=str):
        summaries[f"{family}/{direction}/{arm}/{control or 'registered'}"] = {
            "n": len(rows), "statuses": dict(sorted(Counter(r["status"] for r in rows).items())),
            "transferred": sum(r.get("transferred_process_adopted") is True for r in rows),
            "representation_adopted": sum(r.get("representation_adopted") is True for r in rows),
            "target_effect_verified": sum(r.get("target_effect_verified") is True for r in rows),
            "wrong_frame_acceptances": sum(r.get("wrong_frame_acceptance") is True for r in rows),
            "mean_exact_target_checks": (sum(r.get("exact_target_checks", 0) for r in rows) / len(rows)
                                         if rows else None),
            "mean_heldout_description_saving_bits": (
                sum((r.get("heldout_baseline_total_bits") or 0) -
                    (r.get("heldout_candidate_total_bits") or 0) for r in rows if r.get("profile") != "fresh") /
                max(1, sum(r.get("profile") != "fresh" for r in rows))),
            "mean_elapsed_s": sum(r.get("elapsed_s", 0) for r in rows) / max(1, len(rows)),
            "mean_graph_nodes": sum(r.get("graph_nodes", 0) for r in rows) / max(1, len(rows)),
        }
    pair_hash_failures = 0
    missing_arm_rows = 0
    exact_check_differences = []
    relative_exact_check_savings = []
    for key, arms in paired.items():
        if key[3] is not None:
            continue
        if not {"fresh", "source_exposed", "mismatched_source"}.issubset(arms):
            missing_arm_rows += 1
            continue
        hashes = {row.get("world_access_sha256") for row in arms.values()}
        pair_hash_failures += len(hashes) != 1
        fresh, source = arms["fresh"], arms["source_exposed"]
        # Exact-check savings are comparable only when both arms completed the
        # same target outcome. A fresh no-map abstention is explicitly unknown.
        if (fresh.get("outcome") == "transferred_effect_verified" and
                source.get("outcome") == "transferred_effect_verified"):
            exact_check_differences.append(fresh.get("exact_target_checks", 0) -
                                           source.get("exact_target_checks", 0))
            fresh_checks = fresh.get("exact_target_checks", 0)
            source_checks = source.get("exact_target_checks", 0)
            if fresh_checks:
                relative_exact_check_savings.append((fresh_checks - source_checks) / fresh_checks)
    controls = [r for r in records if r.get("control")]
    audit_failures = sum(
        r.get("agent_input_audit", {}).get("target_program_absent") is not True or
        r.get("agent_input_audit", {}).get("target_oracle_map_absent") is not True or
        r.get("agent_input_audit", {}).get("heldout_used_for_selection") is not False
        for r in records)
    source_verified = sum(r.get("transferred_process_adopted") is True
                          for r in records if r.get("profile") == "source_exposed" and not r.get("control"))
    source_n = sum(r.get("profile") == "source_exposed" and not r.get("control") for r in records)
    if missing_arm_rows or pair_hash_failures or audit_failures:
        primary_status = "INVALID"
    elif not exact_check_differences:
        primary_status = "NOT_ESTABLISHED"
    elif (relative_exact_check_savings and
          sum(relative_exact_check_savings) / len(relative_exact_check_savings) >= 0.25):
        primary_status = "PASS"
    else:
        primary_status = "FAIL"
    return {
        "schema": "pmb-linear-p11-v1-analysis-v1",
        "phase": payload.get("metadata", {}).get("phase"),
        "split": payload.get("metadata", {}).get("split"),
        "n_records": len(records), "groups": summaries,
        "paired_rows": len(paired), "paired_world_hash_failures": pair_hash_failures,
        "missing_arm_rows": missing_arm_rows,
        "matched_solved_exact_check_comparisons": len(exact_check_differences),
        "mean_exact_check_saving_fresh_minus_source": (
            sum(exact_check_differences) / len(exact_check_differences)
            if exact_check_differences else None),
        "mean_relative_exact_check_saving": (
            sum(relative_exact_check_savings) / len(relative_exact_check_savings)
            if relative_exact_check_savings else None),
        "wrong_frame_control_rows": sum(r.get("control") == "wrong_frame" for r in controls),
        "nonconjugate_control_rows": sum(r.get("control") == "nonconjugate" for r in controls),
        "wrong_frame_acceptances": sum(r.get("transferred_process_adopted") is True
                                        for r in controls if r.get("control") == "wrong_frame"),
        "nonconjugate_adoptions": sum(r.get("transferred_process_adopted") is True
                                       for r in controls if r.get("control") == "nonconjugate"),
        "source_transfers": source_verified, "source_rows": source_n,
        "source_transfer_rate": source_verified / source_n if source_n else None,
        "agent_input_audit_failures": audit_failures,
        "primary_status": primary_status,
        "primary_reason": ("no matched source/fresh solved outcomes with exact-check counts" if not exact_check_differences
                           else "paired exact-check savings compared with registered 25% threshold"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard", type=Path, nargs="?")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        sample = {"schema": "pmb-scorecard-v1", "metadata": {"phase": "linear-p11-v1"},
                  "records": [{"family": "p", "direction": "forward", "seed": 1,
                               "profile": arm, "split": "development", "status": "COMPLETED",
                               "outcome": "abstained_or_not_adopted", "exact_target_checks": 0,
                               "agent_input_audit": {"target_program_absent": True,
                                                      "target_oracle_map_absent": True,
                                                      "heldout_used_for_selection": False},
                               "world_access_sha256": "same"}
                              for arm in ("fresh", "source_exposed", "mismatched_source")]}
        result = analyze(sample)
        assert result["primary_status"] == "NOT_ESTABLISHED"
        assert result["paired_world_hash_failures"] == 0
        print("linear_p11_v1 analyzer self-check: PASS")
        return
    if args.scorecard is None:
        parser.error("scorecard is required unless --self-check is used")
    print(json.dumps(analyze(json.loads(args.scorecard.read_text())), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
