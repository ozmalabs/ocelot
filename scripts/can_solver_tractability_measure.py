"""Measurement script for CAN_SOLVER_TRACTABILITY_PREREG.md.

Four independent measurements, run in one process for convenience but each
self-contained and separately reported:

  1. Local-minimum-risk (load-bearing): multi-start discrete-async native
     relaxation on the SAME coupling network, condition A (N=16 complete,
     random-sign, frustrated/dense) and condition B (real Bigville
     residents, sparse). Measures whether different initial conditions land
     on measurably different-quality stable states.
  2. Treewidth: exact brute-force minimum induced width for Bigville's real
     5-node structural template and for the N=16 complete graph used in
     condition A.
  3. Low-rank/shared-generator: SVD effective rank of the real 100-resident
     true_j coupling matrix.
  4. (Bethe/BP is a pure design investigation, reported in the RESULTS doc
     text, not measured by this script.)

WORLD-ADAPTER / MEASUREMENT script only -- no agent decision logic. Every
branch here is fixed analysis code operating on already-computed numbers or
mechanically re-seeding graph state for a fresh trial, not a rule engine
over live agent cognition.
"""
from __future__ import annotations

import itertools
import json
import os
import random
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate_rs import _native                                    # noqa: E402
from substrate.seed_loader import engine_rules_only                 # noqa: E402
from worlds.bigville_can_beliefs import (                           # noqa: E402
    install_productions, build_resident_can_mt, apply_scenario_evidence,
    TOPIC_NAMES, STRUCTURAL_EDGES, true_edge_j, quantize_j,
    effective_resolution_bins,
)

NATIVE_SEED_PATH = os.path.join(_ROOT, "seeds", "can_native_reimplementation.json")
CAST_PATH = os.path.join(_ROOT, "seeds", "bigville_cast100.json")


# ======================================================================
# Measurement 2 -- exact treewidth, brute force over elimination orderings
# ======================================================================

def exact_treewidth(nodes: list, edges: list[tuple]) -> int:
    """Brute-force minimum induced width over ALL elimination orderings.
    Correct (not heuristic) for small graphs. edges: list of (u, v) pairs,
    undirected."""
    adj = {n: set() for n in nodes}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)

    best = None
    for order in itertools.permutations(nodes):
        g = {n: set(adj[n]) for n in nodes}
        width = 0
        pruned = False
        for v in order:
            nbrs = g[v]
            width = max(width, len(nbrs))
            if best is not None and width >= best:
                pruned = True
                break
            # eliminate v: connect all its remaining neighbours (fill-in),
            # then remove v from the graph entirely.
            for a in nbrs:
                for b in nbrs:
                    if a != b:
                        g[a].add(b)
                g[a].discard(v)
            del g[v]
        if not pruned and (best is None or width < best):
            best = width
    return best


def measure_treewidth():
    print("\n=== Measurement 2: exact treewidth ===")
    # Bigville's real structural template (topology only -- weights vary
    # per-resident, topology never does).
    bv_nodes = TOPIC_NAMES
    bv_edges = [(a, b) for a, b, _bj, _nk in STRUCTURAL_EDGES]
    tw_bv = exact_treewidth(bv_nodes, bv_edges)
    print(f"Bigville structural template: nodes={len(bv_nodes)} "
          f"edges={len(bv_edges)} exact_treewidth={tw_bv}")

    # N=16 complete graph (condition A's own topology).
    n16_nodes = list(range(16))
    n16_edges = [(i, j) for i in range(16) for j in range(i + 1, 16)]
    # Complete graph treewidth is N-1 by definition; confirm on a smaller
    # complete graph by brute force (N=16 permutations is intractable to
    # brute force literally -- 16! -- so confirm the DEFINITIONAL fact on
    # N=6 and N=8 complete graphs instead, and state the N=16 number by the
    # same closed-form definition, not by brute force).
    tw_checks = {}
    for n in (4, 6, 8):
        nodes = list(range(n))
        edges = [(i, j) for i in range(n) for j in range(n) if i < j]
        tw_checks[n] = exact_treewidth(nodes, edges)
    print(f"Complete-graph treewidth check (brute force, small N): {tw_checks} "
          f"(expect n-1 for each)")
    tw_n16 = 15  # closed-form N-1, confirmed by the pattern above, not
    # separately brute-forced (16! elimination orderings is not tractable
    # to enumerate; the closed-form fact -- a complete graph's only maximal
    # clique after ANY elimination ordering is the whole graph -- is
    # standard and confirmed empirically for n in (4,6,8) above).
    print(f"N=16 complete graph: exact_treewidth={tw_n16} (closed-form N-1, "
          f"confirmed by the brute-force pattern for n=4,6,8 above)")
    return {
        "bigville_treewidth": tw_bv, "bigville_nodes": len(bv_nodes),
        "bigville_edges": len(bv_edges),
        "complete_graph_treewidth_checks": tw_checks,
        "n16_treewidth": tw_n16,
    }


# ======================================================================
# Measurement 3 -- low-rank / shared-generator, real Bigville data
# ======================================================================

def measure_low_rank():
    print("\n=== Measurement 3: low-rank/shared-generator on real data ===")
    residents = json.load(open(CAST_PATH))["residents"]
    edge_names = [f"{a}-{b}" for a, b, _bj, _nk in STRUCTURAL_EDGES]

    true_matrix = []
    quant_matrix = []
    for r in residents:
        p = r["params"]
        eff_bins = effective_resolution_bins(p["resolution_bins"], p["arousal"])
        row_true = []
        row_quant = []
        for a, b, base_j, nuance_key in STRUCTURAL_EDGES:
            tj = true_edge_j(p, base_j, nuance_key)
            qj = quantize_j(tj, eff_bins)
            row_true.append(tj)
            row_quant.append(qj)
        true_matrix.append(row_true)
        quant_matrix.append(row_quant)

    n_res = len(residents)
    n_edges = len(edge_names)

    # Mean-center columns, compute SVD via a pure-Python Jacobi eigenvalue
    # method on X^T X (5x5, tiny -- no numpy dependency needed, but numpy is
    # already a real dependency of this codebase's own bigville demo script,
    # so use it directly for a correct, standard SVD).
    import numpy as np
    X = np.array(true_matrix, dtype=float)
    Xc = X - X.mean(axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    total_var = float((S ** 2).sum())
    explained = (S ** 2) / total_var if total_var > 0 else S * 0
    cum_explained = np.cumsum(explained)
    participation_ratio = float((S.sum() ** 2) / (S ** 2).sum()) if total_var > 0 else 0.0
    n_for_95pct = int(np.searchsorted(cum_explained, 0.95) + 1)

    print(f"residents={n_res} edges={n_edges}")
    print(f"singular values (true_j, mean-centered): {[round(float(s), 4) for s in S]}")
    print(f"fraction variance explained per component: "
          f"{[round(float(e), 4) for e in explained]}")
    print(f"effective rank (participation ratio (sum s)^2/sum s^2): "
          f"{participation_ratio:.3f}")
    print(f"components needed for 95% variance: {n_for_95pct} of {n_edges}")

    # Distinct-value count (the OTHER candidate explanation -- value-alphabet
    # compression rather than true low rank).
    quant_flat = [v for row in quant_matrix for v in row]
    n_distinct_quant = len(set(round(v, 6) for v in quant_flat))
    print(f"distinct quantized_j values across all {n_res*n_edges} "
          f"(resident,edge) cells: {n_distinct_quant}")

    # Per-edge column rank contribution: how much does each edge's true_j
    # correlate with the two known nuance drivers (mood_bias, w_supergraph)?
    mood = np.array([r["params"]["mood_bias"] for r in residents])
    supg = np.array([r["params"]["w_supergraph"] for r in residents])
    corr_report = []
    for i, (a, b, base_j, nuance_key) in enumerate(STRUCTURAL_EDGES):
        col = Xc[:, i]
        driver = mood if nuance_key == "mood_bias" else supg
        driver_c = driver - driver.mean()
        denom = (np.linalg.norm(col) * np.linalg.norm(driver_c))
        corr = float(np.dot(col, driver_c) / denom) if denom > 0 else 0.0
        corr_report.append((edge_names[i], nuance_key, round(corr, 4)))
    print(f"per-edge correlation with its OWN nuance driver: {corr_report}")

    return {
        "n_residents": n_res, "n_edges": n_edges,
        "singular_values": [float(s) for s in S],
        "explained_variance_fraction": [float(e) for e in explained],
        "participation_ratio_effective_rank": participation_ratio,
        "n_components_for_95pct_variance": n_for_95pct,
        "n_distinct_quantized_values": n_distinct_quant,
        "per_edge_driver_correlation": corr_report,
    }


# ======================================================================
# Measurement 1 (load-bearing) -- local-minimum risk, multi-start
# ======================================================================

def _loaded_native_substrate():
    s = _native.Substrate()
    manifest = json.load(open(NATIVE_SEED_PATH))
    s.load_seed_manifest(engine_rules_only(manifest))
    return s


def _round_to_vocab(x, granularity, half_width):
    k = round(x / granularity)
    k = max(-half_width, min(half_width, k))
    return k * granularity


def _build_n16_draw(s, seed, coarse, discrete_mode="3state"):
    """N=16 complete graph, random-sign coupling -- the frustrated/dense
    condition A. Mirrors test_can_native_reimplementation.py::_build_draw
    exactly, extended from N=8 to N=16."""
    N = 16
    pair_rng = random.Random(seed * 31 + N)
    field_rng = random.Random(seed * 53 + N)
    mt = s.add_node("Microtheory", {
        "temperature": 2.0, "discrete_mode": discrete_mode, "can_tick": 0,
    })
    concepts = [
        s.add_node("Concept", {
            "name": "c%d" % i, "state": 0.0,
            "external_field": 0.0, "identity_field": 0.0,
        })
        for i in range(N)
    ]
    for c in concepts:
        s.add_edge(mt, "has_concept", c, {})
    for i in range(N):
        h = field_rng.uniform(-1, 1)
        s.set_attr(concepts[i], "external_field", h)
    for i in range(N):
        for j in range(i + 1, N):
            raw = pair_rng.uniform(-1, 1)
            v = (_round_to_vocab(raw, 1.0, 1) if coarse
                 else _round_to_vocab(raw, 0.25, 4))
            s.add_edge(concepts[i], "causal_influence", concepts[j], {"weight": v})
            s.add_edge(concepts[j], "causal_influence", concepts[i], {"weight": v})
    return mt, concepts


def _multi_start_sweep(s, mt, concepts, k_starts, rng, discrete_mode="3state",
                        max_steps=3000):
    """Re-seed state K times, relax to a fixpoint each time, record
    frustration + exact final-state signature. Returns list of
    (frustration, state_signature) tuples, one per start."""
    vocab = (-1.0, 0.0, 1.0) if discrete_mode == "3state" else (-1.0, 1.0)
    results = []
    for _ in range(k_starts):
        for c in concepts:
            s.set_attr(c, "state", float(rng.choice(vocab)))
        steps = s.run_rules(max_steps)
        state = {c.value: float(s.node(c)["attrs"].get("state", 0.0)) for c in concepts}
        frustration = s.mt_frustration_given_state(mt, state)
        sig = tuple(round(state[c.value], 3) for c in concepts)
        results.append((float(frustration), sig, steps < max_steps))
    return results


def _summarize_draw(results):
    frustrations = [r[0] for r in results]
    converged_all = all(r[2] for r in results)
    best = min(frustrations)
    worst = max(frustrations)
    spread = worst - best
    n_distinct = len(set(r[1] for r in results))
    frac_at_best = sum(1 for f in frustrations if abs(f - best) < 1e-6) / len(frustrations)
    return {
        "best": best, "worst": worst, "spread": spread,
        "n_distinct_final_states": n_distinct, "frac_at_best": frac_at_best,
        "converged_all": converged_all,
    }


def measure_local_minimum_risk_condition_a(d_draws=15, k_starts=20):
    print("\n=== Measurement 1a: local-minimum risk, condition A "
          "(N=16 complete, frustrated/dense) ===")
    rows = []
    for coarse in (True, False):
        for seed in range(d_draws):
            s = _loaded_native_substrate()
            mt, concepts = _build_n16_draw(s, 5000 + seed, coarse)
            rng = random.Random(9000 + seed)
            results = _multi_start_sweep(s, mt, concepts, k_starts, rng)
            summary = _summarize_draw(results)
            summary["coarse"] = coarse
            summary["seed"] = seed
            rows.append(summary)
    return rows


def measure_local_minimum_risk_condition_b(n_residents=30, k_starts=20):
    print("\n=== Measurement 1b: local-minimum risk, condition B "
          "(real Bigville residents, sparse) ===")
    all_residents = json.load(open(CAST_PATH))["residents"]
    by_bins = sorted(all_residents, key=lambda r: (r["params"]["resolution_bins"], r["index"]))
    lo10 = by_bins[:10]
    hi10 = by_bins[-10:]
    mid_rng = random.Random(20260814)
    remaining = [r for r in all_residents if r not in lo10 and r not in hi10]
    mid10 = mid_rng.sample(remaining, 10)
    sample = lo10 + hi10 + mid10

    rows = []
    for resident in sample:
        s = _native.Substrate()
        install_productions(s)
        manifest = json.load(open(NATIVE_SEED_PATH))
        s.load_seed_manifest(engine_rules_only(manifest))
        built = build_resident_can_mt(s, resident)
        apply_scenario_evidence(s, built["concepts"])
        s.set_attr(built["mt_node"], "discrete_mode", "3state")
        s.set_attr(built["mt_node"], "can_tick", 0)
        concept_ids = list(built["concepts"].values())
        rng = random.Random(resident["index"] + 90000)
        results = _multi_start_sweep(s, built["mt_node"], concept_ids, k_starts, rng)
        summary = _summarize_draw(results)
        summary["resident_index"] = resident["index"]
        summary["resolution_bins"] = resident["params"]["resolution_bins"]
        rows.append(summary)
    return rows


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return 0.0
    mid = n // 2
    return xs[mid] if n % 2 else (xs[mid - 1] + xs[mid]) / 2.0


def report_local_minimum_summary(label, rows):
    spreads = [r["spread"] for r in rows]
    bests = [r["best"] for r in rows]
    fracs = [r["frac_at_best"] for r in rows]
    distincts = [r["n_distinct_final_states"] for r in rows]
    med_spread = _median(spreads)
    med_best = _median(bests)
    med_frac = _median(fracs)
    med_distinct = _median(distincts)
    rel_spread = (med_spread / med_best) if med_best > 0 else (
        float("inf") if med_spread > 0 else 0.0)
    all_converged = all(r["converged_all"] for r in rows)
    print(f"\n--- {label} summary (n_draws={len(rows)}) ---")
    print(f"median best_frustration={med_best:.4f} median spread={med_spread:.4f} "
          f"median_relative_spread={rel_spread:.4f}")
    print(f"median frac_at_best={med_frac:.4f} median n_distinct_final_states={med_distinct}")
    print(f"all draws fully converged (no run hit max_steps): {all_converged}")
    return {
        "label": label, "n_draws": len(rows),
        "median_best_frustration": med_best, "median_spread": med_spread,
        "median_relative_spread": rel_spread, "median_frac_at_best": med_frac,
        "median_n_distinct_final_states": med_distinct,
        "all_converged": all_converged, "rows": rows,
    }


def main():
    out = {}
    out["treewidth"] = measure_treewidth()
    out["low_rank"] = measure_low_rank()

    rows_a = measure_local_minimum_risk_condition_a()
    summary_a = report_local_minimum_summary("Condition A (N=16 frustrated/dense)", rows_a)
    out["local_minimum_condition_a"] = summary_a

    rows_b = measure_local_minimum_risk_condition_b()
    summary_b = report_local_minimum_summary("Condition B (Bigville real sparse)", rows_b)
    out["local_minimum_condition_b"] = summary_b

    go = (summary_a["median_relative_spread"] > 0.05
          and summary_a["median_frac_at_best"] < 0.80
          and summary_a["median_n_distinct_final_states"] > 1)
    print(f"\n=== GO/NO-GO on condition A (registered criteria) ===")
    print(f"median_relative_spread > 0.05: "
          f"{summary_a['median_relative_spread']:.4f} -> "
          f"{summary_a['median_relative_spread'] > 0.05}")
    print(f"median_frac_at_best < 0.80: "
          f"{summary_a['median_frac_at_best']:.4f} -> "
          f"{summary_a['median_frac_at_best'] < 0.80}")
    print(f"median_n_distinct_final_states > 1: "
          f"{summary_a['median_n_distinct_final_states']} -> "
          f"{summary_a['median_n_distinct_final_states'] > 1}")
    print(f"GO (condition A): {go}")
    out["go_condition_a"] = go

    with open(os.path.join(_ROOT, "scripts",
                            "can_solver_tractability_measure_results.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    print("\nwrote scripts/can_solver_tractability_measure_results.json")


if __name__ == "__main__":
    main()
