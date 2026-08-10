#!/usr/bin/env python3
"""BORDER-OWNERSHIP / PROTO-OBJECT — the confirmatory run.

Pre-registration: VISION_BORDER_OWNERSHIP_PREREG.md (committed BEFORE this run, §3).
A local edge becomes a DIRECTED boundary that OWNS its figure; a bounded, owned,
PRE-IDENTITY region is minted as a ProtoObject. The surroundedness flood, the
component labelling, the figure/ground DECISION, the proto minting and the directed
ownership are ALL in the vision_border_ownership seed rules; this runner only
CONSTRUCTS value grids and READS bg / owns / owns_figure / ProtoObject back
(mechanical I/O, §0), and TALLIES metrics over them.

Run from the gamma-substrate dir:  python scripts/border_ownership_measure.py
"""
from __future__ import annotations
import json
import os
import random
import time

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import border_ownership_world as bow  # noqa: E402

H = W = 12


# WHICH mint predicate the synthetic arms exercise (seed v1.1.0). 0.0 = the
# incumbent `bo_mint_enclosed` (isolation / G_figadj); 1.0 = the competitive
# `bo_mint_owned`. Every arm boots through `_boot`, so this one knob re-runs the
# WHOLE synthetic gate under either predicate -- which is how constraint 1 ("the
# synthetic gate must stay 9/9") is tested SUBSTANTIVELY rather than trivially
# satisfied by the flag's 0.0 default. Set by
# tests/test_border_ownership_owned_migrated.py; never read by a rule.
BOWN_OWN_DEFAULT = 0.0

# Likewise for the WELL-POSEDNESS conjunct (seed v1.2.0), so the same nine arms
# can be re-run with `bown_wp` armed -- the constraint that the discriminator
# must not buy a clean negative control with false negatives. Set by
# tests/test_border_ownership_wellposed_migrated.py; never read by a rule.
BOWN_WP_DEFAULT = 0.0


def _boot(grid, *, bown=1.0, bown_own=None, bown_wp=None):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    h = bow.add_field(s, grid)
    bow.set_flag(s, bown=bown,
                 bown_own=BOWN_OWN_DEFAULT if bown_own is None else bown_own,
                 bown_wp=BOWN_WP_DEFAULT if bown_wp is None else bown_wp)
    return s, h


def _blank():
    return [[0] * W for _ in range(H)]


# ---- HEADLINE: the Zhou context-dependence flip -------------------------------
def arm_zhou():
    # Config A: val-1 bar rows3..8 cols3..5 enclosed (figure LEFT of the test edge).
    gA = _blank()
    for r in range(3, 9):
        for c in range(3, 6):
            gA[r][c] = 1
    # Config B: val-0 block rows3..8 cols6..8 enclosed, val-1 surround (figure RIGHT).
    gB = [[1] * W for _ in range(H)]
    for r in range(3, 9):
        for c in range(6, 9):
            gB[r][c] = 0
    # the test edge is between (5,5)=1 and (5,6)=0; assert the local window identical.
    winA = [[gA[r][c] for c in range(4, 8)] for r in range(4, 7)]
    winB = [[gB[r][c] for c in range(4, 8)] for r in range(4, 7)]
    window_identical = (winA == winB)

    sA, hA = _boot(gA); bow.tick(sA)
    sB, hB = _boot(gB); bow.tick(sB)
    A = (bow.owns(sA, hA, 5, 5), bow.owns(sA, hA, 5, 6))
    B = (bow.owns(sB, hB, 5, 5), bow.owns(sB, hB, 5, 6))
    tA = bow.owns_figure_target(sA, hA, 5, 5)   # A: left owns -> its proto root
    tB = bow.owns_figure_target(sB, hB, 5, 6)   # B: right owns -> its proto root
    flipped = (A == (1, 0) and B == (0, 1))
    passed = (window_identical and flipped and tA is not None and tB is not None)
    return {"window_identical": window_identical, "local_window": winA,
            "A_owns_55_56": list(A), "B_owns_55_56": list(B),
            "A_left_target": tA, "B_right_target": tB,
            "flipped": flipped, "pass": passed}


# ---- FIGURE-GROUND on a closed figure -----------------------------------------
def arm_figure_ground():
    g = _blank()
    for r in range(3, 9):
        for c in range(4, 8):
            g[r][c] = 1
    s, h = _boot(g); bow.tick(s)
    protos = bow.protos(s)
    perimeter = [(r, c) for r in range(3, 9) for c in range(4, 8)
                 if r in (3, 8) or c in (4, 7)]
    interior = [(r, c) for r in range(4, 8) for c in range(5, 7)]
    all_perimeter_own = all(bow.owns(s, h, r, c) == 1 for r, c in perimeter)
    all_perimeter_target = all(bow.owns_figure_target(s, h, r, c) == 40
                               for r, c in perimeter)
    no_interior_own = all(bow.owns(s, h, r, c) == 0 for r, c in interior)
    surround_ground = (bow.bg(s, h, 0, 0) == 1 and bow.owns(s, h, 0, 0) == 0)
    passed = (len(protos) == 1 and protos[0]["members"] == 24
              and protos[0]["gestalt"] == 0
              and all_perimeter_own and all_perimeter_target
              and no_interior_own and surround_ground)
    return {"n_protos": len(protos), "protos": protos,
            "all_perimeter_own": all_perimeter_own,
            "all_perimeter_target_is_proto": all_perimeter_target,
            "no_interior_own": no_interior_own,
            "surround_is_ground": surround_ground, "pass": passed}


# ---- RECURRENCE / global consistency (the fixpoint) ---------------------------
def _plus():
    gp = _blank()
    for r in range(2, 10):
        gp[r][6] = 1
    for c in range(2, 10):
        gp[6][c] = 1
    return gp


def arm_recurrence():
    # fixpoint
    s, h = _boot(_plus())
    sweeps = s.tick()
    owned = bow.owned_proto_roots(s, h)
    K = len(owned)
    protos = bow.protos(s)
    bg_full = sum(1 for nid in h["cell_ids"]
                  if float(s.node(nid)["attrs"]["bg"]) > 0.5)
    # sweep truncations: the flood grows monotonically; proto/ownership only at fixpoint
    trunc = {}
    for k in (2, 4, 6):
        st, ht = _boot(_plus())
        st.tick(k)
        bgk = sum(1 for nid in ht["cell_ids"]
                  if float(st.node(nid)["attrs"]["bg"]) > 0.5)
        trunc[k] = {"bg_set": bgk, "n_protos": bow.n_protos(st)}
    monotone = (trunc[2]["bg_set"] < trunc[4]["bg_set"] < trunc[6]["bg_set"] < bg_full)
    load_bearing = (trunc[2]["n_protos"] == 0 and trunc[4]["n_protos"] == 0
                    and len(protos) == 1)
    passed = (sweeps > 1 and K == 1 and len(protos) == 1 and monotone and load_bearing)
    return {"sweeps": sweeps, "distinct_owned_roots": K, "owned_roots": sorted(owned),
            "n_protos": len(protos), "members": protos[0]["members"] if protos else 0,
            "bg_full": bg_full, "truncations": trunc,
            "flood_monotone": monotone, "recurrence_load_bearing": load_bearing,
            "pass": passed}


# ---- GESTALT SIZE (load-bearing, ambiguous bipartition) -----------------------
def _split(kL, vL=1, vR=0):
    """cols < kL get vL, else vR — one vertical contour, both regions frame-touching."""
    return [[vL if c < kL else vR for c in range(W)] for _ in range(H)]


def arm_size():
    # left smaller (cols0..3 = 48) vs right (cols4..11 = 96) -> figure = LEFT
    sL, hL = _boot(_split(4)); bow.tick(sL)
    pL = bow.protos(sL)
    left_fig = (len(pL) == 1 and pL[0]["gestalt"] == 1 and pL[0]["members"] == 48
                and bow.owns(sL, hL, 5, 3) == 1 and pL[0]["root"] == 0)
    # SWAP: right smaller (cols0..7 = 96 left, cols8..11 = 48 right) -> figure = RIGHT
    sR, hR = _boot(_split(8)); bow.tick(sR)
    pR = bow.protos(sR)
    right_fig = (len(pR) == 1 and pR[0]["gestalt"] == 1 and pR[0]["members"] == 48
                 and bow.owns(sR, hR, 5, 8) == 1 and pR[0]["root"] == 8)
    # figure TRACKS size across the swap (load-bearing): not the same position
    tracks = left_fig and right_fig and (pL[0]["root"] != pR[0]["root"])
    return {"left_smaller_proto": pL, "right_smaller_proto": pR,
            "left_is_figure": left_fig, "right_is_figure": right_fig,
            "figure_tracks_size": tracks, "pass": tracks}


# ---- GESTALT CONVEXITY (EXPLORATORY, reported — NOT a claimed pass) ------------
def arm_convexity():
    # two equal-size non-enclosed regions (symmetric split, 72 vs 72). My mechanism
    # holds equal-size ties OPEN (anti-confabulation); convexity-as-tiebreaker is NOT
    # wired. So this REPORTS 0 protos (held open) and names convexity a frontier.
    s, h = _boot(_split(6)); bow.tick(s)
    n = bow.n_protos(s)
    return {"n_protos": n, "held_open": (n == 0),
            "note": "convexity-as-tiebreaker NOT implemented; equal-size ambiguity is "
                    "held open (anti-confabulation). Convexity is a NAMED FRONTIER "
                    "(needs diagonal corner logic); reported honestly, not claimed.",
            "exploratory": True}


# ---- ANTI-OVERFIT floor -------------------------------------------------------
def arm_floor_open():
    # an open horizontal bar rows5..6 cols0..11 (touches frame) -> not enclosed, >=3
    # components -> no proto, nothing owned.
    g = _blank()
    for r in (5, 6):
        for c in range(W):
            g[r][c] = 1
    s, h = _boot(g); bow.tick(s)
    owned = bow.owned_proto_roots(s, h)
    passed = (bow.n_protos(s) == 0 and len(owned) == 0)
    return {"n_protos": bow.n_protos(s), "owned_roots": sorted(owned), "pass": passed}


def arm_floor_ambiguous():
    # symmetric bipartition (72/72) — equal size, held open.
    s, h = _boot(_split(6)); bow.tick(s)
    passed = (bow.n_protos(s) == 0)
    return {"n_protos": bow.n_protos(s), "held_open": passed, "pass": passed}


def arm_floor_noise(n_seeds=100, base_seed=36000):
    false_fields = 0
    detail = []
    for i in range(n_seeds):
        seed = base_seed + i
        rng = random.Random(seed)
        g = [[rng.randint(0, 99) for _ in range(W)] for _ in range(H)]
        s, h = _boot(g); bow.tick(s)
        k = bow.n_protos(s)
        if k > 0:
            false_fields += 1
            detail.append({"seed": seed, "n_protos": k, "protos": bow.protos(s)})
    return {"n_seeds": n_seeds, "seed_range": [base_seed, base_seed + n_seeds - 1],
            "false_mint_fields": false_fields, "detail": detail,
            "pass": (false_fields == 0)}


# ---- §9 OFF-DAY ---------------------------------------------------------------
def arm_offday():
    g = _blank()
    for r in range(3, 9):
        for c in range(4, 8):
            g[r][c] = 1
    s, h = _boot(g, bown=0.0)   # flag OFF (also the default)
    bow.tick(s)
    max_bg = max(bow.cell_attr(s, h, r, c, "bg") for r in range(H) for c in range(W))
    max_owns = max(bow.cell_attr(s, h, r, c, "owns") for r in range(H) for c in range(W))
    passed = (bow.n_protos(s) == 0 and max_bg == 0.0 and max_owns == 0.0)
    return {"n_protos": bow.n_protos(s), "max_bg": max_bg, "max_owns": max_owns,
            "pass": passed}


# ---- SCALING (reported, not gated) --------------------------------------------
def arm_scaling():
    import math
    sizes = [12, 16, 20, 24, 28]
    xs, ys = [], []
    per = {}
    for n in sizes:
        grid = [[0] * n for _ in range(n)]
        lo, hi = n // 4, 3 * n // 4
        for r in range(lo, hi):
            for c in range(lo, hi):
                grid[r][c] = 1
        s, ag = boot_core()
        load_seeds_into(s, ag, ["vision_border_ownership"])
        hh = bow.add_field(s, grid)
        bow.set_flag(s, bown=1.0)
        t0 = time.time()
        s.tick()
        dt = time.time() - t0
        per[n] = {"N": n * n, "seconds": round(dt, 4), "n_protos": bow.n_protos(s)}
        xs.append(math.log(n * n)); ys.append(math.log(max(dt, 1e-6)))
    m = len(xs)
    mx, my = sum(xs) / m, sum(ys) / m
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    p = num / den if den else float("nan")
    return {"per_size": per, "fitted_exponent": round(p, 3),
            "note": "reported not gated; a same-value reachability flood is "
                    "O(N*diameter), diameter ~sqrt(N), so a mild super-linear "
                    "exponent is honest and is NOT the O(N^2) apply_rule_once drive."}


def main():
    t0 = time.time()
    prov = provenance_line()
    results = {
        "provenance": prov,
        "H": H, "W": W,
        "HEADLINE_zhou": arm_zhou(),
        "figure_ground": arm_figure_ground(),
        "recurrence": arm_recurrence(),
        "gestalt_size": arm_size(),
        "gestalt_convexity_EXPLORATORY": arm_convexity(),
        "floor_open": arm_floor_open(),
        "floor_ambiguous": arm_floor_ambiguous(),
        "offday": arm_offday(),
        "scaling": arm_scaling(),
        "floor_noise": arm_floor_noise(),
    }
    confirmatory = ["HEADLINE_zhou", "figure_ground", "recurrence", "gestalt_size",
                    "floor_open", "floor_ambiguous", "offday", "floor_noise"]
    all_pass = all(results[k]["pass"] for k in confirmatory)
    results["ALL_CONFIRMATORY_PASS"] = all_pass
    results["elapsed_s"] = round(time.time() - t0, 2)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "results", "border_ownership_measure.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(prov)
    for k in confirmatory:
        print(f"  {k:20s} pass={results[k]['pass']}")
    print(f"  {'gestalt_convexity':20s} EXPLORATORY held_open="
          f"{results['gestalt_convexity_EXPLORATORY']['held_open']}")
    print(f"  {'scaling':20s} exponent={results['scaling']['fitted_exponent']}")
    print("ALL_CONFIRMATORY_PASS:", all_pass, "| wrote", out, "|",
          results["elapsed_s"], "s")


if __name__ == "__main__":
    main()
