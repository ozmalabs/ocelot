#!/usr/bin/env python3
"""Independent gate and measurement reconstruction for v4.2."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_discourse_goal_identity_replicated_scale_v4_2_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/discourse_goal_identity_replicated_scale_v4_2_lock_20260926.json"
FIXTURE = ROOT / "tests/fixtures/conversational_manifold/phase3_same_addressee_concurrent_goals_scale_v4_1.json"
OUT = ROOT / "evaluation/reports/substrate_discourse_goal_identity_replicated_scale_v4_2_analysis_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cost(run: dict) -> dict:
    counters = {}
    for cp in run["checkpoints"]:
        for key, value in cp["settlement"].get("counters", {}).items():
            counters[key] = counters.get(key, 0) + int(value)
    return {"candidate_pairs": counters.get("cand_tested", 0),
            "term_evaluations": counters.get("term_evals_total", 0),
            "wall_ns": sum(int(cp["settlement"].get("wall_ns", 0)) for cp in run["checkpoints"]),
            "cpu_ns": sum(int(cp["settlement"].get("cpu_ns", 0)) for cp in run["checkpoints"]),
            "queue_turns": sum(int(cp["settlement"].get("turns", 0)) for cp in run["checkpoints"]),
            "frame_setup_ns": int(run["frame_setup_ns"]),
            "peak_rss_kib": int(run["peak_rss_kib"]),
            "rss_after_import_kib": run["rss_after_import_kib"],
            "rss_before_events_kib": run["rss_before_events_kib"],
            "rss_after_settlement_kib": run["rss_after_settlement_kib"],
            "rss_delta_events_to_settlement_kib": run["rss_after_settlement_kib"] - run["rss_before_events_kib"]}


def main() -> None:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    fixture = json.loads(FIXTURE.read_text())
    runs = raw["runs"]
    by_key = {(int(r["size"]), int(r["replicate"]), r["arm"]): r for r in runs}
    gates, reconstructed = {}, {}
    arms = ("temporal_full", "recipient_guard_full", "explicit_full", "explicit_owner_queue",
            "explicit_omit_wakeup")
    for size0 in fixture["goal_counts"]:
        size = int(size0); per_rep = {}; records = {arm: [] for arm in arms}
        for rep in range(3):
            rr = {arm: by_key[(size, rep, arm)] for arm in arms}
            t, rec, exp, own, omit = (rr[a] for a in arms)
            expected = {str(i): [size + 3*i + j for j in range(3)] for i in range(size)}
            paths = lambda run: {k: v["transition_event_indices"] for k, v in run["final_goals"].items()}
            owner_notifications = [(cp["event_index"], int(target))
                for cp in own["checkpoints"] for call in cp["settlement"].get("notifications", [])
                for target in call["native_owners"] if int(target) != int(call["source_frame"])]
            parity = [a["graph_digest"] == b["graph_digest"]
                      for a,b in zip(exp["checkpoints"], own["checkpoints"])]
            divergences = [i for i,(a,b) in enumerate(zip(exp["checkpoints"],omit["checkpoints"]))
                           if a["graph_digest"] != b["graph_digest"]]
            stale = all(omit["checkpoints"][size+3*i+2]["origin_receipts"].get(str(i)) == 0.0
                        for i in range(size))
            gates0 = {
                "five_arms_and_event_frame_counts": len(exp["checkpoints"]) == 4*size
                    and exp["frame_count"] == 2*size and exp["task_link_edges"] == 3*size,
                "global_arms_fixed_point": all(cp["complete"] for run in (t,rec,exp) for cp in run["checkpoints"]),
                "explicit_task_oracle": paths(exp) == expected and paths(own) == expected,
                "controls_fail_task_oracle": paths(t) != expected and paths(rec) != expected,
                "owner_exact_parity_each_checkpoint": len(parity) == 4*size and all(parity),
                "remote_notification_to_each_origin_at_result": all((size+3*i+2,i) in owner_notifications for i in range(size)),
                "omitted_receipt_stale_and_diverges": stale and bool(divergences),
                "recovery_restores_exact_graph": omit["final_graph_digest"] == exp["final_graph_digest"],
                "owner_receipts_resolved": own["final_origin_receipts"] == {str(i):1.0 for i in range(size)},
                "scoped_reports_complete": all(cp["complete"] for run in (own,omit) for cp in run["checkpoints"]),
                "rss_samples_present": all(run[k] is not None for run in rr.values()
                    for k in ("rss_after_import_kib","rss_before_events_kib","rss_after_settlement_kib")),
            }
            per_rep[str(rep)] = gates0
            for arm, run in rr.items(): records[arm].append({"replicate":rep, **cost(run)})
        gates[str(size)] = per_rep
        summary_arms = {}
        for arm, rows in records.items():
            summary_arms[arm] = {"per_replicate":rows}
            for metric in rows[0]:
                if metric == "replicate": continue
                values = [row[metric] for row in rows]
                summary_arms[arm][metric+"_median"] = statistics.median(values)
                summary_arms[arm][metric+"_range"] = [min(values),max(values)]
        ratios = {metric: [records["explicit_owner_queue"][i][metric]/max(1,records["explicit_full"][i][metric])
                           for i in range(3)] for metric in ("candidate_pairs","term_evaluations","wall_ns")}
        reconstructed[str(size)] = {"event_count":4*size,"frame_count":2*size,"checkpoint_count":4*size,
            "arms":summary_arms,"owner_over_full_ratios_by_replicate":ratios,
            "owner_over_full_ratio_medians":{k:statistics.median(v) for k,v in ratios.items()},
            "task_paths_expected":{str(i):[size+3*i+j for j in range(3)] for i in range(size)}}
    pid_unique = len(runs) == 45 and len({r["pid"] for r in runs}) == 45
    checks = {
        "runner_summary_checks_pass": all(raw["checks"].values()),
        "lock_hash_and_locked_inputs_match": raw["lock_sha256"] == sha(LOCK)
            and raw["locked_inputs"] == lock["locked_inputs"],
        "fixture_hash_matches_lock": raw["locked_inputs"]["fixture_sha256"] == sha(FIXTURE),
        "all_45_workers_distinct": pid_unique,
        "complete_size_reconstruction": len(by_key) == 45 and all(len(v)==3 for v in gates.values()),
        "all_independent_semantic_and_memory_gates_pass": all(all(all(v.values()) for v in rows.values())
                                                                  for rows in gates.values()),
        "all_costs_reconstruct_runner_summary": all(
            reconstructed[str(size)]["arms"][arm]["candidate_pairs_median"] == raw["summary"][str(size)]["arms"][arm]["candidate_pairs_median"]
            for size in fixture["goal_counts"] for arm in arms),
    }
    result={"schema_version":1,"run_id":"substrate-discourse-goal-identity-replicated-scale-v4.2-analysis-20260926",
        "raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"fixture_sha256":sha(FIXTURE),
        "checks":checks,"replicate_gates":gates,"summary":reconstructed,
        "claim_boundary":raw["claim_boundary"],
        "interpretation":"Three fresh-process replicates of one generated N=16/32/64 identity-link workload. RSS is current process residency delta across event construction and settlement, not allocator attribution. No production producer integration, natural-task distribution, or formal asymptotic claim is established."}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT),"checks":checks,"summary":reconstructed},indent=2))
    if not all(checks.values()): raise SystemExit("independent v4.2 reconstruction found a mismatch")

if __name__ == "__main__": main()
