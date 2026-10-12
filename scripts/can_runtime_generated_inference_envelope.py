#!/usr/bin/env python3
"""Compare CAN inference on snapshots produced by the authored native rules.

Reuses the N=8 graph constructor from test_can_native_reimplementation.py,
executes its native discrete-async closure, then compares its fixed network's
settled state, exact MAP, max-product BP, and native 20-start relaxation
against an independently coded exhaustive energy oracle.
"""
from __future__ import annotations

import hashlib
import importlib.util
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
TEST = ROOT / "tests/test_can_native_reimplementation.py"
OUT = ROOT / "evaluation/reports/can_runtime_generated_inference_envelope_20260925.json"
MODES = ("2state", "3state")
GRANULARITIES = (True, False)
REPLICATES = 20
K_STARTS = 20
MAX_NATIVE_STEPS = 3000
BP_MAX_ROUNDS = 40
BP_EPSILON = 1e-7


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_energy(unary, pairwise, state):
    value = -sum(float(h) * float(state[i]) for i, h in unary.items())
    for pair, weight in pairwise.items():
        i, j = tuple(pair)
        value -= float(weight) * float(state[i]) * float(state[j])
    return value


def exhaustive_map(nodes, unary, pairwise, vocab):
    best, best_state, count = math.inf, None, 0
    for assignment in itertools.product(vocab, repeat=len(nodes)):
        state = dict(zip(nodes, assignment))
        score = independent_energy(unary, pairwise, state)
        count += 1
        if score < best:
            best, best_state = score, state
    return {"energy": best, "state": best_state, "states_checked": count}


def med(values):
    return int(statistics.median(values))


def main():
    import substrate_rs as sr
    import domains.can_junction_tree as cjt
    from domains.can_native_bp import run_loopy_bp
    from domains.can_native_orchestration import (
        multi_start_settle_and_pick_best, native_audit_basin, scoped_settle,
    )
    from domains.graph_treewidth import min_fill_upper_bound

    spec = importlib.util.spec_from_file_location("authored_can_fixture", TEST)
    fixture = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(fixture)

    records = []
    for mode in MODES:
        for coarse in GRANULARITIES:
            for replicate in range(REPLICATES):
                seed = 1000 + replicate
                substrate = fixture._loaded_substrate()
                inner = substrate._inner
                mt, concepts = fixture._build_draw(substrate, seed, coarse, mode)

                t0 = time.perf_counter_ns()
                converged, native_steps = fixture._discrete_async_converges(
                    inner, MAX_NATIVE_STEPS)
                native_closure_ns = time.perf_counter_ns() - t0
                baseline_state = fixture._read_states(inner, concepts)
                t0 = time.perf_counter_ns()
                native_terminal_steps = inner.run_rules(1)
                native_terminal_ns = time.perf_counter_ns() - t0

                net = cjt.can_network_from_mt(inner, mt)
                expected_nodes = len(concepts)
                expected_pairs = expected_nodes * (expected_nodes - 1) // 2
                if len(net["nodes"]) != expected_nodes or len(net["pairwise"]) != expected_pairs:
                    raise AssertionError("authored workload closure changed the expected complete topology")
                width = min_fill_upper_bound(net["nodes"], net["edges"])

                t0 = time.perf_counter_ns()
                exact = cjt.junction_tree_map(net["nodes"], net["edges"], net["unary"],
                                              net["pairwise"], net["vocab"],
                                              order=width["elimination_order"])
                exact_ns = time.perf_counter_ns() - t0
                t0 = time.perf_counter_ns()
                oracle = exhaustive_map(net["nodes"], net["unary"], net["pairwise"], net["vocab"])
                oracle_ns = time.perf_counter_ns() - t0
                exact_gap = float(exact["energy"] - oracle["energy"])
                if abs(exact_gap) > 1e-7:
                    raise AssertionError("junction-tree MAP disagrees with independent exhaustive oracle")

                baseline_energy = independent_energy(net["unary"], net["pairwise"], baseline_state)
                t0 = time.perf_counter_ns()
                bp = run_loopy_bp(substrate, mt, combine="max_product",
                                  max_rounds=BP_MAX_ROUNDS, epsilon=BP_EPSILON,
                                  discrete_mode=mode, commit=False)
                bp_ns = time.perf_counter_ns() - t0
                bp_energy = independent_energy(net["unary"], net["pairwise"], bp["final_state"])

                tracemalloc.start()
                t0 = time.perf_counter_ns()
                picked = multi_start_settle_and_pick_best(
                    inner, mt, k_starts=K_STARTS,
                    rng=random.Random(20260925 + seed * 104729 + int(coarse)))
                multi_ns = time.perf_counter_ns() - t0
                _, py_peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                basin = native_audit_basin(inner, mt)
                multi_state = basin["marginal"]
                multi_energy = independent_energy(net["unary"], net["pairwise"], multi_state)
                native_energy = float(inner.mt_energy(mt, multi_state))
                before_probe = fixture._read_states(inner, concepts)
                t0 = time.perf_counter_ns()
                multi_terminal_steps = scoped_settle(inner, mt)
                multi_probe_ns = time.perf_counter_ns() - t0
                after_probe = fixture._read_states(inner, concepts)
                multi_stable = multi_terminal_steps == 0 and before_probe == after_probe

                after_net = cjt.can_network_from_mt(inner, mt)
                model_preserved = (net["unary"] == after_net["unary"] and
                                   net["pairwise"] == after_net["pairwise"] and
                                   net["edges"] == after_net["edges"])
                expected_states = len(net["vocab"]) ** expected_nodes
                valid_vocab = all(v in net["vocab"] for v in baseline_state.values())
                rows = {
                    "mode": mode, "coarse_weights": bool(coarse),
                    "weight_granularity": 1.0 if coarse else 0.25,
                    "seed": seed, "nodes": expected_nodes,
                    "directed_edges": expected_nodes * (expected_nodes - 1),
                    "undirected_pairs": len(net["pairwise"]),
                    "treewidth_upper_bound": width["treewidth"],
                    "domain_size": len(net["vocab"]),
                    "oracle_states_enumerated": oracle["states_checked"],
                    "expected_oracle_states": expected_states,
                    "native_closure_converged": converged,
                    "native_closure_steps": native_steps,
                    "native_terminal_steps": native_terminal_steps,
                    "baseline_energy": baseline_energy,
                    "baseline_gap": float(baseline_energy - oracle["energy"]),
                    "exact_gap": exact_gap,
                    "bp_converged": bool(bp["converged"]),
                    "bp_rounds": int(bp["rounds"]),
                    "bp_gap": float(bp_energy - oracle["energy"]),
                    "multi_start_candidates": len(picked["candidates"]),
                    "multi_start_gap": float(multi_energy - oracle["energy"]),
                    "multi_start_frustration": float(basin["frustration"]),
                    "multi_start_winner_frustration": float(picked["frustration"]),
                    "multi_start_terminal_steps": multi_terminal_steps,
                    "multi_start_stable": multi_stable,
                    "input_model_preserved": model_preserved,
                    "native_energy_gap": native_energy - multi_energy,
                    "baseline_state_vocab_valid": valid_vocab,
                    "python_peak_traced_bytes": int(py_peak),
                    "cost_ns": {
                        "native_rule_closure": native_closure_ns,
                        "native_terminal_probe": native_terminal_ns,
                        "graph_extraction": 0,  # extraction is performed once below; see extraction field
                        "min_fill_width": 0,
                        "junction_tree_map": exact_ns,
                        "exhaustive_oracle": oracle_ns,
                        "max_product_bp": bp_ns,
                        "multi_start_relaxation": multi_ns,
                        "multi_start_terminal_probe": multi_probe_ns,
                    },
                }
                # Time the common snapshot operations explicitly for reproducibility.
                t0 = time.perf_counter_ns()
                _ = cjt.can_network_from_mt(inner, mt)
                rows["cost_ns"]["graph_extraction"] = time.perf_counter_ns() - t0
                t0 = time.perf_counter_ns()
                _ = min_fill_upper_bound(net["nodes"], net["edges"])
                rows["cost_ns"]["min_fill_width"] = time.perf_counter_ns() - t0
                rows["ground_truth_energy"] = float(oracle["energy"])
                records.append(rows)
                print(f"mode={mode} gran={rows['weight_granularity']} seed={seed} "
                      f"tw<={width['treewidth']} baseline={rows['baseline_gap']:.3g} "
                      f"BP={rows['bp_gap']:.3g} multi={rows['multi_start_gap']:.3g}", flush=True)

    summaries = []
    for mode in MODES:
        for coarse in GRANULARITIES:
            group = [r for r in records if r["mode"] == mode and r["coarse_weights"] == coarse]
            summaries.append({
                "mode": mode, "weight_granularity": 1.0 if coarse else 0.25,
                "runs": len(group), "all_native_converged": all(r["native_closure_converged"] for r in group),
                "all_terminal_fixed_points": all(r["native_terminal_steps"] == 0 and r["multi_start_stable"] for r in group),
                "baseline_optimal": sum(abs(r["baseline_gap"]) <= 1e-7 for r in group),
                "bp_optimal": sum(abs(r["bp_gap"]) <= 1e-7 for r in group),
                "bp_converged": sum(r["bp_converged"] for r in group),
                "multi_start_optimal": sum(abs(r["multi_start_gap"]) <= 1e-7 for r in group),
                "median_baseline_gap": statistics.median(r["baseline_gap"] for r in group),
                "median_bp_gap": statistics.median(r["bp_gap"] for r in group),
                "median_multi_start_gap": statistics.median(r["multi_start_gap"] for r in group),
                "median_cost_ns": {k: med([r["cost_ns"][k] for r in group]) for k in group[0]["cost_ns"]},
                "median_python_peak_traced_bytes": med([r["python_peak_traced_bytes"] for r in group]),
            })

    source_files = [
        Path(__file__).resolve(), TEST,
        ROOT / "domains/can_junction_tree.py", ROOT / "domains/can_native_bp.py",
        ROOT / "domains/can_native_orchestration.py", ROOT / "domains/graph_treewidth.py",
        ROOT / "seeds/can_native_reimplementation.json",
    ]
    ext_path = Path(sr.__file__).resolve().parent / "_native.abi3.so"
    payload = {
        "schema_version": 1,
        "run_id": "can-runtime-generated-inference-envelope-20260925",
        "scope": "80 post-native-rule-closure N=8 complete CAN snapshots from the authored 2state/3state × coarse/fine workload",
        "claim_boundary": "Authored synthetic workload whose graph state is produced by the current native rule engine. Does not establish natural task distributions, hierarchy locality, or large graph scaling. Python tracemalloc excludes native memory.",
        "configuration": {"modes": MODES, "weight_granularities": [1.0, 0.25],
                          "replicates_per_cell": REPLICATES, "multi_start_k": K_STARTS,
                          "native_step_cap": MAX_NATIVE_STEPS, "bp_max_rounds": BP_MAX_ROUNDS,
                          "bp_epsilon": BP_EPSILON, "production_exact_width_gate": 4,
                          "exact_mode": "direct junction_tree_map, diagnostic only; complete N=8 width 7 is above production gate but within 3^8 exhaustive-oracle envelope"},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor()},
        "provenance": {"source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in source_files},
                       "native_extension_path": str(ext_path), "native_extension_sha256": sha(ext_path)},
        "checks": {
            "all_native_closures_converged": all(r["native_closure_converged"] for r in records),
            "all_native_terminal_probes_zero": all(r["native_terminal_steps"] == 0 for r in records),
            "all_baseline_vocabularies_valid": all(r["baseline_state_vocab_valid"] for r in records),
            "all_junction_tree_results_match_independent_oracle": all(abs(r["exact_gap"]) <= 1e-7 for r in records),
            "all_oracle_state_counts_correct": all(r["oracle_states_enumerated"] == r["expected_oracle_states"] for r in records),
            "all_multi_start_runs_have_20_candidates": all(r["multi_start_candidates"] == K_STARTS for r in records),
            "all_multi_start_runs_stable": all(r["multi_start_stable"] for r in records),
            "all_multi_start_runs_preserve_input_model": all(r["input_model_preserved"] for r in records),
            "all_native_energy_matches_independent_objective": all(abs(r["native_energy_gap"]) <= 1e-4 for r in records),
        },
        "summaries": summaries, "runs": records,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"runs": len(records), "summaries": summaries,
                      "checks": payload["checks"], "output": str(OUT)}, indent=2))
    if not all(payload["checks"].values()):
        raise SystemExit("runtime-generated inference invariant failed")


if __name__ == "__main__":
    main()
