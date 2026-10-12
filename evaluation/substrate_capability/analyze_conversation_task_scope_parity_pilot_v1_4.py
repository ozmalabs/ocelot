#!/usr/bin/env python3
"""Independent parity, source-lock, and operation-work analysis for v1.4."""
from __future__ import annotations
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_4_lock_20261004.json"
CAP = ROOT / "evaluation/reports/conversation_task_scope_parity_pilot_v1_4_20261004.json"
OUT = ROOT / "evaluation/reports/conversation_task_scope_parity_pilot_v1_4_analysis_20261004.json"
EXPECTED = [("common_ground_stress", None), ("concurrent_goals", 2),
            ("concurrent_goals", 4), ("concurrent_goals", 8)]


def sha_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def main():
    errors = []
    lock = json.loads(LOCK.read_text())
    cap = json.loads(CAP.read_text())
    inputs = lock["locked_inputs"]

    def req(ok, message):
        if not ok:
            errors.append(message)

    req("term.rs" in inputs.get("rust_sources_sha256", {}), "term.rs absent from direct lock")
    req(cap["locked_inputs"] == inputs == cap["post_run_inputs"], "source-lock drift")
    req(all(cap["checks"].values()), "runner gate failed")
    req(len(cap["runs"]) == 3 and len({r["pid"] for r in cap["runs"]}) == 3, "worker process count mismatch")
    matrix = collections.Counter((c["case_id"], c.get("requested_goal_count"))
                                 for r in cap["runs"] for c in r["cases"])
    req(matrix == collections.Counter({item: 3 for item in EXPECTED}), "workload matrix mismatch")

    rows = []
    work_summary = collections.defaultdict(lambda: {
        "checkpoint_count": 0, "row_count": 0, "operation_ids": set(),
        "work_units": 0, "rule_uid_zero_units": 0,
        "work_units_by_kind": collections.Counter(), "work_units_by_scope": collections.Counter(), "work_kinds": set(),
        "candidate_pairs": 0, "term_evaluations": 0,
    })
    checkpoint_counts = collections.Counter()
    for run in cap["runs"]:
        for case in run["cases"]:
            mono = case["monolithic"]
            part = case["partition_sweep"]
            paired = case["paired"]
            req(mono["final_graph_digest"] == sha_json(mono["final_graph"]), "monolithic final digest mismatch")
            req(part["final_graph_digest"] == sha_json(part["final_graph"]), "partition final digest mismatch")
            req(mono["final_graph_digest"] == part["final_graph_digest"], "final graph mismatch")
            req(len(mono["checkpoints"]) == len(part["checkpoints"]), "checkpoint count mismatch")
            cp_equal = []
            for mode, payload in (("monolithic", mono), ("partition_sweep", part)):
                for cp in payload["checkpoints"]:
                    checkpoint_counts[(case["case_id"], case.get("requested_goal_count"), mode)] += 1
                    req(cp.get("closure", {}).get("status") == "fixed_point", "closure not at fixed point")
                    req(cp.get("work_trace_dropped") == 0, "work trace dropped rows")
                    req(not cp.get("runtime_access_trace"), "access trace unexpectedly enabled")
                    req(cp.get("candidate_pairs") == cp.get("scale_counters", {}).get("cand_enum", 0), "candidate counter mismatch")
                    req(cp.get("term_evaluations") == cp.get("scale_counters", {}).get("term_evals_total", 0), "term counter mismatch")
                    scope = work_summary[(case["case_id"], case.get("requested_goal_count"), mode)]
                    scope["checkpoint_count"] += 1
                    scope["candidate_pairs"] += int(cp.get("candidate_pairs", 0))
                    scope["term_evaluations"] += int(cp.get("term_evaluations", 0))
                    work = cp.get("runtime_work_trace", [])
                    req(bool(work), "empty operation-work trace")
                    for event in work:
                        req(len(event) == 6, "operation-work row shape mismatch")
                        if len(event) != 6:
                            continue
                        graph_scope, operation_id, rule_uid, kind, subject, units = event
                        req(int(operation_id) > 0 and isinstance(kind, str), "invalid operation-work identity")
                        units = int(units)
                        scope["row_count"] += 1
                        scope["operation_ids"].add(int(operation_id))
                        scope["work_units"] += units
                        scope["work_units_by_kind"][str(kind)] += units
                        scope["work_units_by_scope"][str(graph_scope)] += units
                        scope["work_kinds"].add(str(kind))
                        if int(rule_uid) == 0:
                            scope["rule_uid_zero_units"] += units
                if mode == "partition_sweep":
                    req(all(cp.get("deferred_effects_pending") is False for cp in payload["checkpoints"]), "deferred work remains")
                    scoped_kinds = set().union(*(set(event[3] for event in cp.get("runtime_work_trace", []) if len(event) == 6)
                                                 for cp in payload["checkpoints"]))
                    req({"scoped_scheduler_pass", "scoped_rule_attempt", "scoped_progressing_rule"}.issubset(scoped_kinds),
                        "scoped scheduler work events missing")
            for a, b in zip(mono["checkpoints"], part["checkpoints"]):
                cp_equal.append(a["graph_digest"] == b["graph_digest"])
            req(paired.get("final_graph_equal") == (mono["final_graph_digest"] == part["final_graph_digest"]), "paired final flag mismatch")
            req(paired.get("checkpoint_graph_equal") == cp_equal and all(cp_equal), "checkpoint parity mismatch")
            req(paired.get("goal_status_equal") is True, "goal-status mismatch")
            req(all(g["status"] == "resolved" for g in mono["goals"] + part["goals"]), "goal unresolved")
            req(all(q.get("progress_steps") == 0 and q.get("deferred_effects_pending") is False
                    for cp in part["checkpoints"] for q in cp.get("scope_quiescence", [])), "scope quiescence failed")
            req(all(q.get("frame_notifications_complete") is False
                    for cp in part["checkpoints"] for q in cp.get("scope_quiescence", [])), "notification completeness claim changed")
            rows.append({"replicate": run["replicate"], "case_id": case["case_id"],
                         "requested_goal_count": case.get("requested_goal_count"),
                         "checkpoint_count": len(cp_equal), "final_equal": paired["final_graph_equal"],
                         "scoped_calls": paired["partition_scoped_calls"]})

    by_case = []
    for key, value in sorted(work_summary.items(), key=lambda item: str(item[0])):
        by_case.append({"case_id": key[0], "requested_goal_count": key[1], "mode": key[2],
                        "checkpoint_count": value["checkpoint_count"], "work_rows": value["row_count"],
                        "operation_count": len(value["operation_ids"]), "work_units": value["work_units"],
                        "rule_uid_zero_work_units": value["rule_uid_zero_units"],
                        "rule_attributed_work_units": value["work_units"] - value["rule_uid_zero_units"],
                        "candidate_pairs": value["candidate_pairs"], "term_evaluations": value["term_evaluations"],
                        "work_units_by_kind": dict(sorted(value["work_units_by_kind"].items())),
                        "work_units_by_scope": dict(sorted(value["work_units_by_scope"].items())),
                        "work_kinds": sorted(value["work_kinds"])})
    expected_checkpoints = {("concurrent_goals", 2): 8, ("common_ground_stress", None): 10,
                            ("concurrent_goals", 4): 16, ("concurrent_goals", 8): 32}
    for (case_id, n), expected in expected_checkpoints.items():
        for mode in ("monolithic", "partition_sweep"):
            req(checkpoint_counts[(case_id, n, mode)] == expected * 3, f"checkpoint count mismatch: {case_id}/{n}/{mode}")
    result = {"schema": "ConversationTaskScopeParityPilotV1_4Analysis",
              "analysis_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "capture_sha256": hashlib.sha256(CAP.read_bytes()).hexdigest(),
              "gates_pass": not errors, "errors": errors, "checks": {"independent_analysis_pass": not errors},
              "paired_cases": rows,
              "summary": {"paired_case_count": len(rows), "checkpoint_pairs": sum(r["checkpoint_count"] for r in rows),
                          "final_state_matches": sum(r["final_equal"] for r in rows),
                          "operation_work_by_case_and_mode": by_case},
              "claim_boundary": cap["claim_boundary"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
