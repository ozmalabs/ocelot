#!/usr/bin/env python3
"""Measure exact inference via small shared separators and frame-local factors.

Builds modular pairwise CAN snapshots from clique factors over one shared
separator plus each frame's private interior. Compares native junction-tree
MAP with an independent conditional-frame enumeration that enumerates the
separator assignment and solves each frame interior independently.
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
OUT = ROOT / "evaluation/reports/can_separator_factorization_envelope_20260925.json"
FRAME_COUNTS = (2, 4, 8)
FRAME_INTERIORS = (2, 4)
SEPARATOR_SIZES = (0, 1, 2, 3)
DOMAIN_SIZES = (2, 3)
REPLICATES = 2
VOCAB_BY_D = {2: (-1.0, 1.0), 3: (-1.0, 0.0, 1.0)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def independent_energy(unary, pairwise, state):
    total = -sum(float(h) * float(state[i]) for i, h in unary.items())
    for pair, weight in pairwise.items():
        i, j = tuple(pair)
        total -= float(weight) * float(state[i]) * float(state[j])
    return total


def make_problem(frames, interior_size, separator_size, domain_size, seed):
    sep = list(range(separator_size))
    next_id = separator_size
    interiors = []
    for _ in range(frames):
        ids = list(range(next_id, next_id + interior_size))
        next_id += interior_size
        interiors.append(ids)
    nodes = list(range(next_id))
    pairwise = {}
    # Each local factor is a complete graph over S union I_f. No private
    # interior variable is coupled directly to another frame's interior.
    for ids in interiors:
        local = sep + ids
        for pos, i in enumerate(local):
            for j in local[pos + 1:]:
                pairwise[frozenset((i, j))] = 0.25 * random.Random(
                    seed + i * 65537 + j * 257).randint(-4, 4)
    rng = random.Random(seed ^ 0x51A7)
    unary = {i: 0.25 * rng.randint(-4, 4) for i in nodes}
    return nodes, sep, interiors, unary, pairwise


def conditional_frame_map(sep, interiors, unary, pairwise, vocab):
    """Exact MAP by conditioning the shared boundary, then solving frames."""
    best_total, best_state = math.inf, None
    states_checked = 0
    factor_evaluations = 0
    sep_set = set(sep)
    sep_factors = [(i, j, weight) for pair, weight in pairwise.items()
                   for i, j in [tuple(pair)] if i in sep_set and j in sep_set]
    frame_factors = []
    for interior in interiors:
        interior_set = set(interior)
        local_set = sep_set | interior_set
        frame_factors.append((
            interior,
            [(i, j, weight) for pair, weight in pairwise.items()
             for i, j in [tuple(pair)]
             if i in local_set and j in local_set and
             (i in interior_set or j in interior_set)]))
    for boundary_values in itertools.product(vocab, repeat=len(sep)):
        state = dict(zip(sep, boundary_values))
        base = -sum(unary[i] * state[i] for i in sep)
        for i, j, weight in sep_factors:
            base -= weight * state[i] * state[j]
        factor_evaluations += len(sep_factors)
        total = base
        candidate = dict(state)
        for interior, local_factors in frame_factors:
            local_best, local_state = math.inf, None
            for values in itertools.product(vocab, repeat=len(interior)):
                states_checked += 1
                local = dict(zip(interior, values))
                local.update(state)
                energy = -sum(unary[i] * local[i] for i in interior)
                for i, j, weight in local_factors:
                    energy -= weight * local[i] * local[j]
                factor_evaluations += len(interior) + len(local_factors)
                if energy < local_best:
                    local_best, local_state = energy, dict(local)
            total += local_best
            candidate.update({i: local_state[i] for i in interior})
        if total < best_total:
            best_total, best_state = total, candidate
    return {"energy": best_total, "state": best_state,
            "local_assignments_checked": states_checked,
            "boundary_assignments": len(vocab) ** len(sep),
            "factor_evaluations": factor_evaluations}


def timed_peak(fn):
    tracemalloc.start()
    start = time.perf_counter_ns()
    result = fn()
    elapsed = time.perf_counter_ns() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def main():
    import substrate_rs as sr
    import domains.can_junction_tree as cjt
    from domains.graph_treewidth import min_fill_upper_bound

    records = []
    configs = itertools.product(FRAME_COUNTS, FRAME_INTERIORS, SEPARATOR_SIZES,
                                DOMAIN_SIZES, range(REPLICATES))
    for frames, interior, k, d, rep in configs:
        seed = 20260925 + frames * 100003 + interior * 1009 + k * 97 + d * 13 + rep
        nodes, sep, interiors, unary, pairwise = make_problem(frames, interior, k, d, seed)
        vocab = VOCAB_BY_D[d]
        s = sr.Substrate()
        inner = s._inner
        mt = inner.add_node("Microtheory", {"discrete_mode": "2state" if d == 2 else "3state"})
        concepts = {i: inner.add_node("Concept", {"name": f"x{i}",
                         "external_field": float(unary[i]), "identity_field": 0.0,
                         "state": 0.0}) for i in nodes}
        for node in concepts.values():
            inner.add_edge_unchecked(mt, "has_concept", node, {})
        for pair, weight in pairwise.items():
            i, j = tuple(pair)
            inner.add_edge_unchecked(concepts[i], "causal_influence", concepts[j], {"weight": weight})
            inner.add_edge_unchecked(concepts[j], "causal_influence", concepts[i], {"weight": weight})

        t0 = time.perf_counter_ns()
        extracted = cjt.can_network_from_mt(s, mt)
        extraction_ns = time.perf_counter_ns() - t0
        local_of = {concepts[i].value: i for i in nodes}
        net = {
            "nodes": list(nodes),
            "edges": [(local_of[i], local_of[j]) for i, j in extracted["edges"]],
            "unary": {local_of[i]: h for i, h in extracted["unary"].items()},
            "pairwise": {frozenset(local_of[i] for i in edge): weight
                         for edge, weight in extracted["pairwise"].items()},
        }
        if net["unary"] != unary or net["pairwise"] != pairwise:
            raise AssertionError("native CAN extraction changed generated factor model")
        t0 = time.perf_counter_ns()
        width = min_fill_upper_bound(net["nodes"], net["edges"])
        width_ns = time.perf_counter_ns() - t0

        jt, jt_ns, jt_peak = timed_peak(lambda: cjt.junction_tree_map(
            net["nodes"], net["edges"], net["unary"], net["pairwise"], vocab,
            order=width["elimination_order"]))
        fact, fact_ns, fact_peak = timed_peak(lambda: conditional_frame_map(
            sep, interiors, unary, pairwise, vocab))
        jt_energy = independent_energy(unary, pairwise, jt["state"])
        fact_energy = independent_energy(unary, pairwise, fact["state"])
        if abs(jt_energy - fact_energy) > 1e-7 or abs(jt["energy"] - fact_energy) > 1e-7:
            raise AssertionError("global junction tree and conditional frame exact MAP disagree")
        expected_width = k + interior - 1
        if width["treewidth"] != expected_width:
            raise AssertionError(f"expected width {expected_width}, got {width['treewidth']}")
        records.append({
            "frames": frames, "interior_nodes_per_frame": interior,
            "separator_dimensions": k, "domain_size": d, "replicate": rep,
            "seed": seed, "nodes": len(nodes), "undirected_pairs": len(pairwise),
            "separator_assignments": fact["boundary_assignments"],
            "frame_local_assignments_checked": fact["local_assignments_checked"],
            "factor_evaluations": fact["factor_evaluations"],
            "treewidth_upper_bound": width["treewidth"],
            "exact_energy_gap": jt_energy - fact_energy,
            "input_model_extraction_exact": True,
            "cost_ns": {"graph_extraction": extraction_ns, "min_fill_width": width_ns,
                        "global_junction_tree": jt_ns, "conditional_frame_exact": fact_ns},
            "python_peak_traced_bytes": {"global_junction_tree": jt_peak,
                                          "conditional_frame_exact": fact_peak},
        })
        print(f"F={frames} m={interior} k={k} d={d} rep={rep} n={len(nodes)} "
              f"tw={width['treewidth']} exact_gap=0", flush=True)

    summaries = []
    for frames in FRAME_COUNTS:
        for interior in FRAME_INTERIORS:
            for k in SEPARATOR_SIZES:
                for d in DOMAIN_SIZES:
                    group = [r for r in records if r["frames"] == frames and
                             r["interior_nodes_per_frame"] == interior and
                             r["separator_dimensions"] == k and r["domain_size"] == d]
                    summaries.append({
                        "frames": frames, "interior_nodes_per_frame": interior,
                        "separator_dimensions": k, "domain_size": d, "replicates": len(group),
                        "treewidth": group[0]["treewidth_upper_bound"],
                        "median_cost_ns": {key: int(statistics.median(r["cost_ns"][key] for r in group))
                                           for key in group[0]["cost_ns"]},
                        "median_peak_traced_bytes": {
                            key: int(statistics.median(r["python_peak_traced_bytes"][key] for r in group))
                            for key in ("global_junction_tree", "conditional_frame_exact")},
                        "median_local_assignments_checked": int(statistics.median(
                            r["frame_local_assignments_checked"] for r in group)),
                        "median_separator_assignments": int(statistics.median(
                            r["separator_assignments"] for r in group)),
                        "median_factor_evaluations": int(statistics.median(
                            r["factor_evaluations"] for r in group)),
                    })

    sources = [Path(__file__).resolve(), ROOT / "domains/can_junction_tree.py",
               ROOT / "domains/graph_treewidth.py"]
    payload = {
        "schema_version": 1,
        "run_id": "can-separator-factorization-envelope-20260925",
        "scope": "exact MAP on synthetic modular pairwise CAN models with shared separator; global junction tree versus conditional frame enumeration",
        "claim_boundary": "Validates exact factorization for this explicit separator construction only. Does not establish that learned runtime frames match cheap cuts, natural task locality, native scheduler speedup, or large-system asymptotics. Python tracemalloc excludes native graph memory and process RSS.",
        "configuration": {"frame_counts": FRAME_COUNTS, "interior_sizes": FRAME_INTERIORS,
                          "separator_sizes": SEPARATOR_SIZES, "domain_sizes": DOMAIN_SIZES,
                          "replicates": REPLICATES},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor()},
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in sources},
        "checks": {
            "all_native_snapshots_match_generated_model": all(r["input_model_extraction_exact"] for r in records),
            "all_junction_tree_and_conditional_frame_maps_agree": all(abs(r["exact_energy_gap"]) <= 1e-7 for r in records),
            "all_widths_match_constructed_clique_bound": all(
                r["treewidth_upper_bound"] == r["separator_dimensions"] + r["interior_nodes_per_frame"] - 1
                for r in records),
            "conditional_enumeration_work_matches_frame_separator_formula": all(
                r["frame_local_assignments_checked"] == r["frames"] *
                    (r["domain_size"] ** (r["separator_dimensions"] + r["interior_nodes_per_frame"])) and
                r["separator_assignments"] == r["domain_size"] ** r["separator_dimensions"]
                for r in records),
        },
        "summaries": summaries, "runs": records,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"runs": len(records), "checks": payload["checks"], "output": str(OUT)}, indent=2))
    if not all(payload["checks"].values()):
        raise SystemExit("separator factorization invariant failed")


if __name__ == "__main__":
    main()
