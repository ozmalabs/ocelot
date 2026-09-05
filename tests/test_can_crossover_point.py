"""Live demonstration for CAN_CROSSOVER_POINT_PREREG.md / _RESULTS.md.

The follow-on to CAN_BELIEF_QUANTIZATION_RESULTS.md's 2x3 factorial: that
rung found the "coarse degrades faster than fine as N grows" prediction
REVERSED at N=4/8 and only converging (not diverging) at N=16 -- flagged in
its own PREREG as a probable ceiling/density-effect artifact, not a
confirmed crossover. This file runs the crossover-point sweep that rung
explicitly left for a follow-on: a wider N range, literature-grounded
resolution anchors (coarse=3 bins, fine=7 bins, per
CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md SS8), seed
replication (5 draws per cell, not 1), a continuous resolution sweep across
the literature's own 2-11 tested range, and a population-MIXTURE design
(not one fixed resolution per condition).

Reuses -- does NOT reimplement -- the prior rung's own multi-start basin
discovery (_basin_sweep), network construction (_build_complete_network),
and oscillation probe (_oscillates/_relax_with_fields), imported directly
from tests/test_can_belief_quantization.py (see _import_prior_helpers()
below). Only the quantizer is generalized (see _round_to_vocab_v), and only
because the literature-grounded target (Preston & Colman's own evenly-
spaced 2-11 category design) needs an evenly-spaced-inclusive-of-endpoints
scheme the prior rung's centered-odd-only _round_to_vocab could not
express; V=3 is numerically identical to the prior rung's own "coarse"
condition, so this is a strict generalization, not a redefinition.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import math
import pathlib
import random
import statistics

import pytest
from substrate_rs import _native


# ---------------------------------------------------------------------------
# Reuse, not reinvention: import the prior rung's own helpers directly from
# its test file (PREREG SS4's exact citation set).
# ---------------------------------------------------------------------------
def _import_prior_helpers():
    path = pathlib.Path(__file__).parent / "test_can_belief_quantization.py"
    spec = importlib.util.spec_from_file_location("test_can_belief_quantization", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_prior = _import_prior_helpers()
_fresh_substrate = _prior._fresh_substrate
_build_complete_network = _prior._build_complete_network
_basin_sweep = _prior._basin_sweep
# PHASE A: _relax_with_fields / _oscillates are no longer imported — they
# drove the removed continuous engine and their only consumer here
# (test_sharpening_b) was deleted.


# ---------------------------------------------------------------------------
# SS1 of the PREREG: the literature-grounded, evenly-spaced V-point quantizer,
# generalizing (not replacing) the prior rung's centered-integer-k scheme.
# ---------------------------------------------------------------------------
def _round_to_vocab_v(x: float, V: int) -> float:
    """Round x in [-1,1] to the nearest of V evenly-spaced points spanning
    [-1,+1] inclusive of both endpoints -- the same shape Preston & Colman
    (2000) tested (2 to 11 response categories), generalizing the prior
    rung's odd/zero-centered-only _round_to_vocab. V=3 reproduces the prior
    rung's own coarse condition {-1,0,+1} exactly; V=1 is undefined and
    never used."""
    assert V >= 2
    values = [-1.0 + 2.0 * i / (V - 1) for i in range(V)]
    return min(values, key=lambda v: abs(v - x))


def _draw_true_j(n, seed):
    pair_rng = random.Random(seed * 1000 + n)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    return pairs, {p: pair_rng.uniform(-1.0, 1.0) for p in pairs}


def _draw_structured_true_j(n, seed):
    """SS3(a) of the PREREG: a 'coherent core + adversarial noise' coupling
    generator -- concepts partitioned into blocks of <=4, within-block
    couplings cluster around one of two block-level anchors (+-0.7) plus
    small noise (real, recognizable STRUCTURE a future shape-compressor
    could exploit); across-block couplings stay i.i.d. Uniform(-1,1) (the
    unstructured admixture), per CAN_BELIEF_QUANTIZATION_RESULTS.md SS3
    point 1's own named next step."""
    pair_rng = random.Random(seed * 2000 + n * 3)
    block_of = {}
    block_size = 4
    n_blocks = math.ceil(n / block_size)
    anchors = [0.7 if b % 2 == 0 else -0.7 for b in range(n_blocks)]
    for i in range(n):
        block_of[i] = i // block_size
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    true_j = {}
    for (i, j) in pairs:
        if block_of[i] == block_of[j]:
            anchor = anchors[block_of[i]]
            true_j[(i, j)] = max(-1.0, min(1.0, anchor + pair_rng.uniform(-0.15, 0.15)))
        else:
            true_j[(i, j)] = pair_rng.uniform(-1.0, 1.0)
    return pairs, true_j


def _cell(n, pairs, true_j, V, restarts, beta, seed):
    rounded = {p: _round_to_vocab_v(v, V) for p, v in true_j.items()}
    mean_abs_err = sum(abs(true_j[p] - rounded[p]) for p in pairs) / len(pairs)
    s = _fresh_substrate()
    mt, concepts = _build_complete_network(s, n, beta=beta, weights=rounded)
    rng = random.Random(seed * 7 + n * 13 + V)
    basin_count, eff_basins, dom_frac, mean_f, mean_e = _basin_sweep(
        s, mt, concepts, restarts, rng)
    return {
        "N": n, "V": V, "seed": seed,
        "mean_abs_rounding_error": round(mean_abs_err, 4),
        "basin_count": basin_count,
        "effective_basin_count": round(eff_basins, 3),
        "dominant_basin_fraction": round(dom_frac, 3),
        "mean_frustration": round(mean_f, 4),
        "mean_energy": round(mean_e, 4),
    }


# ---------------------------------------------------------------------------
# Experiment A -- the N-crossover sweep (PREREG SS2.1). N x {coarse,fine} x
# 5 seeds x 40 restarts.
# ---------------------------------------------------------------------------
def _experiment_a(ns=(4, 8, 12, 16, 24, 32), seeds=(1, 2, 3, 4, 5), restarts=40, beta=2.0):
    rows = []
    for n in ns:
        for seed in seeds:
            pairs, true_j = _draw_true_j(n, seed)
            for label, V in (("coarse", 3), ("fine", 7)):
                row = _cell(n, pairs, true_j, V, restarts, beta, seed)
                row["coarseness"] = label
                rows.append(row)
    return rows


def _summarize_by_n_condition(rows, key_extra=()):
    """Group rows by (N, coarseness[, *key_extra]) and report mean + range
    across the seed replicates -- the seed-to-seed spread IS the noise floor
    Experiment A's own registered crossover criterion (PREREG SS2.4.2) is
    measured against."""
    groups = {}
    for r in rows:
        key = (r["N"], r["coarseness"]) + tuple(r[k] for k in key_extra)
        groups.setdefault(key, []).append(r)
    summary = []
    for key, rs in sorted(groups.items()):
        entry = {"N": key[0], "coarseness": key[1]}
        for i, k in enumerate(key_extra):
            entry[k] = key[2 + i]
        for metric in ("effective_basin_count", "dominant_basin_fraction",
                       "mean_frustration", "mean_energy", "basin_count",
                       "mean_abs_rounding_error"):
            vals = [r[metric] for r in rs]
            entry[f"{metric}_mean"] = round(statistics.mean(vals), 4)
            entry[f"{metric}_min"] = round(min(vals), 4)
            entry[f"{metric}_max"] = round(max(vals), 4)
        summary.append(entry)
    return summary


def test_experiment_a_crossover_sweep():
    """THE primary crossover sweep. Run with -s to see the full table --
    CAN_CROSSOVER_POINT_RESULTS.md's Experiment A numbers are taken verbatim
    from this output."""
    rows = _experiment_a()
    summary = _summarize_by_n_condition(rows)
    print("\n=== EXPERIMENT A: N-crossover sweep (5 seeds/cell) ===")
    print(json.dumps(summary, indent=2))
    print("\n%-4s %-8s %-10s %-10s %-10s %-10s %-10s" % (
        "N", "coarse?", "eff_basin", "dom_frac", "frustr", "energy", "basin_ct"))
    for e in summary:
        print("%-4d %-8s %-10.3f %-10.3f %-10.3f %-10.3f %-10.3f" % (
            e["N"], e["coarseness"], e["effective_basin_count_mean"],
            e["dominant_basin_fraction_mean"], e["mean_frustration_mean"],
            e["mean_energy_mean"], e["basin_count_mean"]))
    assert len(rows) == 6 * 2 * 5
    assert all(r["basin_count"] >= 1 for r in rows)


# ---------------------------------------------------------------------------
# Experiment B -- continuous resolution sweep (PREREG SS2.2).
# ---------------------------------------------------------------------------
def _experiment_b(ns=(8, 16, 32), vs=(2, 3, 4, 5, 7, 9, 11), seeds=(1, 2, 3, 4, 5),
                   restarts=40, beta=2.0):
    rows = []
    for n in ns:
        for seed in seeds:
            pairs, true_j = _draw_true_j(n, seed)
            for V in vs:
                row = _cell(n, pairs, true_j, V, restarts, beta, seed)
                rows.append(row)
    return rows


def test_experiment_b_resolution_sweep():
    """The continuous 2-11 bin sweep at N in {8,16,32}. Addresses the
    charter's 'test resolution levels spanning roughly 2-12 bins' requirement
    directly, rather than only the coarse/fine binary."""
    rows = _experiment_b()
    summary = _summarize_by_n_condition(
        [dict(r, coarseness=f"V={r['V']}") for r in rows], key_extra=("V",))
    print("\n=== EXPERIMENT B: continuous resolution sweep (5 seeds/cell) ===")
    print(json.dumps(summary, indent=2))
    print("\n%-4s %-4s %-10s %-10s %-10s %-10s" % (
        "N", "V", "eff_basin", "dom_frac", "frustr", "energy"))
    for e in summary:
        print("%-4d %-4d %-10.3f %-10.3f %-10.3f %-10.3f" % (
            e["N"], e["V"], e["effective_basin_count_mean"],
            e["dominant_basin_fraction_mean"], e["mean_frustration_mean"],
            e["mean_energy_mean"]))
    assert len(rows) == 3 * 7 * 5
    assert all(r["basin_count"] >= 1 for r in rows)


# ---------------------------------------------------------------------------
# Experiment C -- population-mixture design (PREREG SS2.3).
# ---------------------------------------------------------------------------
def _draw_mixture_v(rng):
    """Two-component mixture: pi=0.5 floor/naive (V in {2,3}), pi=0.5
    ceiling/exposed (V in {6,7,8}) -- per PREREG SS2.3, means 2.5 and 7 (a
    3.5x ratio), same order of magnitude as CRT's own measured ~2.5x
    floor/ceiling swing, not force-tuned to match it exactly."""
    if rng.random() < 0.5:
        return "floor", rng.choice([2, 3])
    return "ceiling", rng.choice([6, 7, 8])


def _experiment_c(ns=(4, 8, 16, 32), k_individuals=30, restarts=15, beta=2.0, seed=20260813):
    rows = []
    for n in ns:
        pop_rng = random.Random(seed * 91 + n)
        for indiv in range(k_individuals):
            component, V = _draw_mixture_v(pop_rng)
            pairs, true_j = _draw_true_j(n, seed=(seed * 131 + n * 17 + indiv))
            row = _cell(n, pairs, true_j, V, restarts, beta, seed=(seed + indiv))
            row["component"] = component
            row["individual"] = indiv
            rows.append(row)
    return rows


def test_experiment_c_population_mixture():
    """The realistic-population-spread check: does drawing resolution from a
    two-component floor/ceiling mixture (not one fixed V per condition)
    reproduce Experiment A's own coarse-vs-fine pattern at the same N?"""
    rows = _experiment_c()
    summary = _summarize_by_n_condition(
        [dict(r, coarseness=r["component"]) for r in rows])
    print("\n=== EXPERIMENT C: population mixture (K=30 individuals/N) ===")
    print(json.dumps(summary, indent=2))
    print("\n%-4s %-9s %-10s %-10s %-10s %-10s" % (
        "N", "component", "eff_basin", "dom_frac", "frustr", "energy"))
    for e in summary:
        print("%-4d %-9s %-10.3f %-10.3f %-10.3f %-10.3f" % (
            e["N"], e["coarseness"], e["effective_basin_count_mean"],
            e["dominant_basin_fraction_mean"], e["mean_frustration_mean"],
            e["mean_energy_mean"]))
    assert len(rows) == 4 * 30
    assert all(r["basin_count"] >= 1 for r in rows)
    # Manipulation check: floor individuals really are coarser than ceiling.
    floor_err = statistics.mean(r["mean_abs_rounding_error"] for r in rows if r["component"] == "floor")
    ceiling_err = statistics.mean(r["mean_abs_rounding_error"] for r in rows if r["component"] == "ceiling")
    assert floor_err > ceiling_err


# ---------------------------------------------------------------------------
# Sharpening (a) -- structured vs unstructured coupling (PREREG SS3(a)).
# ---------------------------------------------------------------------------
def _experiment_structured(ns=(4, 8, 12, 16, 24, 32), seeds=(1, 2, 3, 4, 5), restarts=40, beta=2.0):
    rows = []
    for n in ns:
        for seed in seeds:
            pairs, true_j = _draw_structured_true_j(n, seed)
            for label, V in (("coarse", 3), ("fine", 7)):
                row = _cell(n, pairs, true_j, V, restarts, beta, seed)
                row["coarseness"] = label
                rows.append(row)
    return rows


def test_sharpening_a_structured_vs_unstructured():
    """Scoped tractability check (NOT the compression layer itself, per the
    charter's explicit out-of-scope line): does a coupling matrix with real,
    recognizable BLOCK STRUCTURE (redundancy a future shape-compressor could
    exploit) show a different crossover pattern than the i.i.d.-random-sign
    draw Experiment A uses throughout?"""
    rows = _experiment_structured()
    summary = _summarize_by_n_condition(rows)
    print("\n=== SHARPENING (a): structured (blocky) coupling sweep ===")
    print(json.dumps(summary, indent=2))
    print("\n%-4s %-8s %-10s %-10s %-10s" % ("N", "coarse?", "eff_basin", "dom_frac", "frustr"))
    for e in summary:
        print("%-4d %-8s %-10.3f %-10.3f %-10.3f" % (
            e["N"], e["coarseness"], e["effective_basin_count_mean"],
            e["dominant_basin_fraction_mean"], e["mean_frustration_mean"]))
    assert len(rows) == 6 * 2 * 5
    assert all(r["basin_count"] >= 1 for r in rows)


# ---------------------------------------------------------------------------
# Sharpening (b) -- oscillation/abandonment AT the tested N values, correlated
# against the SAME seeds' basin-sweep numbers (PREREG SS3(b)).
# ---------------------------------------------------------------------------
# PHASE A (native-backend cutover): _experiment_oscillation and
# test_sharpening_b_oscillation_at_tested_n were REMOVED. They correlated the
# continuous mean-field synchronous-update oscillation probe (_oscillates,
# built on the removed mt_mean_field_marginal + its `damping` knob) with
# basin degradation. The discrete-async native engine has no synchronous
# 2-cycle and no damping parameter, so there is no discrete analog — these
# tested the removed engine itself, not a surviving feature. The other four
# experiments (A/B/C/sharpening-a) survive: they use _basin_sweep, which is
# re-pointed to the native discrete multi-start in test_can_belief_
# quantization.py.
# ---------------------------------------------------------------------------
