#!/usr/bin/env python3
"""THE STREAM — a bounded budget spent by SALIENCE x SCALE (confirmatory run).

Pre-registration: VISION_STREAM_PREREG.md (committed BEFORE this run, §3). The
percept is STREAMED, not delivered all-at-once: coarse-to-fine by scale (large
structure first), allocated by salience (the bounded budget goes to the
largest-residual region first), and PREEMPTIBLE (a majority-mass 'spear' drains
the budget, the rest degrades to the render — tunnel vision). ONE water-filling
seed rule (stream_resolve_salient) over a residual-mass region field; coarse-first,
budget-allocation and preemption all fall OUT of the Argmax + counted-down budget,
with ZERO magic numbers (no preemption threshold, §13).

NO Python decides a percept: the salience order, the budget spend and the
preemption are the vision_stream RULE (run_rules fixpoint). This runner only
CONSTRUCTS scenes and READS the stream order back (mechanical I/O, §0), and
COMPUTES metrics OVER the stream (measurement, not decision).

Run from the gamma-substrate dir:
    PYTHONPATH=runners/dsl/python:. python scripts/stream_measure.py
"""
from __future__ import annotations
import json
import math
import os
import random
import time

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import stream_world as sw  # noqa: E402


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_stream"])
    return s, ag


def _stream(s, budget, regions):
    """Build a scene, turn the stream ON, run to fixpoint, read order back."""
    h = sw.add_scene(s, budget=budget, regions=regions)
    sw.set_stream(s, 1.0)
    sw.run(s)
    return h


def _mass(regions, idxs):
    return sum(regions[i]["residual"] for i in idxs)


# --------------------------------------------------------------------------- #
#  The generic tunnel detector (READOUT, used by arm C AND the floor).
#  A tunnel = the budget was fully spent, some field remains unseen, and the
#  RESOLVED regions hold the MAJORITY of the field's residual mass (the budget
#  concentrated onto the dominant mass, leaving the rest unseen). Majority is the
#  scale-free definition of dominance — a readout over the percept, NOT a rule
#  threshold (the rule has none, §13).
# --------------------------------------------------------------------------- #
def tunnel(regions, order, spent, budget):
    resolved = [i for i, o in enumerate(order) if o >= 0]
    unresolved = [i for i, o in enumerate(order) if o < 0]
    if spent != budget:
        return False
    if not unresolved:                 # budget covered the whole field: no tunnel
        return False
    return _mass(regions, resolved) >= _mass(regions, unresolved)


def _monotone_inversions(regions, order):
    """# of inversions: a resolved region streamed AFTER a lower-residual one."""
    resolved = sorted((i for i, o in enumerate(order) if o >= 0),
                      key=lambda i: order[i])
    inv = 0
    for a in range(len(resolved)):
        for b in range(a + 1, len(resolved)):
            if regions[resolved[a]]["residual"] < regions[resolved[b]]["residual"]:
                inv += 1
    return inv


# =========================================================================== #
#  ARM A — COARSE-FIRST (scale): large structure streams in first
# =========================================================================== #
def arm_coarse_first():
    s, _ = _boot()
    coarse = [dict(rrow=0, rcol=i, scale=0, residual=r)
              for i, r in enumerate([30, 25, 20])]
    fine = [dict(rrow=1, rcol=i, scale=1, residual=r)
            for i, r in enumerate([6, 5, 4, 3, 2, 1])]
    regions = coarse + fine
    B = len(coarse)                                     # PARTIAL budget
    h = _stream(s, B, regions)
    order = sw.read_order(s, h)
    spent = sw.read_spent(s, h)
    resolved = [i for i, o in enumerate(order) if o >= 0]
    unresolved = [i for i, o in enumerate(order) if o < 0]
    res_resolved = [regions[i]["residual"] for i in resolved]
    res_unres = [regions[i]["residual"] for i in unresolved]
    coarse_idx = set(range(len(coarse)))
    passed = (set(resolved) == coarse_idx
              and all(o < 0 for i, o in enumerate(order) if i >= len(coarse))
              and (min(res_resolved) > max(res_unres))
              and _monotone_inversions(regions, order) == 0
              and spent == B)
    return {"arm": "A_coarse_first", "pass": bool(passed), "budget": B,
            "spent": spent, "order": order,
            "resolved_residuals": res_resolved, "unresolved_residuals": res_unres,
            "inversions": _monotone_inversions(regions, order)}


# =========================================================================== #
#  ARM B — BUDGET-ALLOCATION (salience): the budget goes where the surprise is
# =========================================================================== #
def arm_budget_allocation():
    s, _ = _boot()
    # 7 low-residual rest (rcol 0..6) + the salient region placed LAST (rcol 7).
    rest = [dict(rrow=0, rcol=i, scale=0, residual=r)
            for i, r in enumerate([7, 6, 5, 4, 3, 2, 1])]
    salient = dict(rrow=0, rcol=7, scale=0, residual=50)
    regions = rest + [salient]
    sal_idx = len(regions) - 1
    B = 3
    h = _stream(s, B, regions)
    order = sw.read_order(s, h)
    spent = sw.read_spent(s, h)
    resolved = [i for i, o in enumerate(order) if o >= 0]
    # salience spend: salient resolved FIRST (order 0) + top-B by residual.
    top_b = set(sorted(range(len(regions)),
                       key=lambda i: -regions[i]["residual"])[:B])
    salience_ok = (order[sal_idx] == 0 and set(resolved) == top_b and spent == B)
    # uniform-spend CONTROL (residual-blind row-major, same budget): salient NOT hit.
    uni = sw.uniform_spend(h, B)
    uniform_leaves_salient = sal_idx not in uni
    passed = salience_ok and uniform_leaves_salient
    return {"arm": "B_budget_allocation", "pass": bool(passed), "budget": B,
            "spent": spent, "salient_order": order[sal_idx],
            "salience_resolved": sorted(resolved),
            "uniform_resolved": uni,
            "uniform_leaves_salient": bool(uniform_leaves_salient)}


# =========================================================================== #
#  ARM C — PREEMPTION / TUNNEL (the spear): "you see very little else"
# =========================================================================== #
def _spear_scene(spear_residual):
    spear = [dict(rrow=0, rcol=i, scale=0, residual=spear_residual) for i in range(4)]
    periphery = [dict(rrow=5, rcol=i, scale=2, residual=1) for i in range(10)]
    return spear, periphery


def arm_preemption():
    B = 4
    # WITH spear (looming, majority mass).
    s, _ = _boot()
    spear, periphery = _spear_scene(spear_residual=100)
    regions = spear + periphery
    h = _stream(s, B, regions)
    order = sw.read_order(s, h)
    spent = sw.read_spent(s, h)
    spear_idx = set(range(len(spear)))
    periph_idx = set(range(len(spear), len(regions)))
    periph_resolved_with = sum(1 for i in periph_idx if order[i] >= 0)
    all_budget_on_spear = all(order[i] >= 0 for i in spear_idx) and periph_resolved_with == 0
    fired = tunnel(regions, order, spent, B)
    # WITHOUT spear (peak removed: spear residual 0 -> inert), SAME periphery.
    s2, _ = _boot()
    spear0, periphery0 = _spear_scene(spear_residual=0)
    regions0 = spear0 + periphery0
    h0 = _stream(s2, B, regions0)
    order0 = sw.read_order(s2, h0)
    spent0 = sw.read_spent(s2, h0)
    periph_resolved_without = sum(1 for i in range(len(spear0), len(regions0))
                                  if order0[i] >= 0)
    no_tunnel_without = not tunnel(regions0, order0, spent0, B)
    passed = (fired and all_budget_on_spear
              and periph_resolved_with == 0
              and periph_resolved_without > 0
              and no_tunnel_without)
    return {"arm": "C_preemption", "pass": bool(passed), "budget": B,
            "tunnel_with_spear": bool(fired),
            "periphery_resolved_with_spear": periph_resolved_with,
            "periphery_resolved_without_spear": periph_resolved_without,
            "no_tunnel_without_spear": bool(no_tunnel_without)}


# =========================================================================== #
#  ARM D — ANTI-OVERFIT FLOOR (not a universal salience-hallucinator)
# =========================================================================== #
def arm_floor(n=100, seed0=33000):
    # F1 — a ZERO-residual field spends 0 (deterministic).
    s, _ = _boot()
    zero = [dict(rrow=r, rcol=c, scale=0, residual=0) for r in range(10) for c in range(10)]
    hz = _stream(s, 8, zero)
    f1_spent = sw.read_spent(s, hz)
    f1_ok = (f1_spent == 0)
    # F2/F3 — 100 random iid-noise fields, seeds 33000..33099.
    B = 4
    false_tunnels = 0
    inversions_total = 0
    monotone_ok_count = 0
    for k in range(n):
        rng = random.Random(seed0 + k)
        regions = [dict(rrow=r, rcol=c, scale=0, residual=rng.randint(1, 10))
                   for r in range(10) for c in range(10)]
        s2, _ = _boot()
        h = _stream(s2, B, regions)
        order = sw.read_order(s2, h)
        spent = sw.read_spent(s2, h)
        if tunnel(regions, order, spent, B):
            false_tunnels += 1
        inv = _monotone_inversions(regions, order)
        inversions_total += inv
        if inv == 0:
            monotone_ok_count += 1
    passed = (f1_ok and false_tunnels == 0)
    return {"arm": "D_floor", "pass": bool(passed), "n": n,
            "f1_zero_field_spent": f1_spent, "f1_ok": bool(f1_ok),
            "f2_false_tunnels": false_tunnels,
            "f3_monotone_ok": monotone_ok_count,
            "f3_total_inversions": inversions_total}


# =========================================================================== #
#  ARM E — COMPUTE-BOUNDED (bounded spend + fixed-budget locality + cost fit)
# =========================================================================== #
def arm_compute():
    # C1 — spent == min(B, N_positive) EXACTLY, across arms A/B/C shapes.
    c1 = []
    for (label, B, residuals) in [
        ("A", 3, [30, 25, 20, 6, 5, 4, 3, 2, 1]),   # N_pos=9, min(3,9)=3
        ("B", 3, [7, 6, 5, 4, 3, 2, 1, 50]),        # N_pos=8, min(3,8)=3
        ("full", 5, [4, 3, 2, 1]),                  # N_pos=4, min(5,4)=4 (budget>field)
    ]:
        s, _ = _boot()
        regions = [dict(rrow=0, rcol=i, scale=0, residual=r)
                   for i, r in enumerate(residuals)]
        h = _stream(s, B, regions)
        spent = sw.read_spent(s, h)
        n_pos = sum(1 for r in residuals if r > 0)
        c1.append({"case": label, "budget": B, "n_positive": n_pos,
                   "spent": spent, "ok": spent == min(B, n_pos)})
    c1_ok = all(x["ok"] for x in c1)

    # C2 — fixed budget, vary N: resolved-count is FLAT in N (== B).
    B = 4
    c2 = []
    sizes = [16, 64, 256, 1024]
    times = []
    for N in sizes:
        s, _ = _boot()
        regions = [dict(rrow=i // 32, rcol=i % 32, scale=0, residual=(i % 97) + 1)
                   for i in range(N)]
        t0 = time.perf_counter()
        h = _stream(s, B, regions)
        dt = time.perf_counter() - t0
        spent = sw.read_spent(s, h)
        c2.append({"N": N, "spent": spent, "time_s": dt})
        times.append(dt)
    c2_ok = all(x["spent"] == B for x in c2)

    # C3 — descriptive log-log exponent of tick cost vs N at fixed B (UNGATED).
    xs = [math.log(N) for N in sizes]
    ys = [math.log(t) for t in times]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom if denom else float("nan")

    passed = c1_ok and c2_ok
    return {"arm": "E_compute", "pass": bool(passed),
            "c1_bounded_spend": c1, "c1_ok": bool(c1_ok),
            "c2_fixed_budget_flat": c2, "c2_ok": bool(c2_ok),
            "c3_cost_exponent": slope}


# =========================================================================== #
#  §9 OFF-day — the seed is inert with the flag OFF (default).
# =========================================================================== #
def arm_offday():
    s, _ = _boot()
    regions = [dict(rrow=0, rcol=i, scale=0, residual=r)
               for i, r in enumerate([30, 20, 10])]
    h = sw.add_scene(s, budget=3, regions=regions)
    # DO NOT set the flag (default 0.0).
    sw.run(s)
    spent = sw.read_spent(s, h)
    order = sw.read_order(s, h)
    passed = (spent == 0 and all(o < 0 for o in order))
    return {"arm": "X_offday", "pass": bool(passed), "spent": spent, "order": order}


def main():
    t0 = time.time()
    prov = provenance_line()
    print("PROVENANCE:", prov)
    arms = [arm_coarse_first(), arm_budget_allocation(), arm_preemption(),
            arm_compute(), arm_offday(), arm_floor()]
    out = {"provenance": prov, "arms": arms,
           "elapsed_s": round(time.time() - t0, 1)}
    os.makedirs("results", exist_ok=True)
    with open("results/stream_measure.json", "w") as f:
        json.dump(out, f, indent=2)
    print()
    for a in arms:
        print(f"  {a['arm']:22s} {'PASS' if a['pass'] else 'FAIL'}")
    print(f"\n  elapsed {out['elapsed_s']}s -> results/stream_measure.json")


if __name__ == "__main__":
    main()
