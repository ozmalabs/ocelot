#!/usr/bin/env python3
"""Paired CAN inference cost and quality envelope.

Builds deterministic native graph snapshots, extracts each into the current
CAN network representation, and compares exact MAP, max-product loopy BP,
and native multi-start relaxation against exhaustive MAP. The mutating
relaxation runs on a separate identical substrate.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import platform
import random
import statistics
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/can_inference_cost_quality_envelope_20260925.json"
SIZES = (5, 7, 9)
FAMILIES = ("path", "cycle", "complete", "sparse_random")
REPLICATES = 2
TREEWIDTH_BOUND = 4
BP_MAX_ROUNDS = 40
BP_EPSILON = 1e-7
MULTI_START_K = 20
VOCAB = (-1.0, 0.0, 1.0)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_edges(n: int, family: str, seed: int) -> list[tuple[int, int]]:
    if family == "path":
        return [(i, i + 1) for i in range(n - 1)]
    if family == "cycle":
        return [(i, i + 1) for i in range(n - 1)] + ([(0, n - 1)] if n > 2 else [])
    if family == "complete":
        return [(i, j) for i in range(n) for j in range(i + 1, n)]
    if family == "sparse_random":
        rng = random.Random(seed + 31)
        p = min(1.0, 2.8 / max(n - 1, 1))
        return [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p]
    raise ValueError(f"unknown family {family}")


def make_values(n: int, edges: list[tuple[int, int]], seed: int):
    rng = random.Random(seed)
    unary = {i: round(rng.uniform(-1.0, 1.0) * 4) / 4 for i in range(n)}
    pairwise = {frozenset((i, j)): round(rng.uniform(-1.0, 1.0) * 2) / 2
                for i, j in edges}
    return unary, pairwise


def independent_energy(unary, pairwise, state) -> float:
    total = -sum(float(h) * float(state[i]) for i, h in unary.items())
    for pair, weight in pairwise.items():
        i, j = tuple(pair)
        total -= float(weight) * float(state[i]) * float(state[j])
    return total


def exhaustive_map(nodes, unary, pairwise):
    best_energy = math.inf
    best_state = None
    checked = 0
    for values in itertools.product(VOCAB, repeat=len(nodes)):
        state = dict(zip(nodes, values))
        energy = independent_energy(unary, pairwise, state)
        checked += 1
        if energy < best_energy:
            best_energy, best_state = energy, state
    return {"energy": best_energy, "state": best_state, "states_checked": checked}


def build_substrate(sr, n, edges, unary, pairwise):
    substrate = sr.Substrate()
    inner = substrate._inner
    mt = inner.add_node("Microtheory", {"temperature": 2.0, "discrete_mode": "3state"})
    concepts = [inner.add_node("Concept", {
        "name": f"x{i}", "state": 0.0,
        "external_field": float(unary[i]), "identity_field": 0.0,
    }) for i in range(n)]
    for node in concepts:
        inner.add_edge_unchecked(mt, "has_concept", node, {})
    for i, j in edges:
        weight = float(pairwise[frozenset((i, j))])
        inner.add_edge_unchecked(concepts[i], "causal_influence", concepts[j], {"weight": weight})
        inner.add_edge_unchecked(concepts[j], "causal_influence", concepts[i], {"weight": weight})
    return substrate, mt, concepts


def graph_state(substrate, concepts):
    return [float(substrate.node(n)["attrs"].get("state", 0.0)) for n in concepts]


def median(rows, field):
    return int(statistics.median(r["cost_ns"][field] for r in rows))


def native_seeded_relaxation(sr, n, edges, unary, pairwise, seed):
    """Run ordinary seeded CAN relaxation on an isolated identical graph."""
    from substrate.seed_loader import engine_rules_only
    from domains.can_native_orchestration import (
        multi_start_settle_and_pick_best, native_audit_basin, scoped_settle,
    )
    from domains.can_junction_tree import can_network_from_mt

    substrate, mt, concepts = build_substrate(sr, n, edges, unary, pairwise)
    inner = substrate._inner
    before_net = can_network_from_mt(substrate, mt)
    t0 = time.perf_counter_ns()
    for path in ("seeds/can_native_reimplementation.json", "seeds/can_decay_identity.json"):
        with (ROOT / path).open(encoding="utf-8") as f:
            inner.load_seed_manifest(engine_rules_only(json.load(f)))
    setup_ns = time.perf_counter_ns() - t0

    tracemalloc.start()
    t0 = time.perf_counter_ns()
    picked = multi_start_settle_and_pick_best(
        inner, mt, k_starts=MULTI_START_K,
        rng=random.Random(seed ^ 0x5A17C0DE))
    relax_ns = time.perf_counter_ns() - t0
    _, py_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    basin = native_audit_basin(inner, mt)
    state = basin["marginal"]
    after_net = can_network_from_mt(substrate, mt)
    structure_preserved = (after_net["unary"] == before_net["unary"] and
                           after_net["pairwise"] == before_net["pairwise"] and
                           after_net["edges"] == before_net["edges"])
    before_probe = graph_state(substrate, concepts)
    t0 = time.perf_counter_ns()
    terminal_steps = scoped_settle(inner, mt)
    probe_ns = time.perf_counter_ns() - t0
    after_probe = graph_state(substrate, concepts)
    return {
        "state": state,
        "energy": float(inner.mt_energy(mt, state)),
        "frustration": float(basin["frustration"]),
        "winner_frustration": float(picked["frustration"]),
        "candidate_count": len(picked["candidates"]),
        "input_network_preserved": structure_preserved,
        "terminal_steps": int(terminal_steps),
        "stable_at_terminal_probe": terminal_steps == 0 and before_probe == after_probe,
        "python_peak_traced_bytes": int(py_peak),
        "cost_ns": {"seed_load_setup": setup_ns, "multi_start_relaxation": relax_ns,
                    "terminal_stability_probe": probe_ns},
    }


def main() -> None:
    import substrate_rs as sr
    import domains.can_junction_tree as cjt
    from domains.can_native_bp import run_loopy_bp
    from domains.graph_treewidth import min_fill_upper_bound, build_elimination_triangulation

    records = []
    for n in SIZES:
        for family in FAMILIES:
            for rep in range(REPLICATES):
                seed = 20260925 + n * 100 + rep * 17 + FAMILIES.index(family) * 1000
                source_edges = make_edges(n, family, seed)
                source_unary, source_pairwise = make_values(n, source_edges, seed + 7)
                substrate, mt, concepts = build_substrate(sr, n, source_edges,
                                                          source_unary, source_pairwise)
                before_state = graph_state(substrate, concepts)

                t0 = time.perf_counter_ns()
                net = cjt.can_network_from_mt(substrate, mt)
                extraction_ns = time.perf_counter_ns() - t0
                if len(net["nodes"]) != n or len(net["pairwise"]) != len(source_edges):
                    raise AssertionError("native-to-CAN snapshot extraction lost nodes or pairs")

                t0 = time.perf_counter_ns()
                width = min_fill_upper_bound(net["nodes"], net["edges"])
                width_ns = time.perf_counter_ns() - t0
                order = width["elimination_order"]

                t0 = time.perf_counter_ns()
                tri = build_elimination_triangulation(net["nodes"], net["edges"], order)
                triangulation_ns = time.perf_counter_ns() - t0
                if max(len(bag) for bag in tri["bags"].values()) - 1 != width["treewidth"]:
                    raise AssertionError("treewidth and triangulation bag size disagree")

                # Split triangulation from the remainder of the exact map pass
                # by timing the exact call's own triangulation invocation.
                exact_tree_ns = 0
                original_builder = cjt.build_elimination_triangulation

                def timed_builder(*args, **kwargs):
                    nonlocal exact_tree_ns
                    start = time.perf_counter_ns()
                    value = original_builder(*args, **kwargs)
                    exact_tree_ns += time.perf_counter_ns() - start
                    return value

                cjt.build_elimination_triangulation = timed_builder
                try:
                    t0 = time.perf_counter_ns()
                    jt = cjt.junction_tree_map(net["nodes"], net["edges"], net["unary"],
                                               net["pairwise"], net["vocab"], order=order)
                    jt_total_ns = time.perf_counter_ns() - t0
                finally:
                    cjt.build_elimination_triangulation = original_builder
                jt_message_backtrack_ns = max(0, jt_total_ns - exact_tree_ns)

                t0 = time.perf_counter_ns()
                ground_truth = exhaustive_map(net["nodes"], net["unary"], net["pairwise"])
                ground_truth_ns = time.perf_counter_ns() - t0
                jt_gap = float(jt["energy"] - ground_truth["energy"])
                if abs(jt_gap) > 1e-7:
                    raise AssertionError(f"junction-tree disagrees with enumeration by {jt_gap}")

                t0 = time.perf_counter_ns()
                integrated = cjt.junction_tree_exact_settle(
                    substrate, mt, treewidth_bound=TREEWIDTH_BOUND,
                    max_exact_n=0, commit=False)
                integrated_ns = time.perf_counter_ns() - t0
                if integrated["attempted"]:
                    integrated_gap = independent_energy(net["unary"], net["pairwise"],
                                                        integrated["state"])-ground_truth["energy"]
                    if abs(integrated_gap) > 1e-7:
                        raise AssertionError("integrated exact path disagrees with ground truth")
                else:
                    integrated_gap = None
                    if width["treewidth"] <= TREEWIDTH_BOUND:
                        raise AssertionError("width gate refused a graph inside its bound")

                t0 = time.perf_counter_ns()
                bp = run_loopy_bp(substrate, mt, combine="max_product",
                                  max_rounds=BP_MAX_ROUNDS, epsilon=BP_EPSILON,
                                  commit=False)
                bp_ns = time.perf_counter_ns() - t0
                bp_energy = independent_energy(net["unary"], net["pairwise"], bp["final_state"])
                bp_gap = float(bp_energy - ground_truth["energy"])

                relax = native_seeded_relaxation(
                    sr, n, source_edges, source_unary, source_pairwise, seed)
                relax_energy = independent_energy(net["unary"], net["pairwise"],
                                                  relax["state"])
                relax_gap = float(relax_energy - ground_truth["energy"])
                relax_native_energy_gap = float(relax["energy"] - relax_energy)

                native_energy = float(substrate._inner.mt_energy(mt, ground_truth["state"]))
                native_energy_gap = native_energy - ground_truth["energy"]
                if abs(native_energy_gap) > 1e-4:
                    raise AssertionError("independent objective mismatches native mt_energy")
                after_state = graph_state(substrate, concepts)
                if after_state != before_state:
                    raise AssertionError("noncommitting solver path mutated graph state")

                records.append({
                    "nodes": n, "family": family, "replicate": rep, "seed": seed,
                    "source_edge_count": len(source_edges),
                    "extracted_edge_count": len(net["pairwise"]),
                    "domain_size": len(net["vocab"]),
                    "ground_truth_states_enumerated": ground_truth["states_checked"],
                    "treewidth_upper_bound": width["treewidth"],
                    "max_bag_size": jt["max_bag_size"],
                    "width_gate_bound": TREEWIDTH_BOUND,
                    "integrated_exact_attempted": integrated["attempted"],
                    "integrated_exact_gap": integrated_gap,
                    "junction_tree_energy": jt["energy"],
                    "ground_truth_energy": ground_truth["energy"],
                    "junction_tree_gap": jt_gap,
                    "bp_converged": bp["converged"],
                    "bp_rounds": bp["rounds"],
                    "bp_max_delta": bp["max_delta_history"][-1],
                    "bp_energy": bp_energy,
                    "bp_gap": bp_gap,
                    "multi_start_k": MULTI_START_K,
                    "multi_start_energy": relax_energy,
                    "multi_start_gap": relax_gap,
                    "multi_start_native_energy_gap": relax_native_energy_gap,
                    "multi_start_frustration": relax["frustration"],
                    "multi_start_winner_frustration": relax["winner_frustration"],
                    "multi_start_candidate_count": relax["candidate_count"],
                    "multi_start_input_network_preserved": relax["input_network_preserved"],
                    "multi_start_terminal_steps": relax["terminal_steps"],
                    "multi_start_stable_at_terminal_probe": relax["stable_at_terminal_probe"],
                    "multi_start_python_peak_traced_bytes": relax["python_peak_traced_bytes"],
                    "native_energy_gap": native_energy_gap,
                    "graph_mutated": after_state != before_state,
                    "cost_ns": {
                        "graph_extraction": extraction_ns,
                        "min_fill_width": width_ns,
                        "standalone_triangulation": triangulation_ns,
                        "jt_triangulation_inside_map": exact_tree_ns,
                        "jt_message_and_backtrack": jt_message_backtrack_ns,
                        "jt_map_total": jt_total_ns,
                        "integrated_width_gated_exact": integrated_ns,
                        "exhaustive_ground_truth": ground_truth_ns,
                        "max_product_bp": bp_ns,
                        "multi_start_seed_load_setup": relax["cost_ns"]["seed_load_setup"],
                        "multi_start_relaxation": relax["cost_ns"]["multi_start_relaxation"],
                        "multi_start_terminal_probe": relax["cost_ns"]["terminal_stability_probe"],
                    },
                })
                print(f"n={n} {family} rep={rep+1}/{REPLICATES} "
                      f"tw<={width['treewidth']} exact={integrated['attempted']} "
                      f"bp={bp['converged']} gap={bp_gap:.3g}", flush=True)

    summaries = []
    for n in SIZES:
        for family in FAMILIES:
            group = [r for r in records if r["nodes"] == n and r["family"] == family]
            if not group:
                continue
            summaries.append({
                "nodes": n, "family": family, "replicates": len(group),
                "source_edges": group[0]["source_edge_count"],
                "width_bounds": sorted({r["treewidth_upper_bound"] for r in group}),
                "exact_attempts": sum(r["integrated_exact_attempted"] for r in group),
                "bp_converged": sum(r["bp_converged"] for r in group),
                "bp_optimal_count": sum(abs(r["bp_gap"]) <= 1e-7 for r in group),
                "bp_gap_median": statistics.median(r["bp_gap"] for r in group),
                "bp_gap_max": max(r["bp_gap"] for r in group),
                "multi_start_candidates_per_case": sorted({r["multi_start_candidate_count"] for r in group}),
                "multi_start_terminal_stable": sum(r["multi_start_stable_at_terminal_probe"] for r in group),
                "multi_start_optimal_count": sum(abs(r["multi_start_gap"]) <= 1e-7 for r in group),
                "multi_start_gap_median": statistics.median(r["multi_start_gap"] for r in group),
                "multi_start_gap_max": max(r["multi_start_gap"] for r in group),
                "median_cost_ns": {key: median(group, key) for key in group[0]["cost_ns"]},
            })
    source_files = [
        ROOT / "domains/can_junction_tree.py",
        ROOT / "domains/can_native_bp.py",
        ROOT / "domains/can_native_orchestration.py",
        ROOT / "domains/graph_treewidth.py",
        ROOT / "seeds/can_native_reimplementation.json",
        ROOT / "seeds/can_decay_identity.json",
    ]
    payload = {
        "schema_version": 1,
        "run_id": "can-inference-cost-quality-envelope-20260925",
        "method": "paired synthetic native CAN graph snapshots; exact MAP, integrated width gate, max-product BP, and seeded native 20-start relaxation; independent exhaustive MAP oracle; mutating relaxation isolated on an identical substrate",
        "claim_boundary": "Small synthetic Ising/CAN workloads only. Does not establish natural task inference quality, large-width scaling, frame locality, or general capability. Python tracemalloc does not include native Rust allocations or process peak RSS.",
        "configuration": {"sizes": SIZES, "families": FAMILIES, "replicates": REPLICATES,
                          "treewidth_bound": TREEWIDTH_BOUND, "bp_max_rounds": BP_MAX_ROUNDS,
                          "bp_epsilon": BP_EPSILON, "multi_start_k": MULTI_START_K,
                          "vocabulary": VOCAB},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor()},
        "provenance": {"script_sha256": sha(Path(__file__).resolve()),
                       "sources_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in source_files}},
        "checks": {
            "all_junction_tree_results_match_exhaustive": all(abs(r["junction_tree_gap"]) <= 1e-7 for r in records),
            "all_native_energy_scores_match_independent_objective": all(abs(r["native_energy_gap"]) <= 1e-4 for r in records),
            "all_noncommitting_runs_preserve_graph_state": all(not r["graph_mutated"] for r in records),
            "all_multi_start_runs_use_requested_candidate_count": all(
                r["multi_start_candidate_count"] == MULTI_START_K for r in records),
            "all_multi_start_native_energies_match_independent_objective": all(
                abs(r["multi_start_native_energy_gap"]) <= 1e-4 for r in records),
            "all_multi_start_runs_reach_terminal_fixed_points": all(
                r["multi_start_stable_at_terminal_probe"] for r in records),
            "all_multi_start_runs_preserve_input_energy_network": all(
                r["multi_start_input_network_preserved"] for r in records),
            "width_refusal_matches_bound": all(r["integrated_exact_attempted"] ==
                                                (r["treewidth_upper_bound"] <= TREEWIDTH_BOUND)
                                                for r in records),
        },
        "summaries": summaries,
        "runs": records,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"runs": len(records), "checks": payload["checks"], "output": str(OUT)}, indent=2))
    if not all(payload["checks"].values()):
        raise SystemExit("inference quality/cost envelope invariant failed")


if __name__ == "__main__":
    main()
