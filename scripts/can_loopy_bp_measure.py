"""Measurement script for CAN_LOOPY_BP_PREREG.md / _RESULTS.md.

Compares four solvers on the SAME real stress-test networks
`CAN_SOLVER_TRACTABILITY_RESULTS.md` used:

  1. single discrete-async settle (baseline)
  2. multi_start_settle_and_pick_best (K=20, existing tool)
  3. loopy BP, max-product (this rung's PRIMARY variant)
  4. loopy BP, sum-product (this rung's measured comparison variant)

on (a) N=16 complete-graph frustrated/dense draws and (b) real Bigville
residents (sparse, treewidth 2). Reports convergence and
`mt_frustration_given_state` for each. WORLD-ADAPTER / MEASUREMENT
script only -- no agent decision logic; every branch here is fixed
analysis code operating on already-computed numbers or mechanically
re-seeding graph state for a fresh trial.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate_rs import _native                                    # noqa: E402
from substrate.seed_loader import engine_rules_only                 # noqa: E402
from domains.can_native_orchestration import (                      # noqa: E402
    scoped_settle, native_marginal_from_state, multi_start_settle_and_pick_best,
)
from domains.can_native_bp import run_loopy_bp                      # noqa: E402
from worlds.bigville_can_beliefs import (                           # noqa: E402
    install_productions, build_resident_can_mt, apply_scenario_evidence,
)

NATIVE_SEED_PATH = os.path.join(_ROOT, "seeds", "can_native_reimplementation.json")
CAST_PATH = os.path.join(_ROOT, "seeds", "bigville_cast100.json")

N16_DRAWS = 8
"""Smaller than CAN_SOLVER_TRACTABILITY_RESULTS.md's own 30 -- BP is
materially more expensive per network (real, measured wall-clock cost,
not assumed). Reported plainly, not implied to match the prior rung's
n."""
N16_MAX_ROUNDS = 60
BIGVILLE_N_RESIDENTS = 15
BIGVILLE_MAX_ROUNDS = 40


def _round_to_vocab(x, granularity, half_width):
    k = round(x / granularity)
    k = max(-half_width, min(half_width, k))
    return k * granularity


def _build_n16_draw(s, seed, coarse=True, discrete_mode="3state"):
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


def _loaded_native_substrate():
    s = _native.Substrate()
    manifest = json.load(open(NATIVE_SEED_PATH))
    s.load_seed_manifest(engine_rules_only(manifest))
    return s


def _row_n16(seed, coarse, max_rounds):
    s = _loaded_native_substrate()
    mt, concepts = _build_n16_draw(s, seed, coarse)

    t0 = time.time()
    scoped_settle(s, mt)
    baseline_state = native_marginal_from_state(s, mt)
    baseline_f = float(s.mt_frustration_given_state(mt, baseline_state))
    t_baseline = time.time() - t0

    # multi-start needs a FRESH copy of the same network (it re-seeds
    # `state` itself) -- rebuild rather than reuse the now-settled graph.
    s2 = _loaded_native_substrate()
    mt2, concepts2 = _build_n16_draw(s2, seed, coarse)
    t0 = time.time()
    ms_result = multi_start_settle_and_pick_best(s2, mt2, k_starts=20, rng=random.Random(seed + 5000))
    t_multistart = time.time() - t0

    s3 = _loaded_native_substrate()
    mt3, concepts3 = _build_n16_draw(s3, seed, coarse)
    t0 = time.time()
    bp_max = run_loopy_bp(s3, mt3, combine="max_product", max_rounds=max_rounds)
    t_bp_max = time.time() - t0
    bp_max_f = float(s3.mt_frustration_given_state(mt3, bp_max["final_state"]))

    s4 = _loaded_native_substrate()
    mt4, concepts4 = _build_n16_draw(s4, seed, coarse)
    t0 = time.time()
    bp_sum = run_loopy_bp(s4, mt4, combine="sum_product", max_rounds=max_rounds)
    t_bp_sum = time.time() - t0
    bp_sum_f = float(s4.mt_frustration_given_state(mt4, bp_sum["final_state"]))

    row = {
        "seed": seed, "coarse": coarse,
        "baseline_frustration": baseline_f, "t_baseline": t_baseline,
        "multistart_frustration": float(ms_result["frustration"]), "t_multistart": t_multistart,
        "bp_max_frustration": bp_max_f, "bp_max_converged": bp_max["converged"],
        "bp_max_rounds": bp_max["rounds"], "t_bp_max": t_bp_max,
        "bp_sum_frustration": bp_sum_f, "bp_sum_converged": bp_sum["converged"],
        "bp_sum_rounds": bp_sum["rounds"], "t_bp_sum": t_bp_sum,
    }
    print(f"  seed={seed} coarse={coarse} baseline={baseline_f:.1f} "
          f"multistart={ms_result['frustration']:.1f} "
          f"bp_max={bp_max_f:.1f}(conv={bp_max['converged']},r={bp_max['rounds']}) "
          f"bp_sum={bp_sum_f:.1f}(conv={bp_sum['converged']},r={bp_sum['rounds']}) "
          f"[t: base={t_baseline:.2f}s ms={t_multistart:.2f}s "
          f"bpmax={t_bp_max:.2f}s bpsum={t_bp_sum:.2f}s]")
    return row


def measure_n16():
    print(f"\n=== N=16 frustrated/dense, {N16_DRAWS} draws, max_rounds={N16_MAX_ROUNDS} ===")
    rows = []
    for seed in range(N16_DRAWS):
        rows.append(_row_n16(5000 + seed, True, N16_MAX_ROUNDS))
    return rows


def _row_bigville(resident, max_rounds):
    s = _native.Substrate()
    install_productions(s)
    manifest = json.load(open(NATIVE_SEED_PATH))
    s.load_seed_manifest(engine_rules_only(manifest))
    built = build_resident_can_mt(s, resident)
    apply_scenario_evidence(s, built["concepts"])
    s.set_attr(built["mt_node"], "discrete_mode", "3state")
    s.set_attr(built["mt_node"], "can_tick", 0)
    mt = built["mt_node"]

    t0 = time.time()
    steps = s.run_rules(3000)
    baseline_state = {c.value: float(s.node(c)["attrs"].get("state", 0.0))
                       for c in built["concepts"].values()}
    baseline_f = float(s.mt_frustration_given_state(mt, baseline_state))
    t_baseline = time.time() - t0

    def _fresh():
        s2 = _native.Substrate()
        install_productions(s2)
        s2.load_seed_manifest(engine_rules_only(manifest))
        built2 = build_resident_can_mt(s2, resident)
        apply_scenario_evidence(s2, built2["concepts"])
        s2.set_attr(built2["mt_node"], "discrete_mode", "3state")
        s2.set_attr(built2["mt_node"], "can_tick", 0)
        return s2, built2["mt_node"]

    s2, mt2 = _fresh()
    t0 = time.time()
    ms_result = multi_start_settle_and_pick_best(s2, mt2, k_starts=20, rng=random.Random(resident["index"] + 6000))
    t_multistart = time.time() - t0

    s3, mt3 = _fresh()
    t0 = time.time()
    bp_max = run_loopy_bp(s3, mt3, combine="max_product", max_rounds=max_rounds)
    t_bp_max = time.time() - t0
    bp_max_f = float(s3.mt_frustration_given_state(mt3, bp_max["final_state"]))

    s4, mt4 = _fresh()
    t0 = time.time()
    bp_sum = run_loopy_bp(s4, mt4, combine="sum_product", max_rounds=max_rounds)
    t_bp_sum = time.time() - t0
    bp_sum_f = float(s4.mt_frustration_given_state(mt4, bp_sum["final_state"]))

    row = {
        "resident_index": resident["index"],
        "resolution_bins": resident["params"]["resolution_bins"],
        "baseline_frustration": baseline_f,
        "multistart_frustration": float(ms_result["frustration"]),
        "bp_max_frustration": bp_max_f, "bp_max_converged": bp_max["converged"],
        "bp_max_rounds": bp_max["rounds"],
        "bp_sum_frustration": bp_sum_f, "bp_sum_converged": bp_sum["converged"],
        "bp_sum_rounds": bp_sum["rounds"],
    }
    print(f"  resident#{resident['index']} baseline={baseline_f:.2f} "
          f"multistart={ms_result['frustration']:.2f} "
          f"bp_max={bp_max_f:.2f}(conv={bp_max['converged']},r={bp_max['rounds']}) "
          f"bp_sum={bp_sum_f:.2f}(conv={bp_sum['converged']},r={bp_sum['rounds']})")
    return row


def measure_bigville():
    print(f"\n=== Bigville real residents, n={BIGVILLE_N_RESIDENTS}, "
          f"max_rounds={BIGVILLE_MAX_ROUNDS} ===")
    all_residents = json.load(open(CAST_PATH))["residents"]
    by_bins = sorted(all_residents, key=lambda r: (r["params"]["resolution_bins"], r["index"]))
    lo = by_bins[:5]
    hi = by_bins[-5:]
    mid_rng = random.Random(20260814)
    remaining = [r for r in all_residents if r not in lo and r not in hi]
    mid = mid_rng.sample(remaining, 5)
    sample = lo + hi + mid
    rows = []
    for resident in sample:
        rows.append(_row_bigville(resident, BIGVILLE_MAX_ROUNDS))
    return rows


def _summ(rows, key):
    vals = [r[key] for r in rows]
    return sum(vals) / len(vals) if vals else 0.0


def main():
    out = {}
    rows_n16 = measure_n16()
    out["n16"] = rows_n16
    rows_bv = measure_bigville()
    out["bigville"] = rows_bv

    print("\n=== SUMMARY: N=16 frustrated ===")
    print(f"n={len(rows_n16)}")
    print(f"mean baseline_frustration={_summ(rows_n16,'baseline_frustration'):.3f}")
    print(f"mean multistart_frustration={_summ(rows_n16,'multistart_frustration'):.3f}")
    print(f"mean bp_max_frustration={_summ(rows_n16,'bp_max_frustration'):.3f} "
          f"converged_frac={sum(r['bp_max_converged'] for r in rows_n16)/len(rows_n16):.2f}")
    print(f"mean bp_sum_frustration={_summ(rows_n16,'bp_sum_frustration'):.3f} "
          f"converged_frac={sum(r['bp_sum_converged'] for r in rows_n16)/len(rows_n16):.2f}")
    n_bp_max_beats_ms = sum(1 for r in rows_n16 if r['bp_max_frustration'] < r['multistart_frustration'] - 1e-9)
    n_bp_max_ties_ms = sum(1 for r in rows_n16 if abs(r['bp_max_frustration'] - r['multistart_frustration']) < 1e-9)
    n_bp_max_worse_ms = sum(1 for r in rows_n16 if r['bp_max_frustration'] > r['multistart_frustration'] + 1e-9)
    print(f"bp_max vs multistart: beats={n_bp_max_beats_ms} ties={n_bp_max_ties_ms} worse={n_bp_max_worse_ms}")
    n_max_beats_sum = sum(1 for r in rows_n16 if r['bp_max_frustration'] < r['bp_sum_frustration'] - 1e-9)
    n_max_ties_sum = sum(1 for r in rows_n16 if abs(r['bp_max_frustration'] - r['bp_sum_frustration']) < 1e-9)
    n_max_worse_sum = sum(1 for r in rows_n16 if r['bp_max_frustration'] > r['bp_sum_frustration'] + 1e-9)
    print(f"bp_max vs bp_sum: max_product_better={n_max_beats_sum} ties={n_max_ties_sum} max_product_worse={n_max_worse_sum}")

    print("\n=== SUMMARY: Bigville real residents ===")
    print(f"n={len(rows_bv)}")
    print(f"mean baseline_frustration={_summ(rows_bv,'baseline_frustration'):.3f}")
    print(f"mean multistart_frustration={_summ(rows_bv,'multistart_frustration'):.3f}")
    print(f"mean bp_max_frustration={_summ(rows_bv,'bp_max_frustration'):.3f} "
          f"converged_frac={sum(r['bp_max_converged'] for r in rows_bv)/len(rows_bv):.2f}")
    print(f"mean bp_sum_frustration={_summ(rows_bv,'bp_sum_frustration'):.3f} "
          f"converged_frac={sum(r['bp_sum_converged'] for r in rows_bv)/len(rows_bv):.2f}")

    with open(os.path.join(_ROOT, "scripts", "can_loopy_bp_measure_results.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    print("\nwrote scripts/can_loopy_bp_measure_results.json")


if __name__ == "__main__":
    main()
