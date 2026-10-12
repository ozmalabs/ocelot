#!/usr/bin/env python3
"""Exact-vs-approximate inference on the authored Bigville CAN cast.

Runs the current exact solver, max-product BP, and native 20-start rule
relaxation on each deterministic cast resident's five-concept CAN after the
shared authored scenario evidence. Exhaustive enumeration is the independent
MAP oracle (243 states per resident). This is authored project workload data,
not an externally observed or natural-world sample.
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
OUT = ROOT / "evaluation/reports/can_bigville_inference_envelope_20260925.json"
K_STARTS = 20
BP_MAX_ROUNDS = 40
BP_EPSILON = 1e-7
TREEWIDTH_BOUND = 4


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def med(values):
    return int(statistics.median(values))


def independent_energy(unary, pairwise, state):
    total = -sum(float(h) * float(state[i]) for i, h in unary.items())
    for pair, weight in pairwise.items():
        i, j = tuple(pair)
        total -= float(weight) * float(state[i]) * float(state[j])
    return total


def exhaustive_map(nodes, unary, pairwise, vocab):
    best_energy, best_state, checked = math.inf, None, 0
    for assignment in itertools.product(vocab, repeat=len(nodes)):
        state = dict(zip(nodes, assignment))
        energy = independent_energy(unary, pairwise, state)
        checked += 1
        if energy < best_energy:
            best_energy, best_state = energy, state
    return {"energy": best_energy, "state": best_state, "states_checked": checked}


def main():
    import substrate_rs as sr
    import domains.can_junction_tree as cjt
    from domains.can_native_bp import run_loopy_bp
    from domains.can_native_orchestration import (
        multi_start_settle_and_pick_best, native_audit_basin, scoped_settle,
    )
    from domains.graph_treewidth import min_fill_upper_bound
    from substrate.seed_loader import engine_rules_only
    from worlds import bigville_can_beliefs as bigville

    cast_path = ROOT / "seeds/bigville_cast100.json"
    cast = json.loads(cast_path.read_text(encoding="utf-8"))["residents"]
    records = []
    for resident in cast:
        index = int(resident["index"])
        s = sr.Substrate()
        inner = s._inner
        bigville.install_productions(inner)
        built = bigville.build_resident_can_mt(inner, resident)
        mt_ref = built["mt_node"]
        bigville.apply_scenario_evidence(inner, built["concepts"])
        inner.set_attr(mt_ref, "discrete_mode", "3state")
        inner.set_attr(mt_ref, "can_tick", 0.0)

        t0 = time.perf_counter_ns()
        net = cjt.can_network_from_mt(inner, mt_ref)
        extraction_ns = time.perf_counter_ns() - t0
        if len(net["nodes"]) != 5 or len(net["pairwise"]) != 5:
            raise AssertionError(f"resident {index}: expected authored 5-node/5-pair CAN")

        t0 = time.perf_counter_ns()
        width = min_fill_upper_bound(net["nodes"], net["edges"])
        width_ns = time.perf_counter_ns() - t0
        t0 = time.perf_counter_ns()
        jt = cjt.junction_tree_map(net["nodes"], net["edges"], net["unary"],
                                   net["pairwise"], net["vocab"],
                                   order=width["elimination_order"])
        exact_ns = time.perf_counter_ns() - t0
        t0 = time.perf_counter_ns()
        oracle = exhaustive_map(net["nodes"], net["unary"], net["pairwise"], net["vocab"])
        oracle_ns = time.perf_counter_ns() - t0
        if oracle["states_checked"] != 243 or abs(jt["energy"] - oracle["energy"]) > 1e-7:
            raise AssertionError(f"resident {index}: exact MAP disagrees with 243-state oracle")

        t0 = time.perf_counter_ns()
        bp = run_loopy_bp(inner, mt_ref, combine="max_product", max_rounds=BP_MAX_ROUNDS,
                          epsilon=BP_EPSILON, commit=False)
        bp_ns = time.perf_counter_ns() - t0
        bp_energy = independent_energy(net["unary"], net["pairwise"], bp["final_state"])

        t0 = time.perf_counter_ns()
        for path in ("seeds/can_native_reimplementation.json", "seeds/can_decay_identity.json"):
            with (ROOT / path).open(encoding="utf-8") as f:
                inner.load_seed_manifest(engine_rules_only(json.load(f)))
        rule_setup_ns = time.perf_counter_ns() - t0
        tracemalloc.start()
        t0 = time.perf_counter_ns()
        picked = multi_start_settle_and_pick_best(
            inner, mt_ref, k_starts=K_STARTS,
            rng=random.Random(20260925 + index * 7919))
        relax_ns = time.perf_counter_ns() - t0
        _, py_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        basin = native_audit_basin(inner, mt_ref)
        state = basin["marginal"]
        relax_energy = independent_energy(net["unary"], net["pairwise"], state)
        native_energy = float(inner.mt_energy(mt_ref, state))

        pre_probe = {cid: float(inner.node(concept)["attrs"].get("state", 0.0))
                     for topic, concept in built["concepts"].items()
                     for cid in [concept.value if hasattr(concept, "value") else int(concept)]}
        t0 = time.perf_counter_ns()
        terminal_steps = scoped_settle(inner, mt_ref)
        terminal_ns = time.perf_counter_ns() - t0
        post_probe = {cid: float(inner.node(concept)["attrs"].get("state", 0.0))
                      for topic, concept in built["concepts"].items()
                      for cid in [concept.value if hasattr(concept, "value") else int(concept)]}
        stable = terminal_steps == 0 and pre_probe == post_probe

        # Check that the solver's rule closure did not alter the model being
        # compared; state and bookkeeping nodes may change by design.
        after_net = cjt.can_network_from_mt(inner, mt_ref)
        network_preserved = (net["unary"] == after_net["unary"] and
                             net["pairwise"] == after_net["pairwise"] and
                             net["edges"] == after_net["edges"])
        records.append({
            "resident_index": index, "resident_name": resident["name"],
            "resolution_bins_trait": resident["params"]["resolution_bins"],
            "effective_bins": built["effective_bins"],
            "nodes": len(net["nodes"]), "undirected_pairs": len(net["pairwise"]),
            "treewidth_upper_bound": width["treewidth"],
            "ground_truth_states_enumerated": oracle["states_checked"],
            "exact_energy": float(jt["energy"]), "ground_truth_energy": float(oracle["energy"]),
            "exact_gap": float(jt["energy"] - oracle["energy"]),
            "bp_energy": bp_energy, "bp_gap": float(bp_energy - oracle["energy"]),
            "bp_converged": bool(bp["converged"]), "bp_rounds": int(bp["rounds"]),
            "multi_start_k": K_STARTS, "multi_start_energy": relax_energy,
            "multi_start_gap": float(relax_energy - oracle["energy"]),
            "multi_start_frustration": float(basin["frustration"]),
            "multi_start_winner_frustration": float(picked["frustration"]),
            "multi_start_candidate_count": len(picked["candidates"]),
            "multi_start_terminal_steps": int(terminal_steps),
            "multi_start_stable": stable, "input_network_preserved": network_preserved,
            "native_energy_gap": native_energy - relax_energy,
            "python_peak_traced_bytes": int(py_peak),
            "cost_ns": {"graph_extraction": extraction_ns, "min_fill_width": width_ns,
                        "junction_tree_map": exact_ns, "exhaustive_oracle": oracle_ns,
                        "max_product_bp": bp_ns, "rule_seed_setup": rule_setup_ns,
                        "multi_start_relaxation": relax_ns,
                        "terminal_stability_probe": terminal_ns},
        })
        print(f"resident={index:03d} bins={built['effective_bins']} tw<={width['treewidth']} "
              f"BP_gap={bp_energy-oracle['energy']:.3g} "
              f"multi_gap={relax_energy-oracle['energy']:.3g} stable={stable}", flush=True)

    source_files = [
        Path(__file__).resolve(), cast_path,
        ROOT / "worlds/bigville_can_beliefs.py",
        ROOT / "domains/can_junction_tree.py", ROOT / "domains/can_native_bp.py",
        ROOT / "domains/can_native_orchestration.py", ROOT / "domains/graph_treewidth.py",
        ROOT / "seeds/can_native_reimplementation.json", ROOT / "seeds/can_decay_identity.json",
    ]
    metrics = {
        "residents": len(records),
        "exact_optimal": sum(abs(r["exact_gap"]) <= 1e-7 for r in records),
        "bp_optimal": sum(abs(r["bp_gap"]) <= 1e-7 for r in records),
        "bp_converged": sum(r["bp_converged"] for r in records),
        "multi_start_optimal": sum(abs(r["multi_start_gap"]) <= 1e-7 for r in records),
        "multi_start_stable": sum(r["multi_start_stable"] for r in records),
        "multi_start_network_preserved": sum(r["input_network_preserved"] for r in records),
        "all_exact_width_bounds_at_most_gate": all(r["treewidth_upper_bound"] <= TREEWIDTH_BOUND for r in records),
        "median_bp_gap": statistics.median(r["bp_gap"] for r in records),
        "median_multi_start_gap": statistics.median(r["multi_start_gap"] for r in records),
        "median_cost_ns": {key: med([r["cost_ns"][key] for r in records])
                           for key in records[0]["cost_ns"]},
        "median_python_peak_traced_bytes": med([r["python_peak_traced_bytes"] for r in records]),
    }
    ext_path = Path(sr.__file__).resolve().parent / "_native.abi3.so"
    payload = {
        "schema_version": 1,
        "run_id": "can-bigville-inference-envelope-20260925",
        "claim_boundary": "Deterministic authored Bigville cast workload, not naturally sampled real-world data. Five concepts per resident and exhaustive 3^5 oracle; does not establish general CAN scaling, learned frame locality, or natural-task inference performance. Tracemalloc excludes native Rust memory.",
        "configuration": {"residents": len(records), "scenario_evidence": bigville.SCENARIO_EVIDENCE,
                          "multi_start_k": K_STARTS, "bp_max_rounds": BP_MAX_ROUNDS,
                          "bp_epsilon": BP_EPSILON, "treewidth_gate": TREEWIDTH_BOUND},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor()},
        "provenance": {"source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in source_files},
                       "native_extension_path": str(ext_path),
                       "native_extension_sha256": sha(ext_path)},
        "checks": {
            "all_junction_tree_matches_exhaustive": all(abs(r["exact_gap"]) <= 1e-7 for r in records),
            "all_native_energy_matches_independent_energy": all(abs(r["native_energy_gap"]) <= 1e-4 for r in records),
            "all_multi_start_have_20_candidates": all(r["multi_start_candidate_count"] == K_STARTS for r in records),
            "all_multi_start_reach_terminal_fixed_point": all(r["multi_start_stable"] for r in records),
            "all_multi_start_preserve_input_network": all(r["input_network_preserved"] for r in records),
            "all_widths_within_exact_gate": metrics["all_exact_width_bounds_at_most_gate"],
        },
        "summary": metrics,
        "runs": records,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"summary": metrics, "checks": payload["checks"], "output": str(OUT)}, indent=2))
    if not all(payload["checks"].values()):
        raise SystemExit("Bigville inference envelope invariant failed")


if __name__ == "__main__":
    main()
