#!/usr/bin/env python3
"""Independent analysis for the live describe_scene Percept × noise factorial."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/live_describe_scene_percept_noise_factorial_v1_1_workers_raw_20260929.json"
DRIVER = ROOT / "evaluation/reports/live_describe_scene_percept_noise_factorial_v1_1_20260929.json"
LOCK = ROOT / "evaluation/substrate_capability/live_describe_scene_percept_noise_factorial_v1_1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/live_describe_scene_percept_noise_factorial_v1_1_analysis_20260929.json"
PERCEPTS = (3, 6, 12, 24)
NOISE = (0, 1024, 4096)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_work(row: dict) -> dict:
    scale = row["scale"]
    cand = int(scale.get("cand_tested", 0)); cand_un = int(scale.get("cand_tested_unattributed", 0))
    terms = int(scale.get("term_evals_total", 0)); terms_un = int(scale.get("term_evals_unattributed", 0))
    metadata = {int(i): {"name": name, "arity": int(arity), "ambiguous": bool(amb)}
                for i, sym, name, arity, amb in row["metadata"]}
    per = Counter(); per_term = 0; clauses = Counter(); missing = set(); bad = []
    for i, metric, value in row["per_rule"]:
        i = int(i); value = int(value)
        if i not in metadata: missing.add(i)
        if metric == "candidate_tests": per[i] += value
        elif metric == "term_evaluations": per_term += value
    for i, pos, value in row["per_clause"]:
        i = int(i); pos = int(pos); value = int(value)
        if i not in metadata: missing.add(i)
        elif pos >= metadata[i]["arity"]: bad.append((i, pos, value))
        else: clauses[i] += value
    ambiguous = {i for i, m in metadata.items() if m["ambiguous"]}
    ambiguous_rows = [x for x in row["per_rule"] if int(x[0]) in ambiguous]
    term_kinds = sum(int(v) for k, v in scale.items() if k.startswith("term_eval:"))
    return {"candidate_tests": cand, "candidate_unattributed": cand_un,
            "candidate_attributed": sum(per.values()), "per_clause_candidates": sum(clauses.values()),
            "term_evaluations": terms, "term_attributed": per_term, "term_unattributed": terms_un,
            "term_kind_evaluations": term_kinds, "ambiguous_rule_count": len(ambiguous),
            "ambiguous_rule_rows": len(ambiguous_rows), "metadata_missing_ids": sorted(missing),
            "bad_clauses": bad, "per_rule_candidates": {str(i): v for i, v in sorted(per.items())},
            "operation_work_units": int(row["operation_work"]["units"]),
            "operation_work_by_kind": dict(sorted(Counter(row["operation_work"]["by_kind"]).items())),
            "operation_work_by_rule_uid": row["operation_work"]["by_rule_uid"],
            "operation_count": len({x["operation_id"] for x in row["operation_work"]["rows"]}),
            "trace_events": int(row["trace_event_count"]), "trace_rows": len(row["trace_rows"]),
            "wall_ns": int(row["request_wall_ns"]), "cpu_ns": int(row["request_process_cpu_ns"]),
            "peak_rss_bytes": int(row["peak_rss_bytes"]), "graph_nodes": int(row["graph_node_count"]),
            "graph_edges": int(row["graph_edge_count"]), "graph_digest": row["semantic_graph_sha256"]}


def fit_finite_model(cells: list[dict], metric: str) -> dict:
    """Least-squares fit β0 + βP(P-3) + βD D + βPD(P-3)D; retain cell residuals."""
    import numpy as np
    x = np.array([[1.0, float(c["percept_count"] - 3), float(c["noise_count"]),
                   float((c["percept_count"] - 3) * c["noise_count"])] for c in cells])
    y = np.array([float(c[metric]) for c in cells])
    beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    predicted = x @ beta
    return {"metric": metric, "coefficients": {k: float(v) for k, v in zip(("intercept", "percept_delta", "noise_count", "interaction"), beta)},
            "design_rank": int(rank), "rmse": float(np.sqrt(np.mean((y-predicted)**2))),
            "residual_by_cell": [{"percept_count": c["percept_count"], "noise_count": c["noise_count"],
                                  "observed": float(yi), "predicted": float(pi), "residual": float(yi-pi)}
                                 for c, yi, pi in zip(cells, y, predicted)]}


def main() -> int:
    raw = json.loads(RAW.read_text()); driver = json.loads(DRIVER.read_text())
    locked = json.loads(LOCK.read_text())["locked_inputs"]; runs = raw["runs"]
    groups = {(p, d, rep): {r["arm"]: r for r in runs
                            if r["percept_count"] == p and r["noise_count"] == d and r["replicate"] == rep}
              for p in PERCEPTS for d in NOISE for rep in range(2)}
    checks = {
        "forty_eight_unique_workers": len(runs) == 48 and len({r["pid"] for r in runs}) == 48,
        "complete_factorial": all(set(g) == {"audited", "untraced"} for g in groups.values()),
        "source_stable": raw["locked_inputs"] == locked and driver["locked_inputs"] == locked
            and driver["post_run_inputs"] == locked
            and all(r["worker_started_inputs"] == r["worker_finished_inputs"] == locked for r in runs),
        "semantic_scene_goal_and_reply_oracles": all(
            r["scene_percepts"] == r["percept_count"] and r["request_scene_view_count"] == 1
            and r["request_view_percept_count"] == r["percept_count"] and r["request_view_classification_exact"]
            and r["reply_semantic_coverage"] and r["route"] == "describe_scene" and r["goal_count"] == 1
            and r["goal"] is not None and r["goal"]["status"] == "resolved"
            and r["goal"]["transition_kinds"] == ["selection", "execution", "action_result"]
            and r["goal"]["closed"] and not r["goal"]["active"] for r in runs),
        "noise_factor_isolated_and_unclassified": all(
            r["noise_count"] == r["noise_concept_count"] == r["noise_membership_count"]
            and r["noise_count"] in NOISE and r["noise_classified_edges"] == 0 for r in runs),
        "audited_control_semantic_parity": all(
            g["audited"]["reply"] == g["untraced"]["reply"]
            and g["audited"]["goal"] == g["untraced"]["goal"]
            and g["audited"]["semantic_graph_sha256"] == g["untraced"]["semantic_graph_sha256"]
            and (g["audited"]["graph_node_count"], g["audited"]["graph_edge_count"])
                == (g["untraced"]["graph_node_count"], g["untraced"]["graph_edge_count"])
            and g["audited"]["request_view_classifications"] == g["untraced"]["request_view_classifications"]
            for g in groups.values()),
        "constant_base_graph_population": len({r["base_concepts_before_noise"] for r in runs}) == 1
            and len({r["base_memberships_before_noise"] - r["percept_count"] for r in runs}) == 1,
        "untraced_streams_empty": all(not r["scale"] and not r["per_rule"] and not r["per_clause"]
            and not r["metadata"] and not r["trace_rows"] and r["trace_event_count"] == 0
            and not r["operation_work"]["rows"] and r["operation_work"]["units"] == 0
            for r in runs if r["arm"] == "untraced"),
        "audited_access_and_work_streams_complete": all(r["trace_dropped"] == 0
            and r["trace_event_count"] == sum(x["count"] for x in r["trace_rows"])
            and r["operation_work"]["dropped"] == 0
            and r["operation_work"]["units"] == sum(x["work_units"] for x in r["operation_work"]["rows"])
            for r in runs if r["arm"] == "audited"),
    }
    audited = [r for r in runs if r["arm"] == "audited"]
    records = [{**audit_work(r), "percept_count": r["percept_count"], "noise_count": r["noise_count"],
                "replicate": r["replicate"], "reply": r["reply"],
                "reply_matches_exact_baseline": r["reply_matches_expected"],
                "reply_semantic_coverage": r["reply_semantic_coverage"],
                "request_view_classifications": r["request_view_classifications"],
                "request_view_classification_exact": r["request_view_classification_exact"],
                "noise_classified_edges": r["noise_classified_edges"]} for r in audited]
    checks["candidate_term_and_match_attribution_conserves"] = all(
        x["candidate_tests"] == x["candidate_unattributed"] + x["candidate_attributed"]
        and x["candidate_attributed"] == x["per_clause_candidates"]
        and x["term_evaluations"] == x["term_attributed"] + x["term_unattributed"] == x["term_kind_evaluations"]
        for x in records)
    checks["rule_ids_and_clause_indices_valid"] = all(x["ambiguous_rule_rows"] == 0
        and not x["metadata_missing_ids"] and not x["bad_clauses"] for x in records)
    def signature(x):
        return (x["candidate_tests"], x["candidate_unattributed"], x["candidate_attributed"],
                x["term_evaluations"], x["term_unattributed"], x["term_attributed"],
                x["operation_work_units"], tuple(sorted(x["operation_work_by_kind"].items())),
                x["trace_events"], tuple(sorted(x["per_rule_candidates"].items())))
    checks["audited_profiles_repeat_within_cells"] = all(
        len({signature(x) for x in records if (x["percept_count"], x["noise_count"]) == (p, d)}) == 1
        for p in PERCEPTS for d in NOISE)
    checks["semantic_graph_repeats_within_cells"] = all(
        len({(x["graph_digest"], x["graph_nodes"], x["graph_edges"])
             for x in records if (x["percept_count"], x["noise_count"]) == (p, d)}) == 1
        for p in PERCEPTS for d in NOISE)

    cells = []
    for p in PERCEPTS:
        for d in NOISE:
            xs = [x for x in records if (x["percept_count"], x["noise_count"]) == (p, d)]
            by_arm = {arm: [r for r in runs if (r["percept_count"], r["noise_count"], r["arm"]) == (p, d, arm)]
                      for arm in ("audited", "untraced")}
            representative = xs[0]
            cells.append({"percept_count": p, "noise_count": d,
                "candidate_tests": representative["candidate_tests"],
                "candidate_attributed": representative["candidate_attributed"],
                "candidate_unattributed": representative["candidate_unattributed"],
                "term_evaluations": representative["term_evaluations"],
                "term_attributed": representative["term_attributed"],
                "term_unattributed": representative["term_unattributed"],
                "operation_count": representative["operation_count"],
                "operation_work_units": representative["operation_work_units"],
                "operation_work_by_kind": representative["operation_work_by_kind"],
                "selected_access_events": representative["trace_events"],
                "graph_nodes": representative["graph_nodes"], "graph_edges": representative["graph_edges"],
                "graph_digest": representative["graph_digest"],
                "request_wall_ns_median": {a: statistics.median(r["request_wall_ns"] for r in rows) for a, rows in by_arm.items()},
                "request_cpu_ns_median": {a: statistics.median(r["request_process_cpu_ns"] for r in rows) for a, rows in by_arm.items()},
                "peak_rss_bytes_median": {a: statistics.median(r["peak_rss_bytes"] for r in rows) for a, rows in by_arm.items()},
                "exact_baseline_reply_all_repeats": all(x["reply_matches_exact_baseline"] for x in xs),
                "semantic_reply_coverage": all(x["reply_semantic_coverage"] for x in xs),
                "request_view_classification_exact": all(x["request_view_classification_exact"] for x in xs),
                "outbound_message_alignment_all_repeats": all(r["outbound_message_alignment"] for r in by_arm["audited"])})
    model_fits = {metric: fit_finite_model(cells, metric) for metric in
                  ("candidate_tests", "term_evaluations", "selected_access_events")}
    per_rule = []
    for p in PERCEPTS:
        for d in NOISE:
            r = next(r for r in audited if (r["percept_count"], r["noise_count"]) == (p, d))
            cv = Counter(); tv = Counter()
            for i, metric, value in r["per_rule"]:
                (cv if metric == "candidate_tests" else tv if metric == "term_evaluations" else Counter())[int(i)] += int(value)
            names = {int(i): name for i, sym, name, arity, amb in r["metadata"]}
            per_rule.append({"percept_count": p, "noise_count": d, "rules": [
                {"audit_id": i, "name": names.get(i), "candidate_tests": cv[i], "term_evaluations": tv[i]}
                for i in sorted(set(cv) | set(tv))]})
    payload = {"schema_version": 1, "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "driver_sha256": sha(DRIVER), "checks": checks, "all_checks_pass": all(checks.values()),
        "summary_by_factor_cell": cells, "audited_worker_profiles": records,
        "per_rule_work_by_factor_cell": per_rule, "finite_factor_model": model_fits,
        "claim_boundary": "Source-locked full-seed live describe_scene route with repeated known Percepts and 0/1,024/4,096 synthetic noise Concepts. Finite factorial measurements only; not an asymptotic complexity result, natural workload prevalence, novelty learning, learned frame locality, scoped execution, or general capability."}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks, "all_checks_pass": payload["all_checks_pass"],
                      "summary_by_factor_cell": cells, "finite_factor_model": model_fits}, indent=2))
    return 0 if payload["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
