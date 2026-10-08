#!/usr/bin/env python3
"""Run preregistered interacting-rule closure checks against a finite oracle."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = ROOT / "scripts/analyze_mint_termination_fragment.py"
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_mint_termination_fragment import analyze  # noqa: E402

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_MINT_INTERACTING_RULES_PREREG_20260925.md"
WORKLOADS = {
    "cascade": [
        {"name": "seed_to_witness", "match": [["x", "seed_link", "y"]], "effects": [
            ["add_node_if_absent", "w", "Witness", {"tag": "shared"}],
            ["add_edge", "y", "derived", "w", {}]]},
        {"name": "derived_to_marker", "match": [["y", "derived", "w"]], "effects": [
            ["add_node_if_absent", "m", "Marker", {"tag": "shared"}],
            ["add_edge", "w", "marker", "m", {}]]},
        {"name": "marker_self_loop", "match": [["w", "marker", "m"]], "effects": [
            ["add_edge", "m", "loop", "m", {}]]},
    ],
    "feedback": [
        {"name": "seed_to_witness", "match": [["x", "seed_link", "y"]], "effects": [
            ["add_node_if_absent", "w", "Witness", {"tag": "shared"}],
            ["add_edge", "y", "derived", "w", {}]]},
        {"name": "derived_feedback", "match": [["y", "derived", "w"]], "effects": [
            ["add_edge", "w", "seed_link", "y", {}]]},
    ],
}
INITIAL_EDGES = [[0, "seed_link", 1], [1, "seed_link", 2]]


def oracle(rules: list[dict], node_types: list[str], edges: set[tuple[int, str, int]],
           max_rounds: int = 1000) -> tuple[list[str], set[tuple[int, str, int]], int]:
    node_types = list(node_types)
    node_attrs: list[dict] = [{} for _ in node_types]
    edges = set(edges)
    progress_events = 0
    for _round in range(max_rounds):
        round_progress = False
        for rule in rules:
            bindings: list[dict[str, int]] = [{}]
            for src_var, et, tgt_var in rule["match"]:
                joined: list[dict[str, int]] = []
                for binding in bindings:
                    for src, edge_type, tgt in sorted(edges):
                        if edge_type != et:
                            continue
                        if src_var in binding and binding[src_var] != src:
                            continue
                        if tgt_var in binding and binding[tgt_var] != tgt:
                            continue
                        extended = dict(binding)
                        extended[src_var] = src
                        extended[tgt_var] = tgt
                        joined.append(extended)
                bindings = joined
            for binding in bindings:
                changed = False
                local = dict(binding)
                for effect in rule["effects"]:
                    if effect[0] == "add_node_if_absent":
                        _op, var, typ, attrs = effect
                        found = next((i for i, node_type in enumerate(node_types)
                                      if node_type == typ and all(
                                          node_attrs[i].get(k) == v for k, v in attrs.items())), None)
                        if found is None:
                            found = len(node_types)
                            node_types.append(typ)
                            node_attrs.append(dict(attrs))
                            changed = True
                        local[var] = found
                    elif effect[0] == "add_edge":
                        _op, src_var, et, tgt_var, _attrs = effect
                        item = (local[src_var], et, local[tgt_var])
                        if item not in edges:
                            edges.add(item)
                            changed = True
                    else:
                        raise ValueError(f"oracle does not support effect {effect[0]}")
                if changed:
                    round_progress = True
                    progress_events += 1
        if not round_progress:
            return node_types, edges, progress_events
    raise RuntimeError("independent oracle exceeded its finite closure guard")


def one_case(name: str, rules: list[dict]) -> dict:
    from substrate_rs import _native

    analysis = analyze(rules, ["0", "1", "2"],
                       [[str(src), edge_type, str(tgt)]
                        for src, edge_type, tgt in INITIAL_EDGES])
    s = _native.Substrate()
    nodes = [s.add_node("Seed") for _ in range(3)]
    for src, et, tgt in INITIAL_EDGES:
        s.add_edge_unchecked(nodes[src], et, nodes[tgt])
    for rule in rules:
        s.add_rule(rule)
    access = s.rule_access_sets()
    start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
    report = s.run_rules_report(1000, False)
    wall_ns, cpu_ns = time.perf_counter_ns() - start_wall, time.process_time_ns() - start_cpu

    expected_types, expected_edges, oracle_progress = oracle(rules, ["Seed"] * 3,
                                                             set(tuple(e) for e in INITIAL_EDGES))
    edge_types = sorted({e[1] for e in INITIAL_EDGES} |
                        {effect[2] for rule in rules for effect in rule["effects"] if effect[0] == "add_edge"})
    observed_edges = {(src, et, tgt) for src in range(s.node_count()) for et in edge_types
                      for tgt in range(s.node_count())
                      if s.has_edge(_native.NodeID(src), et, _native.NodeID(tgt))}
    expected_type_counts = {typ: expected_types.count(typ) for typ in set(expected_types)}
    observed_type_counts = {typ: len(s.nodes(typ)) for typ in expected_type_counts}
    exact_graph = (s.node_count() == len(expected_types) and observed_edges == expected_edges
                   and observed_type_counts == expected_type_counts and s.edge_count() == len(expected_edges))
    bound = analysis["progress_steps_upper_bound"]
    return {
        "workload": name,
        "rules": rules,
        "classifier": analysis,
        "native_access_sets": access,
        "native_report": report,
        "oracle": {"node_types": expected_types, "edge_triples": [list(e) for e in sorted(expected_edges)],
                   "progress_events": oracle_progress},
        "native_state": {"node_count": s.node_count(), "edge_count": s.edge_count(),
                         "edge_triples": [list(e) for e in sorted(observed_edges)],
                         "type_counts": observed_type_counts},
        "static_progress_bound": bound,
        "native_progress_within_bound": report["progress_steps"] <= bound,
        "oracle_progress_within_bound": oracle_progress <= bound,
        "exact_graph_match": exact_graph,
        "cost": {"wall_time_ns": wall_ns, "cpu_time_ns": cpu_ns},
        "checks": {"classifier_accepts": analysis["accepted"],
                   "native_fixed_point": report["status"] == "fixed_point",
                   "native_graph_equals_oracle": exact_graph,
                   "native_progress_within_bound": report["progress_steps"] <= bound,
                   "oracle_progress_within_bound": oracle_progress <= bound},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],
        cwd=ROOT, env=env, text=True).strip()
    if stale:
        raise SystemExit(f"native build is stale:\n{stale}")
    from substrate_rs import _native

    records = [one_case(name, rules) for name, rules in WORKLOADS.items()]
    checks = [check for row in records for check in row["checks"].values()]
    native_sha = hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()
    build_record_path = ROOT / "runners/dsl/python/substrate_rs/_native.build.json"
    result = {
        "schema_version": 1, "run_id": f"mint-interacting-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "preregistration": {"path": str(PREREG.relative_to(ROOT)),
                            "sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest()},
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty_tree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "native_sha256": native_sha, "python": sys.version.split()[0], "platform": platform.platform(),
        "build_record_sha256": hashlib.sha256(build_record_path.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "analyzer_sha256": hashlib.sha256(ANALYZER_PATH.read_bytes()).hexdigest(),
        "configuration": {"budget": 1000, "cycle_detection": False, "case_count": len(records)},
        "records": records, "all_checks_pass": all(checks),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": result["all_checks_pass"],
                      "cases": {r["workload"]: r["checks"] for r in records}}, sort_keys=True))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
