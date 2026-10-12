#!/usr/bin/env python3
"""Independent graph, mutation, safety, and partition audit for Bigville."""
from __future__ import annotations

import hashlib
import json
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/substrate_authored_bigville_cut_mutation_v1.py"
ANALYZER = Path(__file__)
LOCK = ROOT / "evaluation/substrate_capability/authored_bigville_cut_mutation_v1_lock_20260926.json"
RAW = ROOT / "evaluation/reports/substrate_authored_bigville_cut_mutation_v1_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_authored_bigville_cut_mutation_v1_analysis_20260926.json"


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def graph_digest(graph: dict) -> str:
    return sha_bytes(json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode())


def minfill(nodes: list[int], pairs: set[tuple[int, int]]) -> tuple[list[int], int]:
    g = {n: set() for n in nodes}
    for a, b in pairs:
        if a != b:
            g[a].add(b); g[b].add(a)
    order, width = [], 0
    while g:
        ranked = []
        for n, ns in g.items():
            q = sorted(ns)
            fill = sum(1 for i, a in enumerate(q) for b in q[i + 1:] if b not in g[a])
            ranked.append((fill, n))
        chosen = min(ranked)[1]; ns = list(g[chosen]); width = max(width, len(ns))
        for i, a in enumerate(ns):
            for b in ns[i + 1:]:
                g[a].add(b); g[b].add(a)
        for a in ns:
            g[a].discard(chosen)
        del g[chosen]; order.append(chosen)
    return order, width


def expected_metrics(checkpoint: dict, authored: dict[int, int]) -> tuple[list[int], int, dict[str, dict]]:
    graph = checkpoint["closure_graph"]
    task = set(authored); frames = sorted(set(authored.values())); nodes = sorted(task)
    sizes = [sum(authored[n] == f for n in nodes) for f in frames]
    edges = [(int(e["src"]), str(e["type"]), int(e["tgt"])) for e in graph["edges"]]
    obs = [(int(r[2]), int(r[4])) for r in checkpoint["runtime_access_trace"]
           if r[2] is not None and r[4] is not None]
    deps = {tuple(sorted((a, b))) for a, typ, b in edges
            if typ != "has_concept" and a in task and b in task and a != b}
    deps.update(tuple(sorted((a, b))) for a, b in obs if a in task and b in task and a != b)
    order, width = minfill(nodes, deps)
    owners = {"authored": dict(authored)}
    for name, grouping in (("balanced_id", nodes), ("dependency_min_fill", order)):
        owner = {}; cursor = 0
        for f, size in zip(frames, sizes):
            for n in grouping[cursor:cursor + size]:
                owner[n] = f
            cursor += size
        owners[name] = owner
    authored_pairs = [(a, b) for i, a in enumerate(nodes) for b in nodes[i + 1:]
                      if authored[a] == authored[b]]
    out = {}
    for name, owner in owners.items():
        causal_cross = [(a, b) for a, typ, b in edges
                        if typ == "causal_influence" and a in task and b in task and owner[a] != owner[b]]
        all_cross = [(a, typ, b) for a, typ, b in edges
                     if typ != "has_concept" and a in task and b in task and owner[a] != owner[b]]
        global_edges = [(a, typ, b) for a, typ, b in edges
                        if typ != "has_concept" and ((a in task) != (b in task))]
        touched = {n for a, _, b in all_cross for n in (a, b)}
        touched.update(a if a in task else b for a, _, b in global_edges)
        retained = sum(owner[a] == owner[b] for a, b in authored_pairs)
        by_type_cross, by_type_global = {}, {}
        for _, typ, _ in all_cross: by_type_cross[typ] = by_type_cross.get(typ, 0) + 1
        for _, typ, _ in global_edges: by_type_global[typ] = by_type_global.get(typ, 0) + 1
        out[name] = {"frame_sizes": [sum(owner[n] == f for n in nodes) for f in frames],
                     "causal_influence_cross_frame_directed_edges": len(causal_cross),
                     "all_nonownership_cross_frame_edges_by_type": by_type_cross,
                     "task_to_global_boundary_edges_by_type": by_type_global,
                     "known_cut_or_boundary_task_nodes": len(touched),
                     "within_authored_pair_retention": {"retained": retained,
                         "total": len(authored_pairs), "fraction": retained / len(authored_pairs) if authored_pairs else 1.0},
                     "min_fill_induced_width_upper_bound": width}
    return order, width, out


def main() -> None:
    raw = json.loads(RAW.read_text()); lock = json.loads(LOCK.read_text())
    locked_inputs = lock.get("locked_inputs", lock)
    current = {"runner_sha256": hashlib.sha256(RUNNER.read_bytes()).hexdigest(),
               "analyzer_sha256": hashlib.sha256(ANALYZER.read_bytes()).hexdigest()}
    checks = {"runner_and_analyzer_match_lock": all(locked_inputs.get(k) == v for k, v in current.items()),
              "post_run_sources_match_lock": raw["post_run_inputs"] == raw["locked_inputs"],
              "six_fresh_workers": len(raw["runs"]) == 6 and len({r["pid"] for r in raw["runs"]}) == 6,
              "all_preregistered_branches_and_trace_arms": {(r["branch"], r["traced"]) for r in raw["runs"]}
                  == {(b, t) for b in ("insert", "retract", "reweight") for t in (False, True)},
              "full_closure_fixed_point_and_independent_residual": all(
                  cp["closure_report"].get("status") == "fixed_point" and cp["independent_residual_count"] == 0
                  and cp["terminal_probe"].get("status") == "fixed_point"
                  and cp["terminal_probe"].get("progress_steps") == 0
                  for r in raw["runs"] for cp in r["checkpoints"]),
              "tested_link_changes_have_no_rule_effect_in_this_fixture": all(
                  not cp["closure_made_progress"] and not cp["closure_changed_graph"]
                  for r in raw["runs"] for cp in r["checkpoints"]),
              "zero_observed_trace_rows_reflected_without_absence_claim": all(
                  cp["trace_event_rows"] == 0 and cp["partition_metrics"]["observed_access_is_partial"]
                  for r in raw["runs"] for cp in r["checkpoints"]),
              "all_partition_arms_refused_before_scoped_execution": all(
                  cp["partition_execution"] == {"status": "refused_wildcard_rule_access", "scoped_calls": 0}
                  for r in raw["runs"] for cp in r["checkpoints"]),
              "raw_trace_off_on_graph_parity": all(all(v) for v in raw["trace_on_off_terminal_parity"].values()),
              "dialogue_unsupported_cell_retained": raw["dialogue_mutation_cell"]["status"]
                  == "unsupported_no_oracle_preserving_boundary_mutation_harness"}
    case_checks = {}
    for run in raw["runs"]:
        authored = {int(n): int(f) for n, f in run["authored_node_frame"]}
        stages = [cp["stage"] for cp in run["checkpoints"]]
        expect_stages = {"insert": ["insert_cross_frame_dependency"],
                         "retract": ["insert_before_retract", "retract_cross_frame_dependency"],
                         "reweight": ["insert_before_reweight", "reweight_same_edge_identity"]}[run["branch"]]
        per_cp = []
        for cp in run["checkpoints"]:
            graph = cp["closure_graph"]
            order, width, expected = expected_metrics(cp, authored)
            reported = {p["partition"]: p for p in cp["partition_metrics"]["partitions"]}
            id_a, id_b = run["fixed_endpoints"]
            directed = {(int(e["src"]), e["type"], int(e["tgt"])): e.get("attrs", {}) for e in graph["edges"]}
            edge_present = ((id_a, "causal_influence", id_b) in directed
                            and (id_b, "causal_influence", id_a) in directed)
            weight = directed.get((id_a, "causal_influence", id_b), {}).get("weight")
            if cp["stage"] == "insert_cross_frame_dependency":
                mutation_ok = edge_present and weight == 0.2
            elif cp["stage"] == "insert_before_retract":
                mutation_ok = edge_present and weight == 0.2
            elif cp["stage"] == "retract_cross_frame_dependency":
                mutation_ok = not edge_present
            elif cp["stage"] == "insert_before_reweight":
                mutation_ok = edge_present and weight == 0.2
            else:
                mutation_ok = edge_present and weight == 0.35 and cp.get("edge_identity_preserved") is True
            per_cp.append({"graph_digest_recomputed": graph_digest(graph) == cp["closure_graph_sha256"],
                           "min_fill_order_recomputed": order == cp["partition_metrics"]["min_fill_order_node_ids"],
                           "partition_metrics_recomputed": all(
                               all(reported[n].get(k) == v for k, v in value.items())
                               for n, value in expected.items()),
                           "mutation_state_correct": mutation_ok,
                           "complete_graph_inventory": cp["partition_metrics"]["complete_graph_edge_inventory"]})
        case_checks[f"{run['branch']}_{'trace' if run['traced'] else 'plain'}"] = {
            "branch_checkpoint_sequence": stages == expect_stages,
            "all_checkpoints_recomputed": all(all(x.values()) for x in per_cp),
            "checkpoint_checks": per_cp,
            "rule_wildcard_expected": run["target_rule_reads_any"],
        }
    checks["all_mutation_branch_checks_pass"] = all(x["branch_checkpoint_sequence"]
                                                    and x["all_checkpoints_recomputed"]
                                                    and x["rule_wildcard_expected"] for x in case_checks.values())
    result = {"schema_version": 1, "run_id": "substrate-authored-bigville-cut-mutation-v1-analysis-20260926",
              "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
              "lock_sha256": hashlib.sha256(LOCK.read_bytes()).hexdigest(),
              "checks": checks, "case_checks": case_checks,
              "claim_boundary": raw["claim_boundary"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "case_check_count": len(case_checks)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent authored Bigville cut/mutation analysis failed")


if __name__ == "__main__":
    main()
