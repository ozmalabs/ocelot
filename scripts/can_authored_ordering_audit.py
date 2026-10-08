#!/usr/bin/env python3
"""Audit guarded forest ordering on authored/runtime-generated CAN workloads."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import math
import platform
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/can_authored_ordering_audit_20260925.json"
WIDTH_GATE = 4
NATIVE_MODES = ("2state", "3state")
NATIVE_GRANULARITIES = (True, False)
NATIVE_REPLICATES = 20


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_fixture():
    path = ROOT / "tests/test_can_native_reimplementation.py"
    spec = importlib.util.spec_from_file_location("authored_can_fixture", path)
    module = importlib.util.module_from_spec(spec)
    if not spec or not spec.loader:
        raise RuntimeError("cannot import native CAN fixture")
    spec.loader.exec_module(module)
    return module


def edges_local(nodes, edges):
    local = {node: i for i, node in enumerate(nodes)}
    return sorted({tuple(sorted((local[a], local[b]))) for a, b in edges})


def forest_detector(n, edges):
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        if a == b:
            return False
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
    return True


def leaf_order(n, edges):
    from collections import deque
    adj = [set() for _ in range(n)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    degree = [len(x) for x in adj]
    queue = deque(i for i, d in enumerate(degree) if d <= 1)
    removed = [False] * n
    order = []
    while queue:
        v = queue.popleft()
        if removed[v]:
            continue
        removed[v] = True
        order.append(v)
        for u in adj[v]:
            if not removed[u]:
                degree[u] -= 1
                if degree[u] <= 1:
                    queue.append(u)
    if len(order) != n:
        raise ValueError("cyclic graph passed forest detector")
    return order


def exhaustive_map(nodes, unary, pairwise, vocab):
    best = math.inf
    best_state = None
    for values in itertools.product(vocab, repeat=len(nodes)):
        state = dict(zip(nodes, values))
        energy = -sum(unary[i] * state[i] for i in nodes)
        energy -= sum(weight * state[i] * state[j]
                      for pair, weight in pairwise.items()
                      for i, j in [tuple(pair)])
        if energy < best:
            best, best_state = energy, state
    return best, best_state


def assess_model(label, source, net, cjt, min_fill_upper_bound, triangulate, records):
    nodes = net["nodes"]
    local_edges = edges_local(nodes, net["edges"])
    t0 = time.perf_counter_ns()
    is_forest = forest_detector(len(nodes), local_edges)
    detect_ns = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    minfill = min_fill_upper_bound(list(range(len(nodes))), local_edges)
    minfill_ns = time.perf_counter_ns() - t0
    if is_forest:
        t0 = time.perf_counter_ns()
        local_order = leaf_order(len(nodes), local_edges)
        leaf_ns = time.perf_counter_ns() - t0
    else:
        local_order = minfill["elimination_order"]
        leaf_ns = 0
    selected = [nodes[i] for i in local_order]
    tri = triangulate(list(range(len(nodes))), local_edges, local_order)
    selected_width = max((len(bag) - 1 for bag in tri["bags"].values()), default=0)
    exact_gap = None
    oracle_states = 0
    map_ns = None
    if selected_width <= WIDTH_GATE:
        t0 = time.perf_counter_ns()
        answer = cjt.junction_tree_map(nodes, net["edges"], net["unary"], net["pairwise"],
                                       net["vocab"], order=selected)
        map_ns = time.perf_counter_ns() - t0
        oracle_energy, _ = exhaustive_map(nodes, net["unary"], net["pairwise"], net["vocab"])
        oracle_states = len(net["vocab"]) ** len(nodes)
        exact_gap = float(answer["energy"] - oracle_energy)
        if abs(exact_gap) > 1e-7:
            raise AssertionError(f"{label}: exact MAP disagrees with exhaustive oracle")
    records.append({
        "label": label, "source": source, "nodes": len(nodes), "edges": len(local_edges),
        "forest_detected": is_forest, "min_fill_width": minfill["treewidth"],
        "selected_order_width": selected_width, "exact_gate_admitted": selected_width <= WIDTH_GATE,
        "exact_energy_gap": exact_gap, "oracle_states": oracle_states,
        "timing_ns": {"forest_detector": detect_ns, "min_fill_order": minfill_ns,
                      "leaf_order": leaf_ns, "exact_map": map_ns},
    })


def main():
    import substrate_rs as sr
    import domains.can_junction_tree as cjt
    from domains.graph_treewidth import min_fill_upper_bound, build_elimination_triangulation
    from worlds import bigville_can_beliefs as bigville

    records = []
    cast_path = ROOT / "seeds/bigville_cast100.json"
    cast = json.loads(cast_path.read_text(encoding="utf-8"))["residents"]
    for resident in cast:
        s = sr.Substrate()
        inner = s._inner
        bigville.install_productions(inner)
        built = bigville.build_resident_can_mt(inner, resident)
        bigville.apply_scenario_evidence(inner, built["concepts"])
        inner.set_attr(built["mt_node"], "discrete_mode", "3state")
        net = cjt.can_network_from_mt(inner, built["mt_node"])
        assess_model(f"bigville:{resident['index']}", "authored_bigville", net, cjt,
                     min_fill_upper_bound, build_elimination_triangulation, records)

    fixture = load_fixture()
    closure_rows = []
    for mode in NATIVE_MODES:
        for coarse in NATIVE_GRANULARITIES:
            for rep in range(NATIVE_REPLICATES):
                seed = 1000 + rep
                substrate = fixture._loaded_substrate()
                inner = substrate._inner
                mt, _concepts = fixture._build_draw(substrate, seed, coarse, mode)
                converged, steps = fixture._discrete_async_converges(inner, 3000)
                terminal_steps = inner.run_rules(1)
                net = cjt.can_network_from_mt(inner, mt)
                label = f"native_can:{mode}:{int(coarse)}:{rep}"
                before = len(records)
                assess_model(label, "native_rule_generated", net, cjt,
                             min_fill_upper_bound, build_elimination_triangulation, records)
                closure_rows.append({
                    "label": label, "converged": bool(converged), "progress_steps": int(steps),
                    "terminal_steps": int(terminal_steps), "nodes": len(net["nodes"]),
                    "edges": records[before]["edges"],
                })

    # Explicit malformed/degenerate edge controls for the detector contract.
    malformed_cases = [
        {"name": "duplicate_undirected_edge", "n": 3, "edges": [(0, 1), (1, 2), (1, 0)],
         "expected_forest": False, "expected_action": "fallback"},
        {"name": "self_loop", "n": 3, "edges": [(0, 1), (1, 2), (2, 2)],
         "expected_forest": False, "expected_action": "fallback"},
        {"name": "out_of_range_endpoint", "n": 3, "edges": [(0, 1), (1, 3)],
         "expected_forest": None, "expected_action": "reject_before_ordering"},
        {"name": "negative_endpoint", "n": 3, "edges": [(0, 1), (-1, 2)],
         "expected_forest": None, "expected_action": "reject_before_ordering"},
    ]
    for case in malformed_cases:
        try:
            valid = all(isinstance(v, int) and not isinstance(v, bool) and 0 <= v < case["n"]
                        for edge in case["edges"] for v in edge)
            if not valid:
                raise ValueError("endpoint outside declared node range")
            result = forest_detector(case["n"], case["edges"])
            observed = {"status": "classified", "is_forest": result,
                        "action": "leaf_order" if result else "fallback"}
        except (IndexError, TypeError, ValueError) as exc:
            observed = {"status": "rejected", "is_forest": None,
                        "action": "reject_before_ordering", "reason": type(exc).__name__}
        case["observed"] = observed
        if case["expected_forest"] is not None and observed["is_forest"] != case["expected_forest"]:
            raise AssertionError(f"malformed control mismatch: {case['name']}")
        if observed["action"] != case["expected_action"]:
            raise AssertionError(f"malformed control action mismatch: {case['name']}")

    current = Path(__file__).resolve()
    sources = [
        current, ROOT / "scripts/can_guarded_forest_dispatch.py",
        ROOT / "tests/test_can_native_reimplementation.py",
        ROOT / "worlds/bigville_can_beliefs.py", cast_path,
        ROOT / "domains/can_junction_tree.py", ROOT / "domains/graph_treewidth.py",
        ROOT / "seeds/can_native_reimplementation.json",
        ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
        ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
    ]
    forest_records = [r for r in records if r["source"] == "authored_bigville"]
    native_records = [r for r in records if r["source"] == "native_rule_generated"]
    payload = {
        "schema_version": 1, "run_id": "can-authored-ordering-audit-20260925-v1",
        "scope": "guarded forest dispatch on authored Bigville and native-rule-generated CAN snapshots, plus malformed-edge policy controls",
        "claim_boundary": "Project-authored workload evidence only. Bigville is deterministically authored. Native CAN controls are generated from the selected test fixture and are complete graphs. No natural-world forest prevalence or production dispatch is established.",
        "configuration": {"bigville_residents": len(forest_records),
                          "native_can_conditions": len(native_records),
                          "native_modes": NATIVE_MODES, "weight_granularity": NATIVE_GRANULARITIES,
                          "replicates_per_mode_granularity": NATIVE_REPLICATES,
                          "exact_width_gate": WIDTH_GATE},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor()},
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in sources},
        "checks": {
            "bigville_exact_oracles_match": all(r["exact_energy_gap"] is not None and
                                                  abs(r["exact_energy_gap"]) <= 1e-7
                                                  for r in forest_records),
            "bigville_forests_use_leaf_order": all(r["selected_order_width"] <= 1
                                                    for r in forest_records if r["forest_detected"]),
            "native_closures_settle": all(r["converged"] and r["terminal_steps"] == 0
                                           for r in closure_rows),
            "native_complete_graphs_fall_back_and_refuse": all(
                not r["forest_detected"] and not r["exact_gate_admitted"] and
                r["min_fill_width"] == 7 for r in native_records),
            "malformed_controls_match_policy": all(c["observed"]["action"] == c["expected_action"]
                                                    for c in malformed_cases),
            "all_records_accounted": len(records) == len(forest_records) + len(native_records),
        },
        "summary": {
            "bigville_forest_count": sum(r["forest_detected"] for r in forest_records),
            "bigville_nonforest_count": sum(not r["forest_detected"] for r in forest_records),
            "bigville_exact_admitted": sum(r["exact_gate_admitted"] for r in forest_records),
            "native_forest_count": sum(r["forest_detected"] for r in native_records),
            "native_width_refusals": sum(not r["exact_gate_admitted"] for r in native_records),
            "median_bigville_min_fill_ns": int(statistics.median(r["timing_ns"]["min_fill_order"] for r in forest_records)),
            "median_bigville_detector_ns": int(statistics.median(r["timing_ns"]["forest_detector"] for r in forest_records)),
        },
        "malformed_controls": malformed_cases, "native_closure_checks": closure_rows,
        "runs": records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"runs": len(records), "checks": payload["checks"],
                      "summary": payload["summary"], "output": str(OUT)}, indent=2))
    if not all(payload["checks"].values()):
        raise SystemExit("authored ordering audit failed")


if __name__ == "__main__":
    main()
