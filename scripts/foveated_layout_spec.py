#!/usr/bin/env python3
"""PART B — the FOVEATED layout, SPEC + SIMULATION (seed block 201000-201999).

The shipped photon eye admits ONLY a uniform az x el receptor grid
(`domains/photon_eye.py`, `_build_2d_retina`: nested `for row in range(n_el):
for col in range(n_az)` with evenly-spaced az/el, no per-receptor position
table; `submit_photons_2d` indexes cells by `flat = row*n_az + col` with a
uniform-grid bounds check). So a live foveated eye is NOT buildable without an
eye change — this is a compute-MODEL of a foveated layout sized to the Part-A
real-time budget, reported HONESTLY as a design+simulation, naming the exact
eye change a live build needs. It fakes no live foveated eye.

Model: a dense 1:1 FOVEAL PATCH (one receptor per Doom pixel — there is no
sub-pixel detail to recover) at the screen centre (the aim point where Doom
enemies appear) + a LOG-POLAR periphery whose receptor density falls ~1/ecc
(the isotropic log-polar property: constant angular samples per ring, rings
spaced geometrically in eccentricity), covering the full frame to the corner
radius. Pure arithmetic; importable; gate-able.
"""
from __future__ import annotations
import json
import math
import os

SCREEN_W, SCREEN_H = 320, 240      # VizDoom RES_320X240 — Doom's own pixel grid
R_MAX = math.hypot(SCREEN_W / 2, SCREEN_H / 2)   # corner radius from centre


def uniform_layout(budget):
    """A uniform 4:3 grid of ~`budget` receptors over the whole screen.
    Returns width/height in cells and px-per-cell (the uniform acuity)."""
    w = round(math.sqrt(budget * SCREEN_W / SCREEN_H))
    h = round(budget / w) if w else 0
    px_per_cell = SCREEN_W / w if w else float("inf")
    return {"cells": w * h, "grid_w": w, "grid_h": h,
            "px_per_cell": round(px_per_cell, 3),
            "central_px_per_cell": round(px_per_cell, 3),
            "coverage": "full frame"}


def foveated_layout(budget, fov_half=15, g=1.15):
    """A 1:1 foveal patch (side 2*fov_half px) + log-polar periphery (coarsening
    ratio g) sized to <= `budget` receptors, covering ecc fov_half..R_MAX.

    Log-polar (isotropic): angular samples/ring N_a = ceil(2*pi/(g-1)); ring
    count K = ceil(log(R_MAX/fov_half)/log(g)); periphery = K*N_a. Foveal patch
    = (2*fov_half)^2 receptors at 1.0 px/receptor. If fov+periphery exceeds the
    budget the foveal patch is shrunk to fit (reported)."""
    def periphery(g):
        N_a = math.ceil(2 * math.pi / (g - 1))
        K = math.ceil(math.log(R_MAX / fov_half) / math.log(g))
        return N_a, K, N_a * K

    N_a, K, peri = periphery(g)
    # GROW the 1:1 foveal patch to fill the budget after reserving the
    # full-frame log-polar periphery (larger budget -> larger 1:1 region), capped
    # at the screen's short side (a 1:1 patch can't exceed the frame).
    foveal_budget = max(0, budget - peri)
    fov_half = min(SCREEN_H // 2, int(math.sqrt(foveal_budget) / 2))
    fov = (2 * fov_half) ** 2
    while fov + peri > budget and fov_half > 1:
        fov_half -= 1
        fov = (2 * fov_half) ** 2
    total = fov + peri
    frame_frac_1to1 = round((2 * fov_half) ** 2 / (SCREEN_W * SCREEN_H), 4)
    return {"cells": total, "budget": budget, "fits": total <= budget,
            "foveal_half_px": fov_half, "foveal_side_px": 2 * fov_half,
            "foveal_receptors": fov, "foveal_px_per_receptor": 1.0,
            "logpolar_spokes": N_a, "logpolar_rings": K,
            "periphery_receptors": peri, "coarsen_ratio_g": g,
            "coverage_to_radius_px": round(R_MAX, 1),
            "frame_fraction_at_1to1": frame_frac_1to1,
            "coverage": "full frame (1:1 centre, ~1/ecc periphery)"}


def payoff(budget, fov_half=15, g=1.15):
    """The foveation payoff at a fixed real-time budget: central acuity gain
    (uniform px/cell / foveal px/receptor) at EQUAL receptor count + equal
    real-time cost, with full-frame coverage preserved."""
    uni = uniform_layout(budget)
    fov = foveated_layout(budget, fov_half=fov_half, g=g)
    gain = uni["central_px_per_cell"] / fov["foveal_px_per_receptor"]
    # enemy-recovery proxy: a Doom enemy sprite ~30 px tall near the horizon
    # centre. cells spanning it = enemy_px / px_per_cell (uniform) vs 1:1 (fov).
    enemy_px = 30.0
    return {"budget": budget, "uniform": uni, "foveated": fov,
            "central_acuity_gain_x": round(gain, 2),
            "enemy_cells_uniform": round(enemy_px / uni["central_px_per_cell"], 1),
            "enemy_cells_foveal": round(enemy_px, 1),
            "note": ("at this budget the foveal patch resolves the central aim "
                     "region at Doom-native 1:1 while the equal-count uniform grid "
                     f"blurs it to {uni['central_px_per_cell']} px/cell — the "
                     "sub-grid wall (152000/153000) lifted for the behaviourally-"
                     "relevant central target, same receptor count, same cost.")}


def build_gap():
    return {
        "eye_supports_nonuniform": False,
        "why": ("photon_eye.py `_build_2d_retina` mints receptors on a strictly "
                "uniform az x el lattice (nested for row/col, evenly-spaced "
                "az/el, no per-receptor position); submit_photons_2d indexes "
                "cells by flat=row*n_az+col with a uniform-grid bounds check."),
        "live_build_needs": [
            "a per-receptor (az, el) position TABLE replacing the uniform nested "
            "loop in _build_2d_retina (the fovea's 1:1 + the log-polar spokes/rings "
            "as explicit receptor positions);",
            "a matching SCATTER in submit_photons_2d: map each incoming photon "
            "packet to the nearest receptor (or a precomputed pixel->receptor "
            "assignment) instead of flat=row*n_az+col;",
            "the carve/onset rules already read per-cell (row,col,epoch) — they "
            "need the receptors' real positions for the common-fate neighbourhood, "
            "so an explicit adjacency (neighbour edges) on the non-uniform sheet.",
        ],
        "no_new_term_expected": ("this is receptor CONSTRUCTION + a scatter — "
                                 "world-adapter / seed-builder work, not a new DSL "
                                 "Term; the onset/carve Terms are position-agnostic."),
    }


def main():
    # Sized to the Part-A ceilings measured in results/doom_realtime_ceiling.json.
    budgets = {
        "graph_28.5ms": 1743, "graph_33ms": 1961,
        "accel_28.5ms": 14023, "accel_33ms": 15830,
    }
    out = {"screen": [SCREEN_W, SCREEN_H], "r_max_px": round(R_MAX, 2),
           "build_gap": build_gap(),
           "layouts": {k: payoff(b) for k, b in budgets.items()}}
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "results", "foveated_layout_spec.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"Doom screen {SCREEN_W}x{SCREEN_H}, corner radius {R_MAX:.1f}px")
    print(f"Eye supports non-uniform receptors: {build_gap()['eye_supports_nonuniform']}")
    for k, b in budgets.items():
        p = out["layouts"][k]
        u, f = p["uniform"], p["foveated"]
        print(f"\n[{k}]  budget={b} receptors")
        print(f"  uniform : {u['grid_w']}x{u['grid_h']} = {u['cells']} cells, "
              f"{u['central_px_per_cell']} px/cell everywhere (enemy ~{p['enemy_cells_uniform']} cells)")
        print(f"  foveated: {f['foveal_side_px']}x{f['foveal_side_px']} 1:1 fovea "
              f"({f['foveal_receptors']} rec) + {f['logpolar_spokes']}spokes x "
              f"{f['logpolar_rings']}rings ({f['periphery_receptors']} rec) = "
              f"{f['cells']} cells (fits={f['fits']})")
        print(f"  PAYOFF  : central acuity gain {p['central_acuity_gain_x']}x "
              f"(fovea 1:1 vs uniform {u['central_px_per_cell']} px/cell), full-frame coverage")
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
