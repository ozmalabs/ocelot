#!/usr/bin/env python3
"""Controlled transitive-closure pilot for the substrate capability programme.

This is a pilot harness, not a confirmatory benchmark. It measures a known finite
closure family through the current native PyO3 rule runner and emits one JSON
document containing provenance plus per-size records. Run from the repository
root with `PYTHONPATH=runners/dsl/python:.` after `scripts/engine_build.sh`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md"
ANALYSIS = ROOT / "scripts/summarize_substrate_audit_overhead.py"
BUILD_RECORD = ROOT / "runners/dsl/python/substrate_rs/_native.build.json"
NATIVE_SO = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def max_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux reports KiB; macOS reports bytes.
    return int(value * 1024 if sys.platform.startswith("linux") else value)


def make_links(node_count: int, topology: str) -> list[tuple[int, int]]:
    links = [(i, i + 1) for i in range(node_count - 1)]
    if topology == "banded_dag":
        links.extend((i, i + 2) for i in range(node_count - 2))
    elif topology == "complete_dag":
        links = [(i, j) for i in range(node_count) for j in range(i + 1, node_count)]
    return links


def expected_reach_count(node_count: int, links: list[tuple[int, int]]) -> int:
    """Count pairs connected by a path of length at least two."""
    adjacency = [[] for _ in range(node_count)]
    for left, right in links:
        adjacency[left].append(right)
    count = 0
    for source in range(node_count):
        seen_states = set()
        found_at_distance_two_or_more = set()
        stack = [(target, 1) for target in adjacency[source]]
        while stack:
            target, distance = stack.pop()
            if target == source:
                continue
            if distance >= 2:
                found_at_distance_two_or_more.add(target)
            state = (target, min(distance, 2))
            if state in seen_states:
                continue
            seen_states.add(state)
            stack.extend((next_target, distance + 1) for next_target in adjacency[target])
        count += len(found_at_distance_two_or_more)
    return count


def make_substrate(node_count: int, topology: str, rule_family: str):
    from substrate_rs import _native

    s = _native.Substrate()
    nodes = [s.add_node("PilotVertex") for _ in range(node_count)]
    links = make_links(node_count, topology)
    for left, right in links:
        s.add_edge_unchecked(nodes[left], "pilot_link", nodes[right])

    if rule_family == "transitive_closure":
        rules = [
            {"name": "pilot_two_link_reach",
             "match": [["x", "pilot_link", "y"], ["y", "pilot_link", "z"]],
             "effects": [["add_edge", "x", "pilot_reach", "z", {}]]},
            {"name": "pilot_reach_extend_link",
             "match": [["x", "pilot_reach", "y"], ["y", "pilot_link", "z"]],
             "effects": [["add_edge", "x", "pilot_reach", "z", {}]]},
        ]
    elif rule_family == "duplicate_noop":
        rules = [{"name": "pilot_duplicate_existing_link",
                  "match": [["x", "pilot_link", "y"]],
                  "effects": [["add_edge", "x", "pilot_link", "y", {}]]}]
    elif rule_family == "bounded_mint":
        rules = [{"name": "pilot_reuse_one_witness",
                  "match": [["x", "pilot_link", "y"]],
                  "effects": [
                      ["add_node_if_absent", "w", "PilotWitness", {"tag": "shared"}],
                      ["add_edge", "x", "pilot_witness", "w", {}],
                  ]}]
    else:
        raise ValueError(f"unknown rule family: {rule_family}")
    for rule in rules:
        s.add_rule(rule)
    return s, links


def scale_snapshot(substrate_type) -> dict[str, int]:
    return dict(substrate_type.scale_audit_snapshot())


def measure_one(node_count: int, topology: str, rule_family: str, max_steps: int, run_id: str,
                audit_mode: str, replicate: int) -> dict:
    from substrate_rs import _native

    NativeSubstrate = _native.Substrate
    peak_rss_after_import = max_rss_bytes()
    s, links = make_substrate(node_count, topology, rule_family)
    peak_rss_after_setup = max_rss_bytes()
    nodes_before = s.node_count()
    edges_before = s.edge_count()
    s.counters_clear()
    NativeSubstrate.scale_audit_reset()
    audit_enabled = audit_mode == "on"
    NativeSubstrate.scale_audit_set_enabled(audit_enabled)

    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    steps = s.run_rules(max_steps)
    cpu_ns = time.process_time_ns() - cpu_start
    wall_ns = time.perf_counter_ns() - wall_start

    counters = s.counters()
    scale = scale_snapshot(NativeSubstrate)
    nodes_after = s.node_count()
    edges_after = s.edge_count()
    peak_rss_after_primary = max_rss_bytes()

    # The public runner returns a progress-step count, not a terminal status.
    # A separate one-step probe distinguishes a settled graph from a run that
    # stopped at the cap with work remaining. Probe cost is excluded above.
    NativeSubstrate.scale_audit_reset()
    probe_before_edges = s.edge_count()
    probe_steps = s.run_rules(1)
    probe_after_edges = s.edge_count()
    probe_scale = scale_snapshot(NativeSubstrate)
    NativeSubstrate.scale_audit_set_enabled(False)

    expected_reach = (expected_reach_count(node_count, links)
                      if rule_family == "transitive_closure" else 0)
    expected_nodes = node_count + (1 if rule_family == "bounded_mint" else 0)
    expected_growth = (expected_reach if rule_family == "transitive_closure"
                       else len({src for src, _ in links}) if rule_family == "bounded_mint"
                       else 0)
    expected_edges = len(links) + expected_growth
    degree = [0] * node_count
    for left, right in links:
        degree[left] += 1
        degree[right] += 1
    treewidth = (1 if topology == "path" else 2 if topology == "banded_dag"
                 else node_count - 1)
    if probe_steps == 0:
        terminal = "settled"
    else:
        terminal = "cap_reached_unsettled"

    return {
        "run_id": run_id,
        "protocol_version": "pilot-0.1",
        "condition": f"native_rule_runner_audit_{audit_mode}",
        "instance_id": f"{topology}_n{node_count}",
        "split": "development",
        "seed": 0,
        "input_structure": {
            "nodes": node_count,
            "edges": len(links),
            "max_degree": max(degree),
            "treewidth_exact": treewidth,
            "treewidth_upper_bound": treewidth,
            "treewidth_provenance": "construction-known for this graph family",
            "boundary_width": None,
            "hierarchy_depth": None,
            "rule_count": 2 if rule_family == "transitive_closure" else 1,
            "pattern_size": 2,
            "domain_size": None,
            "horizon": None,
        },
        "outcome": {
            "status": "success" if edges_after == expected_edges and nodes_after == expected_nodes and probe_steps == 0 else "failure",
            "quality": 1.0 if edges_after == expected_edges and nodes_after == expected_nodes else 0.0,
            "exact": edges_after == expected_edges and nodes_after == expected_nodes,
            "reason": terminal,
            "ground_truth_ref": (f"formula:{rule_family}:n={node_count}:topology={topology}"),
        },
        "cost": {
            "wall_time_ns": wall_ns,
            "cpu_time_ns": cpu_ns,
            "peak_rss_bytes": max_rss_bytes(),
            "allocations": None,
            "rule_matches": scale.get("leaf_visits") if audit_enabled else None,
            "rule_firings": steps,
            "fixpoint_passes": None,
            "graph_writes": None,
            "nodes_minted": nodes_after - nodes_before,
            "search_expansions": None,
            "solver_iterations": None,
        },
        "path": {
            "native_or_host": "native-pyo3-rule-runner",
            "entrypoint": "substrate_rs._native.Substrate.run_rules",
            "state_owner": "Rust Substrate graph",
            "boundary_crossings": scale.get("ffi_calls") if audit_enabled else None,
        },
        "failure_trace_ref": None,
        "pilot_detail": {
            "topology": topology,
            "rule_family": rule_family,
            "audit_mode": audit_mode,
            "replicate": replicate,
            "scale_audit_enabled": audit_enabled,
            "max_steps": max_steps,
            "progress_steps": steps,
            "nodes_before": nodes_before,
            "nodes_after": nodes_after,
            "edges_before": edges_before,
            "edges_after": edges_after,
            "expected_reach_edges": expected_reach,
            "expected_nodes_after": expected_nodes,
            "expected_total_edges": expected_edges,
            "terminal_status_probe_steps": probe_steps,
            "terminal_status_probe_edge_delta": probe_after_edges - probe_before_edges,
            "primary_scale_audit": scale,
            "terminal_probe_scale_audit": probe_scale,
            "substrate_counters_after_primary": counters,
            "rule_costs": s.rule_costs(),
            "candidate_pairs_enumerated": scale.get("cand_enum") if audit_enabled else None,
            "counter_invariants": {
                "candidate_path_sum_matches_total": (
                    scale.get("cand_enum_scan", 0) + scale.get("cand_enum_local", 0)
                    + scale.get("cand_enum_hinted", 0) == scale.get("cand_enum", 0)),
                "first_repeat_sum_matches_total": (
                    scale.get("cand_enum_first", 0) + scale.get("cand_enum_repeat", 0)
                    == scale.get("cand_enum", 0)),
                "candidate_tested_matches_enumerated": (
                    scale.get("cand_tested", 0) == scale.get("cand_enum", 0)),
                "edge_insert_attempts_cover_committed_edge_growth": (
                    scale.get("rule_effect_edge_insert_attempts", 0)
                    >= edges_after - edges_before),
            } if audit_enabled else None,
            "process_peak_rss_scope": "high-water mark of this isolated worker process; includes interpreter and extension startup",
            "peak_rss_after_import_bytes": peak_rss_after_import,
            "peak_rss_after_graph_and_rules_bytes": peak_rss_after_setup,
            "peak_rss_after_primary_run_bytes": peak_rss_after_primary,
            "primary_peak_rss_delta_over_import_bytes": max(0, peak_rss_after_primary - peak_rss_after_import),
            "setup_peak_rss_delta_over_import_bytes": max(0, peak_rss_after_setup - peak_rss_after_import),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[8, 16, 32])
    parser.add_argument("--topologies", choices=["path", "banded_dag", "complete_dag"], nargs="+",
                        default=["path"])
    parser.add_argument("--rule-families",
                        choices=["transitive_closure", "duplicate_noop", "bounded_mint"],
                        nargs="+", default=["transitive_closure"])
    parser.add_argument("--max-steps", type=int, default=100_000)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--audit-modes", choices=["on", "off"], nargs="+", default=["on"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker-size", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--worker-topology", choices=["path", "banded_dag", "complete_dag"],
                        help=argparse.SUPPRESS)
    parser.add_argument("--worker-family",
                        choices=["transitive_closure", "duplicate_noop", "bounded_mint"],
                        help=argparse.SUPPRESS)
    parser.add_argument("--worker-run-id", help=argparse.SUPPRESS)
    parser.add_argument("--worker-audit-mode", choices=["on", "off"], default="on",
                        help=argparse.SUPPRESS)
    parser.add_argument("--worker-replicate", type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker_size is not None:
        if args.worker_size < 3 or args.max_steps < 1 or not args.worker_topology or not args.worker_family or not args.worker_run_id:
            parser.error("invalid isolated worker parameters")
        record = measure_one(args.worker_size, args.worker_topology, args.worker_family,
                             args.max_steps, args.worker_run_id,
                             args.worker_audit_mode, args.worker_replicate)
        print(json.dumps(record, sort_keys=True))
        return 0
    if args.output is None:
        parser.error("--output is required outside worker mode")
    if any(n < 3 for n in args.sizes):
        parser.error("all sizes must be at least 3")
    if args.max_steps < 1 or args.repeats < 1:
        parser.error("--max-steps must be positive")

    stale = subprocess.check_output(
        [sys.executable, "-c",
         "from domains.engine_provenance import build_is_stale; "
         "print('\\n'.join(build_is_stale('.')))"],
        cwd=ROOT, env={**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}"},
        text=True,
    ).strip()
    if stale:
        raise SystemExit(f"native engine is stale; rebuild with scripts/engine_build.sh:\n{stale}")

    protocol_hash = sha256_file(PROTOCOL)
    input_spec = {"families": args.rule_families, "sizes": args.sizes,
                  "topologies": args.topologies,
                  "audit_modes": args.audit_modes, "repeats": args.repeats,
                  "rules": {"transitive_closure": ["link-link->reach", "reach-link->reach"],
                            "duplicate_noop": ["link->same_link"],
                            "bounded_mint": ["link->add_node_if_absent+link_to_witness"]}}
    generated_hash = sha256_bytes(json.dumps(input_spec, sort_keys=True).encode())
    run_id = f"closure-pilot-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    before = time.time_ns()
    records = []
    worker_env = {**os.environ,
                   "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    for rule_family in args.rule_families:
        for topology in args.topologies:
            for n in args.sizes:
                for replicate in range(args.repeats):
                    mode_order = list(args.audit_modes)
                    if replicate % 2:
                        mode_order.reverse()
                    for audit_mode in mode_order:
                        worker = subprocess.run(
                            [sys.executable, str(Path(__file__).relative_to(ROOT)),
                             "--worker-size", str(n), "--worker-topology", topology,
                             "--worker-family", rule_family,
                             "--worker-run-id", run_id, "--worker-audit-mode", audit_mode,
                             "--worker-replicate", str(replicate),
                             "--max-steps", str(args.max_steps)],
                            cwd=ROOT, env=worker_env, text=True, capture_output=True,
                        )
                        if worker.returncode:
                            raise RuntimeError(
                                f"isolated worker failed ({rule_family}, {topology}, n={n}, replicate={replicate}, "
                                f"audit={audit_mode}, exit={worker.returncode}):\n"
                                f"stdout:\n{worker.stdout}\nstderr:\n{worker.stderr}")
                        record = json.loads(worker.stdout)
                        if audit_mode == "on" and not all(
                                record["pilot_detail"]["counter_invariants"].values()):
                            raise RuntimeError(
                                f"counter reconciliation failed: {rule_family}, {topology}, n={n}")
                        record["pilot_detail"]["worker_stderr"] = worker.stderr
                        records.append(record)
    after = time.time_ns()
    dirty = bool(git("status", "--porcelain"))
    rust_sources = git("diff", "HEAD", "--", "runners/dsl/src", "runners/dsl/Cargo.toml").encode()
    build_record = json.loads(BUILD_RECORD.read_text())

    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "run_state": "pilot",
        "protocol": {"name": "SUBSTRATE_BENCHMARK_PROTOCOL", "version": "1.0",
                     "sha256": protocol_hash},
        "hypothesis": {
            "statement": "Native transitive-closure, duplicate-no-op, and bounded-mint rule families produce their exact expected graph states and settle; repeated audit-on/off workers estimate instrumentation overhead where requested.",
            "primary_metric": "exact_state_candidate_work_and_cost_by_rule_family_topology_and_size",
            "decision_rule": "Pilot only: every worker must match its exact state oracle and settle; counter invariants apply to audit-on workers; timing is descriptive and supports no tractability claim.",
            "secondary_metrics": ["wall_time_ns", "cpu_time_ns", "peak_rss_bytes", "leaf_visits", "cand_enum"],
            "preregistration_ref": None,
        },
        "source": {"commit": git("rev-parse", "HEAD"), "dirty": dirty,
                   "patch_sha256": sha256_bytes(rust_sources) if rust_sources else None},
        "build": {
            "rustc": subprocess.check_output(["rustc", "--version"], text=True).strip(),
            "python": sys.version.split()[0],
            "dependency_lock_sha256": None,
            "build_flags": ["cargo build --release"],
            "native_artifacts": [{"path": str(NATIVE_SO.relative_to(ROOT)), "sha256": sha256_file(NATIVE_SO)},
                                 {"path": str(BUILD_RECORD.relative_to(ROOT)), "sha256": sha256_file(BUILD_RECORD)}],
        },
        "environment": {
            "os": platform.platform(), "architecture": platform.machine(),
            "cpu_model": platform.processor() or None, "cpu_count": os.cpu_count(),
            "ram_bytes": None, "accelerators": [], "runtime_config": {},
        },
        "workload": {
            "capability_id": "engine.rule_execution.synthetic_families",
            "family": "synthetic_graph_rule_families", "generator_sha256": sha256_file(Path(__file__)),
            "data_sha256": generated_hash, "split": "development",
            "instance_count": len(records),
            "input_dimensions": {"families": args.rule_families,
                                 "sizes": args.sizes, "topologies": args.topologies,
                                 "audit_modes": args.audit_modes, "repeats": args.repeats,
                                 "max_steps": args.max_steps},
        },
        "conditions": [{
            "condition_id": f"native_rule_runner_audit_{mode}",
            "role": "candidate" if mode == "on" else "ablation",
            "implementation": ("native rewrite engine with scale audit enabled"
                               if mode == "on" else "same native rewrite engine with scale audit disabled"),
            "entrypoint": "substrate_rs._native.Substrate.run_rules",
            "state_owner": "Rust Substrate graph",
            "budget": {"wall_time_ms": None, "cpu_time_ms": None, "memory_bytes": None},
        } for mode in args.audit_modes],
        "analysis": {
            "analysis_sha256": (sha256_file(ANALYSIS)
                                if {"on", "off"}.issubset(args.audit_modes) else None),
            "primary_unit": "directed_graph_instance",
            "interval_method": "median, range, and paired audit-on/off ratios are descriptive only",
            "multiple_comparison_rule": "no confirmatory hypothesis test; exploratory scaling and instrumentation overhead only",
            "exclusion_policy": "no exclusions; errors and caps remain outcomes",
            "thresholds": {"max_steps": args.max_steps, "minimum_nodes": 3},
        },
        "custody": {"classification": "project-self-custodied",
                    "description": "Local development pilot; not independent evaluation.", "evaluator_role": None},
        "artifacts": {
            "command": [sys.executable, str(Path(__file__).relative_to(ROOT)), "--sizes",
                        *map(str, args.sizes), "--topologies", *args.topologies,
                        "--rule-families", *args.rule_families,
                        "--repeats", str(args.repeats), "--audit-modes", *args.audit_modes,
                        "--max-steps", str(args.max_steps), "--output", str(args.output)],
            "stdout_ref": None, "stderr_ref": None, "raw_records_ref": str(args.output),
            "resource_log_ref": None, "result_ref": None,
        },
        "started_at_unix_ns": before,
        "finished_at_unix_ns": after,
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"run_id": run_id, "output": str(args.output),
                      "stale_sources": [], "records": [
                          {"topology": r["pilot_detail"]["topology"],
                           "rule_family": r["pilot_detail"]["rule_family"],
                           "n": r["input_structure"]["nodes"],
                           "replicate": r["pilot_detail"]["replicate"],
                           "audit": r["pilot_detail"]["audit_mode"],
                           "status": r["outcome"]["status"],
                           "edges": r["pilot_detail"]["edges_after"],
                           "expected_edges": r["pilot_detail"]["expected_total_edges"],
                           "steps": r["pilot_detail"]["progress_steps"],
                           "candidates": r["pilot_detail"]["candidate_pairs_enumerated"],
                           "leaf_visits": r["cost"]["rule_matches"],
                           "wall_ms": round(r["cost"]["wall_time_ns"] / 1e6, 3)}
                          for r in records]}, indent=2))
    return 0 if all(r["outcome"]["status"] == "success" for r in records) else 2


if __name__ == "__main__":
    raise SystemExit(main())
