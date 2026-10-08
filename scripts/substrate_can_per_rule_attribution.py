#!/usr/bin/env python3
"""Collect opt-in per-rule CAN work counters in fresh paired processes."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKLOAD = ROOT / "scripts/substrate_can_structure_envelope.py"
OUT = ROOT / "evaluation/reports/substrate_can_per_rule_attribution_20260924.json"
SIZES = (32, 128)
TOPOLOGIES = ("path", "banded2", "complete")
MODES = ("2state", "3state")
REPLICATES = 3


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    inherited = os.environ.copy()
    rows = []
    start = time.perf_counter()
    for n in SIZES:
        for topology in TOPOLOGIES:
            for mode in MODES:
                for replicate in range(REPLICATES):
                    fd, tmp_name = tempfile.mkstemp(prefix="can-per-rule-", suffix=".json")
                    os.close(fd)
                    tmp_path = Path(tmp_name)
                    env = {
                        **inherited,
                        "SUBSTRATE_CAN_OUT": str(tmp_path),
                        "SUBSTRATE_CAN_SIZES": str(n),
                        "SUBSTRATE_CAN_TOPOLOGIES": topology,
                        "SUBSTRATE_CAN_MODES": mode,
                        "SUBSTRATE_CAN_GRANULARITIES": "0.25",
                        "SUBSTRATE_CAN_REPLICATES": "1",
                        "SUBSTRATE_CAN_SKIP_AUDIT": "0",
                        "SUBSTRATE_CAN_PER_RULE_AUDIT": "1",
                    }
                    cmd = [sys.executable, str(WORKLOAD)]
                    proc = subprocess.run(cmd, cwd=ROOT, env=env, text=True,
                                          capture_output=True, timeout=120)
                    if proc.returncode != 0:
                        raise RuntimeError(f"failed {n}/{topology}/{mode}/{replicate}: {proc.stderr}\n{proc.stdout}")
                    run = json.loads(tmp_path.read_text())
                    tmp_path.unlink(missing_ok=True)
                    draw = run["draws"][0]
                    if not draw["audit_state_matches_uninstrumented"] or draw["audit_progress_count"] != draw["progress_count"]:
                        raise RuntimeError("per-rule instrumentation changed workload outcome")
                    per_rule_totals = {}
                    for item in draw["audit_per_rule_counters"]:
                        per_rule_totals[item["metric"]] = per_rule_totals.get(item["metric"], 0) + item["count"]
                    conservation = {
                        "candidate_pairs": "cand_enum", "candidate_tests": "cand_tested",
                        "where_evaluations": "where_evals", "where_rejections": "where_rejects",
                        "pushdown_evaluations": "pushdown_evals", "pushdown_prunes": "pushdown_prunes",
                        "binding_leaves": "leaf_visits", "binding_clones": "bindings_cloned",
                        "term_evaluations": "term_evals_total", "term_units": "term_units_total",
                        "effect_edge_insert_attempts": "rule_effect_edge_insert_attempts",
                        "effect_edge_deletes": "rule_effect_edge_deletes",
                        "effect_node_inserts": "rule_effect_node_inserts",
                        "effect_node_delete_attempts": "rule_effect_node_delete_attempts",
                        "effect_attr_set_attempts": "rule_effect_attr_set_attempts",
                        "effect_replace_edge_deletes": "rule_effect_replace_edge_deletes",
                        "effect_replace_edge_insert_attempts": "rule_effect_replace_edge_insert_attempts",
                        "rule_enumerations": "rule_enumerations",
                    }
                    mismatches = {per_rule: (per_rule_totals.get(per_rule, 0), draw["audit_counters"].get(global_key, 0))
                    for per_rule, global_key in conservation.items()
                                  if per_rule_totals.get(per_rule, 0) != draw["audit_counters"].get(global_key, 0)}
                    fixed_metric_names = set(conservation)
                    for variant, total in per_rule_totals.items():
                        if variant in fixed_metric_names:
                            continue
                        global_total = draw["audit_term_eval_by_variant"].get(variant, 0)
                        if total != global_total:
                            mismatches["term_variant:" + variant] = (total, global_total)
                    if mismatches:
                        raise RuntimeError(f"per-rule/global counter conservation failed: {mismatches}")
                    rows.append({
                        "n": n, "topology": topology, "mode": mode,
                        "replicate": replicate, "seed": draw["seed"],
                        "progress_count": draw["progress_count"],
                        "wall_time_ns_uninstrumented": draw["wall_time_ns"],
                        "wall_time_ns_with_per_rule_audit": draw["audit_wall_time_ns"],
                        "cpu_time_ns_with_per_rule_audit": draw["audit_cpu_time_ns"],
                        "audit_state_matches_uninstrumented": draw["audit_state_matches_uninstrumented"],
                        "per_rule_counter_conservation": True,
                        "audit_counters": draw["audit_counters"],
                        "audit_term_eval_by_variant": draw["audit_term_eval_by_variant"],
                        "audit_term_units_by_variant": draw["audit_term_units_by_variant"],
                        "per_rule_counters": draw["audit_per_rule_counters"],
                        "native_extension_sha256": run["provenance"]["native_extension_sha256"],
                        "worker_command": cmd,
                    })
                    print(f"finished n={n} {topology} {mode} {replicate + 1}/{REPLICATES} "
                          f"candidates={draw['audit_counters']['cand_enum']}", flush=True)

    summaries = []
    for n in SIZES:
        for topology in TOPOLOGIES:
            for mode in MODES:
                group = [r for r in rows if (r["n"], r["topology"], r["mode"]) == (n, topology, mode)]
                counters = sorted({(x["rule_name"], x["metric"])
                                   for r in group for x in r["per_rule_counters"]})
                per_rule = []
                for name, metric in counters:
                    vals = [next((x["count"] for x in r["per_rule_counters"]
                                  if x["rule_name"] == name and x["metric"] == metric), 0)
                            for r in group]
                    per_rule.append({"rule_name": name, "metric": metric,
                                     "median_count": statistics.median(vals), "replicate_counts": vals})
                summaries.append({
                    "n": n, "topology": topology, "mode": mode,
                    "replicates": len(group),
                    "all_instrumented_states_match": all(r["audit_state_matches_uninstrumented"] for r in group),
                    "all_counters_conserve": all(r["per_rule_counter_conservation"] for r in group),
                    "median_wall_time_ns_uninstrumented": int(statistics.median(r["wall_time_ns_uninstrumented"] for r in group)),
                    "median_wall_time_ns_with_per_rule_audit": int(statistics.median(r["wall_time_ns_with_per_rule_audit"] for r in group)),
                    "median_cpu_time_ns_with_per_rule_audit": int(statistics.median(r["cpu_time_ns_with_per_rule_audit"] for r in group)),
                    "median_global_candidate_pairs": int(statistics.median(r["audit_counters"]["cand_enum"] for r in group)),
                    "per_rule": per_rule,
                })
    payload = {
        "run_id": "substrate-can-per-rule-attribution-20260924",
        "scope": "CAN rule-level candidate, where, binding, and effect attempts under opt-in native audit",
        "configuration": {"sizes": SIZES, "topologies": TOPOLOGIES, "modes": MODES,
                          "weight_granularity": 0.25, "replicates": REPLICATES,
                          "audited_and_uninstrumented_runs": "fresh paired graphs; graph and progress parity required"},
        "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                    "elapsed_seconds": time.perf_counter() - start},
        "provenance": {"orchestrator_sha256": sha(Path(__file__).resolve()),
                       "workload_sha256": sha(WORKLOAD),
                       "scale_audit_source_sha256": sha(ROOT / "runners/dsl/src/scale_audit.rs"),
                       "term_source_sha256": sha(ROOT / "runners/dsl/src/term.rs"),
                       "substrate_source_sha256": sha(ROOT / "runners/dsl/src/substrate.rs"),
                       "pyo3_source_sha256": sha(ROOT / "runners/dsl/src/py.rs"),
                       "seed_manifest_sha256": sha(ROOT / "seeds/can_native_reimplementation.json"),
                       "native_extension_sha256": rows[0]["native_extension_sha256"] if rows else None,
                       "command": "PYTHONPATH=<temporary-native-package>:$PWD python3 scripts/substrate_can_per_rule_attribution.py",
                       "pythonpath": inherited.get("PYTHONPATH", ""), "cwd": str(ROOT)},
        "summaries": summaries, "workers": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(rows), "groups": len(summaries),
                      "all_match": all(s["all_instrumented_states_match"] for s in summaries),
                      "all_counters_conserve": all(s["all_counters_conserve"] for s in summaries),
                      "output": str(OUT)}, indent=2))
    if not all(s["all_instrumented_states_match"] and s["all_counters_conserve"] for s in summaries):
        raise SystemExit("instrumented outcome mismatch")


if __name__ == "__main__":
    main()
