#!/usr/bin/env python3
"""Independent integrity and frozen task-oracle analysis for authored panel v1."""
from __future__ import annotations
import hashlib, json, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/independent_authored_anaphora_panel_v1_raw_20260929.json"
OUT = ROOT / "evaluation/reports/independent_authored_anaphora_panel_v1_analysis_20260929.json"
SUITE_PATH = ROOT / "evaluation/substrate_capability/anaphora_independent_task_suite_v1.json"
SUITE = json.loads(SUITE_PATH.read_text())["cases"]
EXPECTED = {row["case_id"]: row for row in SUITE}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def analyze(raw):
    runs = raw["runs"]
    expected_ids = list(EXPECTED)
    rows = [r for r in runs if "worker_error" not in r]
    process_ids = [r.get("worker", {}).get("pid") for r in rows]
    checks = {
        "ten_worker_rows": len(runs) == 10 and len(rows) == 10,
        "ten_distinct_processes": len(set(process_ids)) == 10,
        "all_case_sets_complete_and_ordered": all(
            [c["case_id"] for c in r["worker"]["cases"]] == expected_ids for r in rows),
        "pre_post_fingerprints_stable": all(r.get("before") == r.get("after") == raw["locked_inputs"] for r in rows),
        "capture_lock_stable": raw.get("post_run_inputs") == raw.get("locked_inputs"),
        "turn_counts_match_suite": all(
            len(c["turns"]) == len(EXPECTED[c["case_id"]]["turns"])
            for r in rows for c in r["worker"]["cases"]),
        "turn_texts_match_suite": all(
            [t["text"] for t in c["turns"]] == EXPECTED[c["case_id"]]["turns"]
            for r in rows for c in r["worker"]["cases"]),
        "exact_referent_and_intent_oracles": all(
            c["projection"]["pronoun_count"] == 1
            and c["projection"]["referent_names"] ==
                ([EXPECTED[c["case_id"]]["expected_referent"]]
                 if EXPECTED[c["case_id"]]["expected_referent"] else [])
            and (EXPECTED[c["case_id"]]["expected_intent_about"] is None or
                 ((c["projection"]["intent_exists"] is True
                   and EXPECTED[c["case_id"]]["expected_referent"] in c["projection"]["intent_about_names"])
                  == EXPECTED[c["case_id"]]["expected_intent_about"]))
            for r in rows for c in r["worker"]["cases"]),
        "per_case_graphs_repeat": all(
            len({c["graph_digest"] for r in rows for c in r["worker"]["cases"]
                 if c["case_id"] == case_id}) == 1 for case_id in expected_ids),
        "resource_counters_nonnegative": all(
            r["worker"]["worker_wall_ns"] > 0 and r["worker"]["worker_cpu_ns"] > 0
            and r["worker"]["peak_rss_kib"] > 0
            and all(t[k] >= 0 for c in r["worker"]["cases"] for t in c["turns"]
                    for k in ("receive_wall_ns", "receive_cpu_ns", "comprehend_wall_ns", "comprehend_cpu_ns"))
            for r in rows),
        "adapter_boot_separately_timed": all(
            c["default_adapter_init_wall_ns"] > 0 and c["default_adapter_init_cpu_ns"] > 0
            for r in rows for c in r["worker"]["cases"]),
        "case_time_contains_boot_and_turns": all(
            c["adapter_and_case_wall_ns"] >= c["default_adapter_init_wall_ns"]
            + sum(t["receive_wall_ns"] + t["comprehend_wall_ns"] for t in c["turns"])
            for r in rows for c in r["worker"]["cases"]),
    }
    case_summary = {}
    for case_id in expected_ids:
        case_rows = [c for r in rows for c in r["worker"]["cases"] if c["case_id"] == case_id]
        task_wall = [sum(t["receive_wall_ns"] + t["comprehend_wall_ns"] for t in c["turns"]) / 1e6 for c in case_rows]
        task_cpu = [sum(t["receive_cpu_ns"] + t["comprehend_cpu_ns"] for t in c["turns"]) / 1e6 for c in case_rows]
        boot_wall = [c["default_adapter_init_wall_ns"] / 1e6 for c in case_rows]
        boot_cpu = [c["default_adapter_init_cpu_ns"] / 1e6 for c in case_rows]
        case_summary[case_id] = {
            "n": len(case_rows), "oracle_passes": sum(
                c["projection"]["pronoun_count"] == 1
                and c["projection"]["referent_names"] ==
                    ([EXPECTED[case_id]["expected_referent"]]
                     if EXPECTED[case_id]["expected_referent"] else [])
                and (EXPECTED[case_id]["expected_intent_about"] is None or
                     ((c["projection"]["intent_exists"] is True
                       and EXPECTED[case_id]["expected_referent"] in c["projection"]["intent_about_names"])
                      == EXPECTED[case_id]["expected_intent_about"]))
                for c in case_rows),
            "median_turn_operation_wall_ms": round(statistics.median(task_wall), 4) if task_wall else None,
            "median_turn_operation_cpu_ms": round(statistics.median(task_cpu), 4) if task_cpu else None,
            "median_default_adapter_init_wall_ms": round(statistics.median(boot_wall), 4) if boot_wall else None,
            "median_default_adapter_init_cpu_ms": round(statistics.median(boot_cpu), 4) if boot_cpu else None,
            "graph_nodes": case_rows[0]["graph_nodes"] if case_rows else None,
            "graph_edges": case_rows[0]["graph_edges"] if case_rows else None,
        }
    worker_walls = [r["worker"]["worker_wall_ns"] / 1e6 for r in rows]
    worker_cpus = [r["worker"]["worker_cpu_ns"] / 1e6 for r in rows]
    rss = [r["worker"]["peak_rss_kib"] for r in rows]
    payload = {"schema_version": 1, "run_id": "independent-authored-anaphora-panel-v1-20260929",
               "raw_sha256": sha(RAW), "checks": checks,
               "summary": {"cases": case_summary,
                           "worker_median_wall_ms": round(statistics.median(worker_walls), 3) if worker_walls else None,
                           "worker_median_cpu_ms": round(statistics.median(worker_cpus), 3) if worker_cpus else None,
                           "peak_rss_kib_median": int(statistics.median(rss)) if rss else None},
               "task_suite_sha256": sha(SUITE_PATH),
               "claim_boundary": "Eleven assistant-authored cases through the default production ingestion path; no human-authored or natural-task prevalence/general-language estimate."}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks, "summary": payload["summary"]}, indent=2))
    return all(checks.values())

if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW
    raw = json.loads(source.read_text())
    if source != RAW:
        # Analysis can target an explicitly versioned raw capture but its digest is reported.
        RAW = source
    raise SystemExit(0 if analyze(raw) else 1)
