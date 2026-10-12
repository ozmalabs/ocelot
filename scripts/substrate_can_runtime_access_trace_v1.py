#!/usr/bin/env python3
"""Paired partial access tracing on the authored native CAN workload."""
from __future__ import annotations

import hashlib
import json
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_can_runtime_access_trace_v1_20260925.json"
SIZES = (8, 16)
TOPOLOGIES = ("path", "complete")
REPLICATES = 2


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_input(can, n: int, topology: str, seed: int):
    field_rng = random.Random(seed * 53 + n)
    pair_rng = random.Random(seed * 31 + n)
    fields = [field_rng.uniform(-1.0, 1.0) for _ in range(n)]
    weights = {}
    for a, b in can.make_pairs(n, topology):
        weight = round(pair_rng.uniform(-1.0, 1.0) / 0.25) * 0.25
        weights[a, b] = weight
        weights[b, a] = weight
    return fields, weights


def run_arm(can, sr, engine_rules_only, seed_doc, n: int, topology: str, mode: str,
            seed: int, traced: bool, scale_enabled: bool | None = None) -> dict:
    from substrate_rs import _native

    fields, weights = make_input(can, n, topology, seed)
    inner, concepts = can.build_engine(sr, engine_rules_only, seed_doc, n, mode, fields, weights)
    inner.runtime_access_trace_set_enabled(False)
    inner.runtime_access_trace_reset()
    inner.runtime_access_trace_set_enabled(traced)
    if scale_enabled is None:
        scale_enabled = traced
    inner.scale_audit_reset()
    inner.scale_audit_per_rule_reset()
    inner.scale_audit_set_enabled(scale_enabled)
    inner.scale_audit_set_per_rule_enabled(scale_enabled)
    wall_start, cpu_start = time.perf_counter_ns(), time.process_time_ns()
    progress = int(inner.run_rules(100_000))
    wall_ns, cpu_ns = time.perf_counter_ns() - wall_start, time.process_time_ns() - cpu_start
    states = [float(inner.node(node)["attrs"].get("state", 0.0)) for node in concepts]
    terminal = int(inner.run_rules(1))
    rows, dropped = inner.runtime_access_trace_snapshot()
    inner.runtime_access_trace_set_enabled(False)
    scale_counters = dict(inner.scale_audit_snapshot()) if scale_enabled else {}
    per_rule_raw = inner.scale_audit_per_rule_snapshot() if scale_enabled else []
    inner.scale_audit_set_per_rule_enabled(False)
    inner.scale_audit_set_enabled(False)
    residuals = []
    for a, state in enumerate(states):
        local_field = fields[a] + sum(weights.get((a, b), 0.0) * states[b] for b in range(n))
        residuals.append(can.update(mode, local_field) != state)

    rules = inner.rule_access_sets()
    uid_to_static = {}
    uid_to_index = {}
    exported_rules = inner.export_rules()
    for index, name, active, reads, term_edges, writes, reads_any, writes_any in rules:
        uid = int(inner.rule_metadata(index)["rule_uid"])
        uid_to_index[uid] = int(index)
        uid_to_static[uid] = {
            "name": name, "reads": set(reads) | set(term_edges), "writes": set(writes),
            "reads_any": bool(reads_any), "writes_any": bool(writes_any),
            "match_edge_count": len(exported_rules[index]["match"]),
        }
    per_rule_metrics = {}
    for index, metric, count in per_rule_raw:
        uid = next((uid for uid, rule_index in uid_to_index.items() if rule_index == int(index)), None)
        if uid is not None:
            per_rule_metrics.setdefault(uid, {})[str(metric)] = int(count)

    observed = []
    mismatches = []
    for uid, kind, node, resource, peer, count in rows:
        static = uid_to_static.get(int(uid))
        row = {"rule_uid": int(uid), "rule_name": static["name"] if static else None,
               "kind": kind, "node": node, "resource": resource, "peer": peer, "count": int(count)}
        observed.append(row)
        key = None
        direction = None
        if kind in ("pattern_edge", "term_edge_read"):
            key, direction = f"edge:{resource}", "read"
        elif kind in ("term_attr_read", "jit_attr_read"):
            key, direction = f"attr:{resource}", "read"
        elif kind == "jit_type_read":
            key, direction = f"type:{resource}", "read"
        elif kind == "term_type_read":
            key, direction = f"type:{resource}", "read"
        elif kind in ("term_index_query", "term_edge_attr_read"):
            key, direction = f"attr:{resource}", "read"
        elif kind in ("effect_attr_write",):
            key, direction = f"attr:{resource}", "write"
        elif kind in ("effect_edge_upsert", "effect_edge_delete", "effect_replace_edge"):
            key, direction = f"edge:{resource}", "write"
        elif kind in ("effect_node_mint",):
            key, direction = f"type:{resource}", "write"
        elif kind in ("effect_type_query", "effect_type_candidate_read"):
            key, direction = f"type:{resource}", "read"
        if key and static:
            known = static["reads"] if direction == "read" else static["writes"]
            any_flag = static["reads_any"] if direction == "read" else static["writes_any"]
            if key not in known and not any_flag:
                mismatches.append({**row, "direction": direction, "key": key})

    return {
        "n": n, "topology": topology, "mode": mode, "seed": seed,
        "trace_enabled": traced, "scale_audit_enabled": scale_enabled,
        "wall_time_ns": wall_ns, "cpu_time_ns": cpu_ns,
        "progress": progress, "terminal_progress": terminal, "states": states,
        "fixed_point_residuals": sum(residuals), "dropped_events": int(dropped),
        "scale_audit_counters": scale_counters,
        "per_rule_scale_audit_counters": {
            str(uid): metrics for uid, metrics in sorted(per_rule_metrics.items())
        },
        "event_rows": observed, "event_total": sum(row["count"] for row in observed),
        "distinct_concrete_nodes": len({row["node"] for row in observed if row["node"] is not None}),
        "distinct_static_rule_resources": len({(row["rule_uid"], row["kind"], row["resource"]) for row in observed}),
        "static_resource_mismatches": mismatches,
        "static_rules": [
            {"rule_uid": uid, "rule_name": value["name"],
             "reads": sorted(value["reads"]), "writes": sorted(value["writes"]),
             "reads_any": value["reads_any"], "writes_any": value["writes_any"],
             "match_edge_count": value["match_edge_count"]}
            for uid, value in sorted(uid_to_static.items())
        ],
    }


def main() -> None:
    import substrate_rs as sr
    from substrate.seed_loader import engine_rules_only
    import substrate_can_structure_envelope as can
    from substrate_rs import _native

    seed_doc = json.loads(can.SEED_FILE.read_text())
    cells = []
    for n in SIZES:
        for topology in TOPOLOGIES:
            for mode in ("2state", "3state"):
                for replicate in range(REPLICATES):
                    seed = 20260924 + n * 1000 + replicate
                    plain = run_arm(can, sr, engine_rules_only, seed_doc, n, topology, mode, seed, False, False)
                    traced = run_arm(can, sr, engine_rules_only, seed_doc, n, topology, mode, seed, True, True)
                    cells.append({"n": n, "topology": topology, "mode": mode,
                                  "replicate": replicate, "seed": seed,
                                  "untraced": plain, "traced": traced,
                                  "graph_outcome_matches": plain["states"] == traced["states"],
                                  "progress_matches": plain["progress"] == traced["progress"],
                                  "terminal_matches": plain["terminal_progress"] == traced["terminal_progress"] == 0,
                                  "both_independently_fixed": plain["fixed_point_residuals"] == traced["fixed_point_residuals"] == 0})
    checks = {
        "all_paired_graph_outcomes_match": all(cell["graph_outcome_matches"] for cell in cells),
        "all_paired_progress_matches": all(cell["progress_matches"] for cell in cells),
        "all_pairs_settle_and_pass_independent_fixed_point": all(
            cell["terminal_matches"] and cell["both_independently_fixed"] for cell in cells),
        "all_traced_cells_have_events_without_overflow": all(
            cell["traced"]["event_total"] > 0 and cell["traced"]["dropped_events"] == 0 for cell in cells),
        "all_traced_cells_have_scale_audit_coverage": all(
            cell["traced"]["scale_audit_counters"].get("leaf_visits", 0) > 0
            and cell["traced"]["scale_audit_counters"].get("term_evals_total", 0) > 0
            for cell in cells),
        "no_observed_key_false_negative_against_static_sets": all(
            not cell["traced"]["static_resource_mismatches"] for cell in cells),
    }
    extension = Path(_native.__file__).resolve()
    report = {
        "schema_version": 1,
        "run_id": "substrate-can-runtime-access-trace-v1-20260925",
        "scope": "authored CAN rules, N=8/16, path/complete topology, two-/three-state update, two seeded paired trace replicates per cell",
        "claim_boundary": (
            "Partial trace coverage on one authored workload family. It does not cover JIT/aggregate term reads, "
            "measure overhead, establish trace completeness, or validate frame partitioning."
        ),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "native_extension_path": str(extension), "native_extension_sha256": sha(extension),
            "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            "source_sha256": {path: sha(ROOT / path) for path in (
                "runners/dsl/src/access_trace.rs", "runners/dsl/src/lib.rs", "runners/dsl/src/rewrite.rs",
                "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
                "scripts/substrate_can_structure_envelope.py", "scripts/substrate_can_runtime_access_trace_v1.py",
                "seeds/can_native_reimplementation.json")},
        },
        "checks": checks, "cells": cells,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "cells": len(cells),
                      "total_observed_events": sum(c["traced"]["event_total"] for c in cells),
                      "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("CAN runtime access trace measurement failed")


if __name__ == "__main__":
    main()
