#!/usr/bin/env python3
"""Independent work/counter reconciliation for live self-report trace v1."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/live_self_report_work_trace_v1_2_20260928.json"
OUT = ROOT / "evaluation/reports/live_self_report_work_trace_v1_2_analysis_20260928.json"
SCHEDULER = {
    "scheduler_pass": "scheduler_passes",
    "scheduler_external_poll_slots": "scheduler_external_poll_slots",
    "scheduler_fixedpoint_probe_slots": "scheduler_fixedpoint_probe_slots",
    "scheduler_dirty_vector_slots": "scheduler_dirty_vector_slots",
    "scheduler_selected_rules": "scheduler_selected_rules",
}
FAMILIES = {"rule_edits": 1, "rule_patches": 2, "fb_samples": 3, "track_identity": 4, "net_collapses": 5}
METRICS = list(SCHEDULER.values()) + [
    f"deferred_queue:{family}:{suffix}" for family in FAMILIES
    for suffix in ("enqueued_items", "drain_batches", "drained_items")
]


def metric_for(kind: str, subject: int | None) -> str | None:
    if kind in SCHEDULER:
        return SCHEDULER[kind]
    family = next((name for name, code in FAMILIES.items() if code == subject), None)
    suffix = {"deferred_queue_enqueue_items": "enqueued_items",
              "deferred_queue_drain_batches": "drain_batches",
              "deferred_queue_drained_items": "drained_items"}.get(kind)
    return f"deferred_queue:{family}:{suffix}" if kind.startswith("deferred_queue_") and family and suffix else None


def reconcile_work(turn: dict) -> dict:
    rows = turn["all_scope_work_rows"]
    trace: Counter[tuple[int, str]] = Counter()
    kinds: dict[int, int] = {}
    scopes: set[int] = set()
    valid = True
    for row in rows:
        if len(row) != 6:
            valid = False
            continue
        scope, operation, _uid, kind, subject, units = row
        scope, operation, units = int(scope), int(operation), int(units)
        subject = None if subject is None else int(subject)
        scopes.add(scope)
        valid &= scope > 0 and operation > 0 and units > 0
        if kind == "operation_kind":
            valid &= subject in (1, 2, 3) and units == 1 and operation not in kinds
            if subject is not None:
                kinds[operation] = subject
        else:
            metric = metric_for(kind, subject)
            valid &= metric is not None
            if metric:
                trace[(scope, metric)] += units
    scoped: Counter[tuple[int, str]] = Counter()
    for scope, name, value in turn["all_scope_scale_counters"]:
        scoped[(int(scope), str(name))] += int(value)
    keys = set(trace) | {(scope, name) for scope, name in scoped
                         if name in METRICS or name.startswith("deferred_queue:")}
    scope_deltas = {f"{s}:{n}": scoped[(s, n)] - trace[(s, n)] for s, n in sorted(keys)}
    global_deltas = {}
    for name in METRICS:
        global_deltas[name] = int(turn["scale_counters"].get(name, 0)) - sum(
            value for (_, metric), value in scoped.items() if metric == name)
    operation_ids = {int(row[1]) for row in rows}
    passed = (valid and int(turn["all_scope_work_dropped"]) == 0
              and bool(scopes) and set(kinds) == operation_ids
              and all(v == 0 for v in scope_deltas.values())
              and all(v == 0 for v in global_deltas.values()))
    return {"pass": passed, "scope_count": len(scopes), "operation_count": len(operation_ids),
            "operation_kinds": dict(sorted(Counter(kinds.values()).items())),
            "work_row_count": len(rows), "scope_deltas": scope_deltas,
            "process_global_deltas": global_deltas}


def reconcile_matcher(turn: dict) -> dict:
    scale = turn["scale_counters"]
    global_tests = int(scale.get("cand_tested", 0))
    unattributed = int(scale.get("cand_tested_unattributed", 0))
    metadata = {int(row[0]): {"name": str(row[2]), "arity": int(row[3]), "ambiguous": bool(row[4])}
                for row in turn["rule_metadata"]}
    per_rule: Counter[int] = Counter()
    clauses: Counter[int] = Counter()
    missing = set()
    invalid_clause = []
    ambiguous_hits = []
    for rule_id, metric, value in turn["per_rule"]:
        rule_id, value = int(rule_id), int(value)
        if rule_id not in metadata:
            missing.add(rule_id)
        if metric == "candidate_tests":
            per_rule[rule_id] += value
    for rule_id, position, value in turn["per_clause"]:
        rule_id, position, value = int(rule_id), int(position), int(value)
        info = metadata.get(rule_id)
        if info is None:
            missing.add(rule_id)
        elif info["ambiguous"]:
            ambiguous_hits.append([rule_id, position, value])
        elif position >= info["arity"]:
            invalid_clause.append([rule_id, position, info["arity"], value])
        else:
            clauses[rule_id] += value
    attributed = global_tests - unattributed
    term_total = int(scale.get("term_evals_total", 0))
    term_unattributed = int(scale.get("term_evals_unattributed", 0))
    term_per_rule = sum(int(v) for _, name, v in turn["per_rule"] if name == "term_evaluations")
    term_variants = sum(int(v) for name, v in scale.items() if name.startswith("term_eval:"))
    return {
        "candidate_global": global_tests, "candidate_unattributed": unattributed,
        "candidate_attributed": attributed, "candidate_per_rule": sum(per_rule.values()),
        "candidate_per_clause": sum(clauses.values()), "term_global": term_total,
        "term_unattributed": term_unattributed, "term_per_rule": term_per_rule,
        "term_variant_total": term_variants, "missing_rule_metadata_ids": sorted(missing),
        "invalid_clauses": invalid_clause, "ambiguous_clause_hits": ambiguous_hits,
        "checks": {
            "candidate_attributed_plus_unattributed": attributed + unattributed == global_tests,
            "candidate_per_rule_conserves_attributed": sum(per_rule.values()) == attributed,
            "candidate_per_clause_conserves_attributed": sum(clauses.values()) == attributed,
            "all_attributed_candidates_have_metadata": not missing,
            "all_clause_positions_valid": not invalid_clause and not ambiguous_hits,
            "term_attributed_plus_unattributed": term_per_rule + term_unattributed == term_total,
            "term_variant_total_matches_global": term_variants == term_total,
        },
    }


def main() -> None:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    checks = {
        "capture_status_complete": raw.get("capture_status") == "complete",
        "three_fresh_workers": len(runs) == 3 and len({r["pid"] for r in runs}) == 3,
        "replicates_0_1_2": sorted(int(r["replicate"]) for r in runs) == [0, 1, 2],
        "top_level_source_stable": raw["locked_inputs"] == raw["post_run_inputs"],
        "worker_locks_stable": all(r["worker_started_inputs"] == raw["locked_inputs"]
                                    == r["worker_finished_inputs"] for r in runs),
        "two_prompts_per_worker": all(len(r["turns"]) == 2 for r in runs),
        "first_prompt_is_resolved_self_report": all(
            t["route"] == "self_report" and t["goal_count"] == 1 and t["reply_nonempty"]
            and t["goal"] is not None and t["goal"]["origin_linked"]
            and t["goal"]["self_target"] == "self_organisation"
            and t["goal"]["status"] == "resolved"
            and t["goal"]["event_kinds"] == ["selection", "execution", "action_result"]
            and t["goal"]["all_transitions_bound"] and t["goal"]["closed"] and not t["goal"]["active"]
            for r in runs for t in r["turns"] if t["turn"] == 0),
        "second_prompt_shortfall_reproduces": all(
            t["route"] is None and t["goal_count"] == 0 and t["reply_nonempty"]
            and not t["lifecycle_event_kinds"]
            for r in runs for t in r["turns"] if t["turn"] == 1),
    }
    task_repro = {}
    turn_profiles = {}
    for turn_index in (0, 1):
        ts = [r["turns"][turn_index] for r in runs]
        task_repro[str(turn_index)] = {
            "semantic_graph_signature_repeats": len({(t["semantic_graph_sha256"], t["node_count"], t["edge_count"])
                                                        for t in ts}) == 1,
            "reply_repeats": len({t["reply"] for t in ts}) == 1,
        }
        per_run = []
        for run, turn in zip(runs, ts):
            work = reconcile_work(turn)
            matcher = reconcile_matcher(turn)
            per_run.append({"replicate": run["replicate"], "work": work,
                            "matcher_and_term": matcher,
                            "task_work": {k: turn["scale_counters"].get(k, 0) for k in (
                                "cand_tested", "cand_enum_total", "where_evals", "term_evals_total",
                                "term_evals_unattributed", "scheduler_passes", "scheduler_selected_rules")}})
        turn_profiles[str(turn_index)] = per_run
        checks[f"turn_{turn_index}_graph_and_reply_replicate"] = all(task_repro[str(turn_index)].values())
        checks[f"turn_{turn_index}_work_reconciles"] = all(x["work"]["pass"] for x in per_run)
        checks[f"turn_{turn_index}_matcher_term_reconciles"] = all(
            all(x["matcher_and_term"]["checks"].values()) for x in per_run)
    checks["all_gates_pass"] = all(checks.values())
    result = {
        "schema_version": 1,
        "claim_boundary": "One source-locked live self-report task family, with a successful route and a separate route-shortfall prompt. Work and matcher accounting do not establish natural prevalence, complete access recall, or scaling.",
        "checks": checks, "task_reproducibility": task_repro,
        "per_turn_work_profiles": turn_profiles,
        "all_checks_pass": all(checks.values()),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks,
                      "work_rows_by_turn": {k: [p["work"]["work_row_count"] for p in v]
                                            for k, v in turn_profiles.items()},
                      "all_checks_pass": result["all_checks_pass"], "output": str(OUT)}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("self-report operation-work accounting failed")


if __name__ == "__main__":
    main()
