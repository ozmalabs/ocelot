#!/usr/bin/env python3
"""Measure authored CAN asynchronous updates across graph structure.

The oracle is an independently coded local fixed-point predicate evaluated
from generated fields, weights, and native final states. It intentionally does
not require a particular basin: asynchronous update order can select among
multiple stable states.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import random
import resource
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_FILE = ROOT / "seeds/can_native_reimplementation.json"
OUT = Path(os.environ.get("SUBSTRATE_CAN_OUT", ROOT / "evaluation/reports/substrate_can_structure_envelope_20260924.json"))
SIZES = tuple(int(x) for x in os.environ.get("SUBSTRATE_CAN_SIZES", "8,16,32").split(","))
TOPOLOGIES = tuple(os.environ.get("SUBSTRATE_CAN_TOPOLOGIES", "path,banded2,complete").split(","))
MODES = tuple(os.environ.get("SUBSTRATE_CAN_MODES", "2state,3state").split(","))
GRANULARITIES = tuple(float(x) for x in os.environ.get("SUBSTRATE_CAN_GRANULARITIES", "1.0,0.25").split(","))
REPLICATES = int(os.environ.get("SUBSTRATE_CAN_REPLICATES", "5"))
FRAME_SIZE = 4
BETA = 2.0
THRESHOLD = math.atanh(0.5)
SKIP_AUDIT = os.environ.get("SUBSTRATE_CAN_SKIP_AUDIT", "0") == "1"
PER_RULE_AUDIT = os.environ.get("SUBSTRATE_CAN_PER_RULE_AUDIT", "0") == "1"


def rss_highwater_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_pairs(n: int, topology: str):
    for a in range(n):
        for b in range(a + 1, n):
            if topology == "complete" or (topology == "path" and b == a + 1) or (
                topology == "banded2" and b - a <= 2
            ):
                yield a, b


def update(mode: str, h: float) -> float:
    if mode == "2state":
        return 1.0 if h >= 0.0 else -1.0
    scaled = BETA * h
    if scaled > THRESHOLD:
        return 1.0
    if scaled < -THRESHOLD:
        return -1.0
    return 0.0


def build_engine(sr, engine_rules_only, seed_doc, n, mode, fields, weights):
    substrate = sr.Substrate()
    inner = substrate._inner
    inner.load_seed_manifest(engine_rules_only(seed_doc))
    mt = inner.add_node("Microtheory", {
        "temperature": BETA, "discrete_mode": mode, "can_tick": 0,
    })
    concepts = [inner.add_node("Concept", {
        "name": f"c{i}", "state": 0.0,
        "external_field": fields[i], "identity_field": 0.0,
    }) for i in range(n)]
    for concept in concepts:
        inner.add_edge(mt, "has_concept", concept, {})
    for (a, b), weight in weights.items():
        inner.add_edge(concepts[a], "causal_influence", concepts[b], {"weight": weight})
    return inner, concepts


def main() -> None:
    import substrate_rs as sr
    from substrate.seed_loader import engine_rules_only

    from substrate_rs import _native

    seed_doc = json.loads(SEED_FILE.read_text())
    rss_after_import_kib = rss_highwater_kib()
    records = []
    for n in SIZES:
        for topology in TOPOLOGIES:
            for mode in MODES:
                for granularity in GRANULARITIES:
                    for replicate in range(REPLICATES):
                        draw_seed = 20260924 + n * 1000 + replicate
                        field_rng = random.Random(draw_seed * 53 + n)
                        pair_rng = random.Random(draw_seed * 31 + n)
                        fields = [field_rng.uniform(-1.0, 1.0) for _ in range(n)]
                        weights: dict[tuple[int, int], float] = {}
                        for a, b in make_pairs(n, topology):
                            raw = pair_rng.uniform(-1.0, 1.0)
                            weight = round(raw / granularity) * granularity
                            weights[a, b] = weight
                            weights[b, a] = weight

                        inner, concepts = build_engine(sr, engine_rules_only, seed_doc, n, mode, fields, weights)
                        rss_after_setup_kib = rss_highwater_kib()

                        wall0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
                        progress = inner.run_rules(100_000)
                        wall_ns = time.perf_counter_ns() - wall0
                        cpu_ns = time.process_time_ns() - cpu0
                        states = [float(inner.node(c)["attrs"].get("state", 0.0)) for c in concepts]
                        rss_after_run_kib = rss_highwater_kib()

                        # A fresh, identical substrate run with the native scale
                        # audit enabled attributes candidate and effect work without
                        # contaminating the uninstrumented timing above.
                        audit_counts = None
                        audit_per_rule_counts = None
                        audit_progress = None
                        audited_states = None
                        audit_wall_ns = None
                        audit_cpu_ns = None
                        if not SKIP_AUDIT:
                            audited, audited_concepts = build_engine(
                                sr, engine_rules_only, seed_doc, n, mode, fields, weights
                            )
                            audited.scale_audit_reset()
                            audited.scale_audit_set_enabled(True)
                            if PER_RULE_AUDIT:
                                audited.scale_audit_set_per_rule_enabled(True)
                            audit_wall0, audit_cpu0 = time.perf_counter_ns(), time.process_time_ns()
                            audit_progress = audited.run_rules(100_000)
                            audit_wall_ns = time.perf_counter_ns() - audit_wall0
                            audit_cpu_ns = time.process_time_ns() - audit_cpu0
                            audit_counts = dict(audited.scale_audit_snapshot())
                            if PER_RULE_AUDIT:
                                names = {int(row[0]): str(row[1]) for row in audited.rule_access_sets()}
                                audit_per_rule_counts = [
                                    {"rule_index": idx, "rule_name": names.get(idx, f"rule_{idx}"),
                                     "metric": metric, "count": count}
                                    for idx, metric, count in audited.scale_audit_per_rule_snapshot()
                                ]
                                audited.scale_audit_set_per_rule_enabled(False)
                            audited.scale_audit_set_enabled(False)
                            audited_states = [float(audited.node(c)["attrs"].get("state", 0.0))
                                              for c in audited_concepts]
                            if audited_states != states or audit_progress != progress:
                                raise RuntimeError("audited and uninstrumented CAN runs diverged")
                        residuals = []
                        for a, state in enumerate(states):
                            local_field = fields[a] + sum(
                                weights.get((a, b), 0.0) * states[b] for b in range(n)
                            )
                            residuals.append(update(mode, local_field) != state)
                        terminal = inner.run_rules(1)
                        vocab = {-1.0, 1.0} if mode == "2state" else {-1.0, 0.0, 1.0}
                        frame_cross_edges = sum(
                            1 for (a, b) in weights if a // FRAME_SIZE != b // FRAME_SIZE
                        )
                        records.append({
                            "n": n, "topology": topology, "mode": mode,
                            "weight_granularity": granularity, "replicate": replicate,
                            "seed": draw_seed, "nodes": n + 1,
                            "directed_coupling_edges": len(weights),
                            "frame_size": FRAME_SIZE,
                            "cross_frame_directed_edges": frame_cross_edges,
                            "max_degree": max((sum((a, b) in weights for b in range(n)) for a in range(n)), default=0),
                            "progress_count": progress,
                            "audit_progress_count": audit_progress,
                            "audit_wall_time_ns": audit_wall_ns,
                            "audit_cpu_time_ns": audit_cpu_ns,
                            "audit_counters": None if audit_counts is None else {
                                key: audit_counts.get(key, 0) for key in (
                                    "cand_enum", "cand_enum_local", "cand_enum_scan",
                                    "cand_tested", "where_evals", "where_rejects",
                                    "pushdown_evals", "pushdown_prunes", "leaf_visits", "bindings_cloned",
                                    "rule_enumerations",
                                    "term_evals_total", "term_units_total",
                                    "rule_effect_edge_insert_attempts", "rule_effect_edge_deletes",
                                    "rule_effect_node_inserts", "rule_effect_node_delete_attempts",
                                    "rule_effect_attr_set_attempts", "rule_effect_replace_edge_deletes",
                                    "rule_effect_replace_edge_insert_attempts",
                                )
                            },
                            "audit_term_eval_by_variant": None if audit_counts is None else {
                                key.removeprefix("term_eval:"): value
                                for key, value in audit_counts.items() if key.startswith("term_eval:")
                            },
                            "audit_term_units_by_variant": None if audit_counts is None else {
                                key.removeprefix("term_unit:"): value
                                for key, value in audit_counts.items() if key.startswith("term_unit:")
                            },
                            "audit_per_rule_counters": audit_per_rule_counts,
                            "audit_state_matches_uninstrumented": None if audited_states is None else audited_states == states,
                            "rss_after_import_highwater_kib": rss_after_import_kib,
                            "rss_after_setup_highwater_kib": rss_after_setup_kib,
                            "rss_after_run_highwater_kib": rss_after_run_kib,
                            "budget_not_reached": progress < 100_000,
                            "terminal_probe_count": terminal,
                            "vocabulary_valid": all(s in vocab for s in states),
                            "independent_fixed_point_residuals": sum(residuals),
                            "final_state": [int(s) for s in states],
                            "wall_time_ns": wall_ns, "cpu_time_ns": cpu_ns,
                        })

    summaries = []
    for n in SIZES:
        for topology in TOPOLOGIES:
            for mode in MODES:
                for granularity in GRANULARITIES:
                    group = [r for r in records if
                             (r["n"], r["topology"], r["mode"], r["weight_granularity"])
                             == (n, topology, mode, granularity)]
                    summaries.append({
                        "n": n, "topology": topology, "mode": mode,
                        "weight_granularity": granularity, "replicates": len(group),
                        "all_budget_complete": all(r["budget_not_reached"] for r in group),
                        "all_terminal_probes_zero": all(r["terminal_probe_count"] == 0 for r in group),
                        "all_vocab_valid": all(r["vocabulary_valid"] for r in group),
                        "all_reference_fixed_points": all(r["independent_fixed_point_residuals"] == 0 for r in group),
                        "median_directed_edges": int(statistics.median(r["directed_coupling_edges"] for r in group)),
                        "median_progress_count": statistics.median(r["progress_count"] for r in group),
                        "median_wall_time_ns": int(statistics.median(r["wall_time_ns"] for r in group)),
                        "median_cpu_time_ns": int(statistics.median(r["cpu_time_ns"] for r in group)),
                    })
    payload = {
        "run_id": "substrate-can-structure-envelope-20260924",
        "scope": "authored CAN discrete asynchronous update; size/topology/weight granularity envelope",
        "oracle": "independent Python local-update predicate on native final state; zero residual means a fixed point",
        "oracle_limit": "validates stationarity, not basin selection, global energy optimality, or application task quality",
        "instrumentation": "skipped" if SKIP_AUDIT else "existing native scale_audit counters collected in a separate identical run; final state and progress count checked equal to uninstrumented run",
        "configuration": {"sizes": SIZES, "topologies": TOPOLOGIES, "modes": MODES,
                          "weight_granularities": GRANULARITIES, "replicates": REPLICATES,
                          "frame_size": FRAME_SIZE, "beta": BETA,
                          "skip_audit": SKIP_AUDIT,
                          "per_rule_audit": PER_RULE_AUDIT},
        "provenance": {
            "benchmark_script_sha256": sha(Path(__file__).resolve()),
            "seed_manifest_sha256": sha(SEED_FILE),
            "native_extension": str(Path(_native.__file__).resolve()),
            "native_extension_sha256": sha(Path(_native.__file__).resolve()),
            "python": platform.python_version(), "platform": platform.platform(),
            "processor": platform.processor(),
            "cwd": str(ROOT), "pythonpath": os.environ.get("PYTHONPATH", ""),
            "command": "PYTHONPATH=<native-extension-parent>:$PWD python3 scripts/substrate_can_structure_envelope.py",
        },
        "summaries": summaries,
        "draws": records,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    checks = {k: all(row[k] for row in summaries) for k in
              ("all_budget_complete", "all_terminal_probes_zero", "all_vocab_valid", "all_reference_fixed_points")}
    if not SKIP_AUDIT:
        checks["all_audit_runs_match_uninstrumented"] = all(
            row["audit_state_matches_uninstrumented"] and row["audit_progress_count"] == row["progress_count"]
            for row in records
        )
        checks["candidate_counter_reconciles"] = all(
            row["audit_counters"]["cand_enum"] == row["audit_counters"]["cand_tested"]
            for row in records
        )
        checks["binding_counter_reconciles"] = all(
            row["audit_counters"]["leaf_visits"] == row["audit_counters"]["bindings_cloned"]
            for row in records
        )
    print(json.dumps({"draws": len(records), "summary_groups": len(summaries), "checks": checks}, indent=2))
    print(f"wrote {OUT}")
    if not all(checks.values()):
        raise SystemExit("one or more correctness/resource gates failed")


if __name__ == "__main__":
    main()
