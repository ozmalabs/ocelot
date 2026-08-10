#!/usr/bin/env python3
"""THE REAL-SCENE WTA TIE RATE — decides arm / don't-arm the 16 Eq(node,sel) sites.

The refusal_representable rung named "arm the 16 existing WTA sites" as future work,
"priced by the still-unmeasured real-scene tie rate". The ArgminUnique rung measured
0.0453% on the bench and said it is NOT a natural-scene statistic (201/201 ties came
from calibration gates installing IDENTICAL ideal cells). This measures the tie rate
at the load-bearing real-scene WTA on REAL depth scenes.

The real-scene WTA is `mo_dominant` (vision_motion_group.json): an Argmax over
motion-group MEMBER COUNT (the largest common-fate group is the reference frame). A
tie = the max member count is achieved by >= 2 groups (a non-unique extremum). We ALSO
measure the finer per-cell nearest-surface assignment tie (a cell EXACTLY equidistant
to >= 2 surface mean-velocities — the "cannot assign this cell" question).

Prediction (pre-registered, ~85%): tie rate ~= 0 (< 1%). The SAD sensor confabulates a
value per cell rather than abstaining (parallax rung), and the selectors run over
values that almost never collide exactly (ArgminUnique P1).

NO wall-clock quantity is a verdict. Every number is an exact count over N=200 fresh
seeds (120000-120199), unit = SEED, with a 95% Wilson CI.
"""
from __future__ import annotations
import json
import math
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()
EXPECT_ENGINE = "7041d2e6a7dd"
assert EXPECT_ENGINE in provenance_line(), provenance_line()

import numpy as np  # noqa: E402
from scripts.parallax_char import make_scene, group_common_fate  # noqa: E402
from domains.motion_group_world import vector_field  # noqa: E402

N = 200
SEED0 = 120000
SHIFTS = [0, 3, 6]
BLOCK = 8
TAUS = {"exact_tau0": 0.0, "sensor_tau_sqrt5": math.sqrt(5)}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def dominant_argmax_tie(lab, nlab):
    """mo_dominant: Argmax over group member count. Tie iff the max count is
    achieved by >= 2 groups (a non-unique extremum)."""
    sizes = np.array([(lab == k).sum() for k in range(nlab)])
    mx = sizes.max()
    return int((sizes == mx).sum() >= 2), int((sizes == mx).sum())


def per_cell_assignment_ties(R, lab, nlab):
    """For each cell, nearest surface = argmin over surface mean-velocity distance.
    A tie = >= 2 surfaces EXACTLY equidistant (the 'cannot assign this cell' WTA).
    Surfaces are the real (non-speck) groups: those with >= aperture cells, mirroring
    the participation-ratio surfaces the carve keys on. Returns (n_tied, n_cells)."""
    sizes = np.array([(lab == k).sum() for k in range(nlab)])
    surf = [k for k in range(nlab) if sizes[k] >= BLOCK]
    if len(surf) < 2:
        return 0, R.shape[0] * R.shape[1]
    means = np.array([R[lab == k].reshape(-1, R.shape[2]).mean(axis=0) for k in surf])
    nh, nw = R.shape[0], R.shape[1]
    tied = 0
    for r in range(nh):
        for c in range(nw):
            d = np.hypot(means[:, 0] - R[r, c, 0], means[:, 1] - R[r, c, 1])
            mn = d.min()
            if int((d == mn).sum()) >= 2:
                tied += 1
    return tied, nh * nw


def run():
    load0 = os.getloadavg()
    rows = {}
    for tname, tau in TAUS.items():
        dom_tie_scenes = 0
        gt_dom_tie_scenes = 0   # the SAME selection on the GROUND-TRUTH field
        cell_tie_scenes = 0
        firings = 0            # one dominant-group selection per scene
        cell_firings = 0
        cell_ties_total = 0
        max_dom_multiplicity = 0
        for i in range(N):
            rng = np.random.default_rng(SEED0 + i)
            sc = make_scene(rng, SHIFTS, BLOCK)
            V = vector_field(sc["a"], sc["b_depth"], BLOCK)
            R = V - sc["delta_ref"]
            lab, nlab = group_common_fate(R, tau)
            tie, mult = dominant_argmax_tie(lab, nlab)
            dom_tie_scenes += tie
            firings += 1
            max_dom_multiplicity = max(max_dom_multiplicity, mult)
            # the SAME Argmax on the GROUND-TRUTH field (what the sensor
            # confabulates a unique winner OUT of): the true reference-frame
            # ambiguity, before the sensor breaks it.
            gt_lab, gt_nl = group_common_fate(sc["t_depth"] - sc["delta_ref"], tau)
            gt_tie, _ = dominant_argmax_tie(gt_lab, gt_nl)
            gt_dom_tie_scenes += gt_tie
            ct, nc = per_cell_assignment_ties(R, lab, nlab)
            cell_ties_total += ct
            cell_firings += nc
            if ct > 0:
                cell_tie_scenes += 1
        p_dom, lo_dom, hi_dom = wilson(dom_tie_scenes, firings)
        p_cell, lo_cell, hi_cell = wilson(cell_ties_total, cell_firings)
        rows[tname] = {
            "tau": tau,
            "n_scenes": N,
            "dominant_argmax": {
                "tie_scenes": dom_tie_scenes,
                "firings": firings,
                "tie_rate": p_dom, "wilson95": [lo_dom, hi_dom],
                "max_multiplicity_of_the_largest_group": max_dom_multiplicity,
                "GROUND_TRUTH_tie_scenes": gt_dom_tie_scenes,
                "GROUND_TRUTH_tie_rate": gt_dom_tie_scenes / firings,
                "note": "the sensed rate is what remains AFTER the sensor confabulates a unique winner out of the ground-truth ambiguity",
            },
            "per_cell_nearest_surface": {
                "tie_cells": cell_ties_total,
                "cell_firings": cell_firings,
                "tie_rate": p_cell, "wilson95": [lo_cell, hi_cell],
                "scenes_with_any_cell_tie": cell_tie_scenes,
            },
        }
    load1 = os.getloadavg()

    # DECISION (pre-registered), read PER SITE (a site's tie rate prices arming
    # THAT site): upper Wilson bound < 2% -> VACUOUS, do NOT arm; >= 5% -> arm;
    # 2-5% -> a grey zone the prereg did not resolve cleanly (reported as such,
    # NOT rescued). Any arming is deferred to its OWN pre-registration (§3/§5).
    ub_cell = max(r["per_cell_nearest_surface"]["wilson95"][1] for r in rows.values())
    ub_dom = max(r["dominant_argmax"]["wilson95"][1] for r in rows.values())

    def verdict(ub):
        return "VACUOUS_do_not_arm" if ub < 0.02 else ("ARM" if ub >= 0.05 else "GREY_2to5pct_defer")
    ub = max(ub_cell, ub_dom)
    out = {
        "engine": provenance_line(),
        "engine_hash": EXPECT_ENGINE,
        "wta_site": "mo_dominant (Argmax over motion-group member count) + per-cell nearest-surface argmin",
        "n_seeds": N, "seed0": SEED0, "shifts": SHIFTS, "block": BLOCK,
        "rows": rows,
        "worst_wilson_upper_bound": ub,
        "per_cell_wta_verdict": verdict(ub_cell),
        "per_cell_wilson_upper": ub_cell,
        "dominant_wta_verdict": verdict(ub_dom),
        "dominant_wilson_upper": ub_dom,
        "decision_rule": "per site: upper<2% VACUOUS/don't-arm; >=5% arm; 2-5% grey/defer. Any arming needs its own prereg.",
        "loadavg_start": load0, "loadavg_end": load1,
    }
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "residual_wta_tierate.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: rows[k] for k in rows}, indent=2))
    print("per-cell WTA verdict:", verdict(ub_cell), "(upper", round(ub_cell, 5), ")")
    print("dominant/reference-frame WTA verdict:", verdict(ub_dom), "(upper", round(ub_dom, 5), ")")
    print("loadavg:", load0, "->", load1)


if __name__ == "__main__":
    run()
