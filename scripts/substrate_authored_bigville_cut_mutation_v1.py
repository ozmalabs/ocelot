#!/usr/bin/env python3
"""Locked Bigville cut-rebuild diagnostic with three boundary mutations."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "docs/research/engine_substrate/SUBSTRATE_AUTHORED_BIGVILLE_CUT_MUTATION_V1_PREREG_20260926.md"
BASE = ROOT / "scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py"
CAST = ROOT / "seeds/bigville_cast100.json"
SEED = ROOT / "seeds/can_native_reimplementation.json"
BUILDER = ROOT / "worlds/bigville_can_beliefs.py"
LOCK = ROOT / "evaluation/substrate_capability/authored_bigville_cut_mutation_v1_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_authored_bigville_cut_mutation_v1_20260926.json"
ANALYZER = ROOT / "scripts/analyze_substrate_authored_bigville_cut_mutation_v1.py"
BRANCHES = ("insert", "retract", "reweight")
TRACING = (False, True)
CAP = 100_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nid(x) -> int:
    return int(x.value if hasattr(x, "value") else x)


def load_base():
    spec = importlib.util.spec_from_file_location("authored_bigville_mutation_base", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import locked Bigville base builder")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def locked_inputs() -> dict:
    from substrate_rs import _native
    native = Path(_native.__file__).resolve()
    return {"protocol_sha256": sha(PROTO), "runner_sha256": sha(Path(__file__)),
            "analyzer_sha256": sha(ANALYZER), "base_runner_sha256": sha(BASE),
            "cast_sha256": sha(CAST), "seed_sha256": sha(SEED),
            "builder_sha256": sha(BUILDER), "native_extension_sha256": sha(native),
            "native_extension_path": str(native),
            "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            "cargo_lock_sha256": sha(ROOT / "runners/dsl/Cargo.lock"),
            "rust_sources_sha256": {name: sha(ROOT / "runners/dsl/src" / name)
                                    for name in ("graph.rs", "rewrite.rs", "substrate.rs", "term.rs", "access_trace.rs", "py.rs")}}


def min_fill(nodes: list[int], pairs: set[tuple[int, int]]) -> tuple[list[int], int]:
    graph = {n: set() for n in nodes}
    for a, b in pairs:
        if a != b:
            graph[a].add(b); graph[b].add(a)
    order, width = [], 0
    while graph:
        candidate = min((sum(1 for i, a in enumerate(sorted(neighbors))
                          for b in sorted(neighbors)[i + 1:] if b not in graph[a]), node)
                        for node, neighbors in graph.items())[1]
        neighbors = list(graph[candidate]); width = max(width, len(neighbors))
        for i, a in enumerate(neighbors):
            for b in neighbors[i + 1:]:
                graph[a].add(b); graph[b].add(a)
        for a in neighbors:
            graph[a].discard(candidate)
        del graph[candidate]; order.append(candidate)
    return order, width


def partition_metrics(inner, authored: dict[int, int], *, traced_accesses: list,
                      construction_started: int) -> dict:
    cpu_started = time.process_time_ns()
    task = set(authored); frames = sorted(set(authored.values()))
    sizes = [sum(authored[n] == f for n in task) for f in frames]
    graph = inner.graph_to_dict()
    edge_rows = [(int(e["src"]), str(e["type"]), int(e["tgt"]), dict(e.get("attrs", {})))
                 for e in graph["edges"]]
    dependency_edges = [(a, b) for a, typ, b, _ in edge_rows if typ == "causal_influence"]
    owned_links = [(a, b) for a, typ, b, _ in edge_rows if typ == "has_concept"]
    obs = [(int(r[2]), int(r[4]), int(r[5])) for r in traced_accesses
           if r[2] is not None and r[4] is not None]
    pairs = {tuple(sorted((a, b))) for a, typ, b, _ in edge_rows
             if typ != "has_concept" and a in task and b in task and a != b}
    pairs.update(tuple(sorted((a, b))) for a, b, _ in obs if a in task and b in task and a != b)
    order, width = min_fill(sorted(task), pairs)
    balanced, derived = {}, {}
    cursor = 0
    for f, size in zip(frames, sizes):
        for n in sorted(task)[cursor:cursor + size]:
            balanced[n] = f
        for n in order[cursor:cursor + size]:
            derived[n] = f
        cursor += size
    result = []
    authored_pairs = [(a, b) for i, a in enumerate(sorted(task))
                      for b in sorted(task)[i + 1:] if authored[a] == authored[b]]
    full_edges = [(a, typ, b) for a, typ, b, _ in edge_rows if typ != "has_concept"]
    for name, owner in (("authored", authored), ("balanced_id", balanced), ("dependency_min_fill", derived)):
        cross_dep = [(a, b) for a, b in dependency_edges if a in task and b in task and owner[a] != owner[b]]
        cross_all = [(a, typ, b) for a, typ, b in full_edges if a in task and b in task and owner[a] != owner[b]]
        boundary = [(a, typ, b) for a, typ, b in full_edges if (a in task) != (b in task)]
        touched = {x for a, _, b in cross_all for x in (a, b)}
        touched |= {a if a in task else b for a, _, b in boundary}
        keep = sum(owner[a] == owner[b] for a, b in authored_pairs)
        result.append({"partition": name,
                       "frame_sizes": [sum(owner[n] == f for n in task) for f in frames],
                       "causal_influence_cross_frame_directed_edges": len(cross_dep),
                       "all_nonownership_cross_frame_edges_by_type": _counts(cross_all, 1),
                       "task_to_global_boundary_edges_by_type": _counts(boundary, 1),
                       "known_cut_or_boundary_task_nodes": len(touched),
                       "within_authored_pair_retention": {"retained": keep, "total": len(authored_pairs),
                                                          "fraction": keep / len(authored_pairs) if authored_pairs else 1.0},
                       "min_fill_induced_width_upper_bound": width})
    static = []
    for row in inner.rule_access_sets():
        index, name, active, reads, term_edges, writes, reads_any, writes_any = row
        static.append({"index": int(index), "name": str(name), "active": bool(active),
                       "reads_any": bool(reads_any), "writes_any": bool(writes_any),
                       "reads": sorted(set(reads) | set(term_edges)), "writes": sorted(writes)})
    rebuild_ns = time.perf_counter_ns() - construction_started
    rebuild_cpu_ns = time.process_time_ns() - cpu_started
    return {"partition_rebuild_wall_ns": rebuild_ns, "partition_rebuild_cpu_ns": rebuild_cpu_ns,
            "task_nodes": len(task), "frame_count": len(frames),
            "authored_frame_sizes": sizes, "causal_dependency_pair_count": len(pairs),
            "observed_access_row_count": len(traced_accesses),
            "observed_task_access_pair_count": len({tuple(sorted((a, b))) for a, b, _ in obs if a in task and b in task and a != b}),
            "observed_access_is_partial": True, "edge_inventory_types": sorted({t for _, t, _, _ in edge_rows}),
            "has_concept_ownership_link_count_excluded_from_dependency_metrics": len(owned_links),
            "complete_graph_edge_inventory": True, "static_rule_access": static,
            "min_fill_order_node_ids": order, "partitions": result,
            "cut_construction_status": "complete graph typed edges; ownership links reported separately"}


def _counts(rows, ix):
    out = {}
    for row in rows:
        key = str(row[ix - 1])
        # For edge triples the type is column 1; branch passes ix=1.
        if len(row) == 3:
            key = str(row[1])
        out[key] = out.get(key, 0) + 1
    return out


def branch_worker(branch: str, traced: bool) -> dict:
    import substrate_rs as sr
    from substrate_rs import _native
    from worlds import bigville_can_beliefs as bigville
    base = load_base(); cast = json.loads(CAST.read_text())["residents"]; seed = json.loads(SEED.read_text())
    (outer, inner, residents, mts, concepts, frame_nodes, node_frame, edges, cross,
     ref_by_id, node_flat) = base.build(sr, cast, seed, bigville)
    if len(frame_nodes) != 100 or set(map(len, frame_nodes)) != {5} or cross:
        raise RuntimeError("Bigville authored ownership precondition failed")
    # Capture the target CAN rule's complete active declaration; the builder
    # deliberately loads only this one production rule for the frozen replay.
    rule_rows = [r for r in inner.rule_access_sets() if r[2] and r[1] == "can_native_update_3state"]
    if len(rule_rows) != 1:
        raise RuntimeError("expected exactly one active native CAN update rule")
    wildcard = bool(rule_rows[0][6])
    a_id = base.nid(concepts[0]["world_safe"]); b_id = base.nid(concepts[1]["world_safe"])
    a, b = ref_by_id[a_id], ref_by_id[b_id]
    weight = 0.2
    dynamic_weights = base.weights_by_id(concepts, residents, bigville, node_flat)

    def apply_edge(value):
        inner.add_edge_unchecked(a, "causal_influence", b, {"weight": value})
        inner.add_edge_unchecked(b, "causal_influence", a, {"weight": value})
        for left, right in ((a_id, b_id), (b_id, a_id)):
            pair = (node_flat[left], node_flat[right])
            dynamic_weights[:] = [row for row in dynamic_weights if row[:2] != pair]
            dynamic_weights.append((pair[0], pair[1], value))

    def capture(stage: str, mutation_ns: int) -> dict:
        before = inner.graph_to_dict()
        started_wall, started_cpu = time.perf_counter_ns(), time.process_time_ns()
        closure = dict(inner.run_rules_report(CAP, False))
        wall_ns = time.perf_counter_ns() - started_wall; cpu_ns = time.process_time_ns() - started_cpu
        graph = inner.graph_to_dict()
        rebuild_started = time.perf_counter_ns()
        trace_rows, dropped = inner.runtime_access_trace_snapshot()
        structural = partition_metrics(inner, node_frame, traced_accesses=trace_rows,
                                       construction_started=rebuild_started)
        states = base.states(inner, concepts); fields = base.fields(inner, concepts)
        residual = base.residuals(states, fields, dynamic_weights)
        terminal = dict(inner.run_rules_report(CAP, False))
        final_graph = inner.graph_to_dict()
        return {"stage": stage, "mutation_ns": mutation_ns,
                "preclosure_graph_sha256": hashlib.sha256(json.dumps(before, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest(),
                "closure_graph_sha256": hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest(),
                "preclosure_graph": before, "closure_graph": graph,
                "terminal_graph_sha256": hashlib.sha256(json.dumps(final_graph, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest(),
                "closure_report": closure, "terminal_probe": terminal,
                "closure_changed_graph": graph != before,
                "closure_made_progress": int(closure.get("progress_steps", 0)) > 0,
                "closure_wall_ns": wall_ns, "closure_cpu_ns": cpu_ns,
                "independent_residual_count": sum(residual), "trace_dropped": int(dropped),
                "trace_event_rows": len(trace_rows),
                "runtime_access_trace": [[int(x[0]), str(x[1]), x[2], x[3], x[4], int(x[5])] for x in trace_rows],
                "partition_metrics": structural,
                "partition_execution": {"status": "refused_wildcard_rule_access" if wildcard else "not_attempted",
                                        "scoped_calls": 0}}

    # Fresh baseline settle, then prepare the operation branch.
    inner.run_rules_report(CAP, False)
    inner.runtime_access_trace_reset(); inner.runtime_access_trace_set_enabled(traced)
    cp = []
    t = time.perf_counter_ns(); apply_edge(weight); insert_ns = time.perf_counter_ns() - t
    if branch == "insert":
        cp.append(capture("insert_cross_frame_dependency", insert_ns))
    else:
        cp.append(capture("insert_before_" + branch, insert_ns))
        if branch == "retract":
            t = time.perf_counter_ns()
            inner.remove_edge_unchecked(a, "causal_influence", b)
            inner.remove_edge_unchecked(b, "causal_influence", a)
            dynamic_weights[:] = [row for row in dynamic_weights
                                  if row[:2] not in {(node_flat[a_id], node_flat[b_id]), (node_flat[b_id], node_flat[a_id])}]
            mutation_ns = time.perf_counter_ns() - t
            cp.append(capture("retract_cross_frame_dependency", mutation_ns))
        elif branch == "reweight":
            t = time.perf_counter_ns(); apply_edge(0.35); mutation_ns = time.perf_counter_ns() - t
            after = inner.graph_to_dict()
            cp.append(capture("reweight_same_edge_identity", mutation_ns))
            cp[-1]["edge_identity_preserved"] = any(int(e["src"]) == a_id and int(e["tgt"]) == b_id and e["type"] == "causal_influence" and e.get("attrs", {}).get("weight") == 0.35 for e in after["edges"])
        else:
            raise ValueError(branch)
    native = Path(_native.__file__).resolve()
    return {"branch": branch, "traced": traced, "pid": os.getpid(),
            "native_extension_sha256": sha(native), "fresh_100_frame_baseline": True,
            "target_rule_reads_any": wildcard, "fixed_endpoints": [a_id, b_id],
            "authored_node_frame": [[int(n), int(f)] for n, f in sorted(node_frame.items())],
            "checkpoints": cp, "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def main() -> None:
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(branch_worker(sys.argv[2], sys.argv[3] == "trace"), sort_keys=True)); return
    locked = locked_inputs()
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": locked}, indent=2, sort_keys=True)); return
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale lock")
    env = dict(os.environ); env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    runs = []
    for branch in BRANCHES:
        for trace in TRACING:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", branch,
                                   "trace" if trace else "plain"], cwd=ROOT, env=env,
                                  text=True, capture_output=True, check=True, timeout=180)
            runs.append(json.loads(proc.stdout))
    post = locked_inputs()
    keyed = {(r["branch"], r["traced"]): r for r in runs}
    parity = {}
    for branch in BRANCHES:
        plain, trace = keyed[(branch, False)], keyed[(branch, True)]
        parity[branch] = [a["terminal_graph_sha256"] == b["terminal_graph_sha256"]
                          for a, b in zip(plain["checkpoints"], trace["checkpoints"])]
    checks = {"six_fresh_worker_processes": len(runs) == 6 and len({r["pid"] for r in runs}) == 6,
              "locked_sources_unchanged_during_run": post == locked,
              "three_branches_and_trace_arms": len(keyed) == 6,
              "wildcard_refusal_before_scoped_call": all(r["target_rule_reads_any"] and all(
                  c["partition_execution"] == {"status": "refused_wildcard_rule_access", "scoped_calls": 0}
                  for c in r["checkpoints"]) for r in runs),
              "all_full_closures_fixed_and_terminal": all(c["closure_report"].get("status") == "fixed_point"
                  and c["terminal_probe"].get("status") == "fixed_point"
                  and c["terminal_probe"].get("progress_steps") == 0
                  and c["independent_residual_count"] == 0
                  for r in runs for c in r["checkpoints"]),
              "trace_on_off_terminal_parity": all(all(v) for v in parity),
              "reweight_identity_preserved": all(c.get("edge_identity_preserved") for r in runs
                  if r["branch"] == "reweight" for c in r["checkpoints"] if c["stage"] == "reweight_same_edge_identity"),
              "dialogue_mutation_cell_explicitly_unsupported": True}
    sensitivity = {branch: any(cp["closure_changed_graph"] or cp["closure_made_progress"]
                               for r in runs if r["branch"] == branch for cp in r["checkpoints"])
                   for branch in BRANCHES}
    payload = {"schema_version": 1, "run_id": "substrate-authored-bigville-cut-mutation-v1-20260926",
               "status": "capture_complete_but_mutation_semantics_inconclusive",
               "claim_boundary": "Fresh Bigville insertion/retraction/reweight capture; all candidate partition executions refuse on reads_any. Dialogue mutation seam is unsupported; no general tractability claim.",
               "locked_inputs": locked, "post_run_inputs": post,
               "environment": {"python": sys.version, "platform": platform.platform()},
               "checks": checks, "trace_on_off_terminal_parity": parity,
               "mutation_closure_sensitivity": sensitivity,
               "dialogue_mutation_cell": {"status": "unsupported_no_oracle_preserving_boundary_mutation_harness",
                                          "scoped_status": "refused_shared_state_on_40_task_global_incidences"},
               "runs": runs}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "trace_on_off_terminal_parity": parity}, indent=2))
    if not all(checks.values()):
        raise SystemExit("Bigville mutation diagnostic gate failed; preserve raw capture")


if __name__ == "__main__":
    main()
