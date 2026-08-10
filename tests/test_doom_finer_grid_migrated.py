"""GATE for the DOOM FINER GRID + HUD MASK probe (block 153000-153999).

Three independent things are gated (the first two ALWAYS run, no VizDoom):

1. THE SCORER + IoU are correct on a CONSTRUCTED synthetic known-object case.
   (Reuses the 152000 scorer, which this probe shares — priced again here so a
   regression in the shared primitive fails THIS gate too.)

2. THE HUD MASK crops the ego-attached self-apparatus percept (the weapon
   sprite) on a CONSTRUCTED case and leaves an above-band world object
   untouched. `mask_regions` is a fixed geometric crop: able to fail if it
   dropped the wrong region. (The weapon/HUD are NOT false objects — the eye
   perceives them correctly; they are the agent's own apparatus, ego-attached
   and fixed in view-space. The fixed-region mask is a disclosed STEPPING-STONE
   scaffold, not the principled treatment — see the results doc.)

3. THE MEASURED RESOLUTION -> IoU RELATIONSHIP on the recorded run: matched-
   subset enemy IoU at full-res (down=1) exceeds that at 4x (down=4) — the H1
   relationship, read from results/doom_finer_grid.json. ABLE TO FAIL if finer
   grid did not help. Skips explicitly if VizDoom is absent AND no results file
   is present (never silently passes).

The absolute Doom IoU is the FINDING and is NOT hard-coded; only the DIRECTION
of the resolution effect (and the mask's effect) is asserted, both read from the
recorded measurement.
"""
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if os.path.join(ROOT, "scripts") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import eye_on_doom_probe as P            # noqa: E402  (shared scorer)
import doom_finer_grid_probe as F        # noqa: E402  (this rung)

RESULTS = os.path.join(ROOT, "results", "doom_finer_grid.json")


# ----------------------------------------------------------------------
#  1. SCORER CORRECTNESS — constructed, deterministic, able to fail
# ----------------------------------------------------------------------
def test_iou_and_scorer_known_values():
    a = frozenset({(0, 0), (0, 1), (1, 0), (1, 1)})
    assert P.iou(a, a) == 1.0
    assert P.iou(a, frozenset({(0, 0), (0, 1)})) == 0.5
    assert P.iou(a, frozenset({(9, 9)})) == 0.0

    gt = np.zeros((6, 6), dtype=np.int64)
    gt[2:4, 2:4] = 5
    gt_cells = frozenset({(2, 2), (2, 3), (3, 2), (3, 3)})
    sc = P.score_frame([gt_cells], gt)
    assert sc["per_obj_best"][5]["iou"] == 1.0
    half = frozenset({(2, 2), (2, 3)})
    assert P.score_frame([half], gt)["per_obj_best"][5]["iou"] == 0.5
    spurious = frozenset({(0, 0), (0, 1)})
    assert P.score_frame([spurious], gt)["false_positive_regions"]["0.1"] == 1


# ----------------------------------------------------------------------
#  2. THE HUD MASK — constructed, deterministic, able to fail
# ----------------------------------------------------------------------
def test_band_grid_row_geometry():
    # rows >= 150 of 240 -> 0.625 of the grid height, resolution-independent.
    assert F.band_grid_row(240) == 150
    assert F.band_grid_row(120) == 75
    assert F.band_grid_row(60) == 38          # round(0.625*60)=round(37.5)=38


def test_mask_removes_in_band_object_keeps_above_band():
    gh = 60
    band = F.band_grid_row(gh)                # 38
    # a "weapon" region (ego-attached self-apparatus) ENTIRELY in the band
    # (rows 45-47) and an "enemy" (world object) region ENTIRELY above the band
    # (rows 20-21) — the measured Doom geometry in miniature.
    weapon = {"rid": 1, "cells": frozenset({(45, 40), (46, 40), (47, 40)})}
    enemy = {"rid": 2, "cells": frozenset({(20, 40), (21, 40)})}
    kept = F.mask_regions([weapon, enemy], band)
    kept_rids = {r["rid"] for r in kept}
    assert kept_rids == {2}, ("mask must crop the in-band ego-apparatus percept, "
                              "keep the world-object enemy")

    # a region STRADDLING the boundary is KEPT (it may be a low enemy).
    straddle = {"rid": 3, "cells": frozenset({(37, 5), (39, 5)})}
    kept2 = F.mask_regions([weapon, straddle], band)
    assert {r["rid"] for r in kept2} == {3}


def test_mask_does_not_touch_a_carve_with_no_in_band_region():
    band = F.band_grid_row(120)               # 75
    regs = [{"rid": 7, "cells": frozenset({(10, 10), (11, 10)})},
            {"rid": 8, "cells": frozenset({(30, 30)})}]
    assert F.mask_regions(regs, band) == regs   # nothing in band -> unchanged


# ----------------------------------------------------------------------
#  3. THE MEASURED RESOLUTION -> IoU RELATIONSHIP (reads the recorded run)
# ----------------------------------------------------------------------
def _have_vizdoom():
    try:
        import vizdoom  # noqa: F401
        return True
    except Exception:
        return False


def _load_results():
    if not os.path.exists(RESULTS):
        if not _have_vizdoom():
            pytest.skip("VizDoom absent and results/doom_finer_grid.json not "
                        "present — cannot check the measured relationship")
        pytest.skip("results/doom_finer_grid.json not present (run the probe)")
    with open(RESULTS) as fh:
        return json.load(fh)


def test_recorded_scores_are_wellformed():
    r = _load_results()
    assert r["scenario"] == "defend_the_center"
    assert r["engine_source_match"] in ("shared", "own")     # never DIVERGED
    for down in ("4", "2", "1"):
        assert down in r["by_resolution"], f"missing resolution down={down}"
        res = r["by_resolution"][down]
        for key in ("value_unmasked", "motion_unmasked",
                    "value_masked", "motion_masked"):
            iou = res[key]["enemy_iou"]["mean"]
            assert 0.0 <= iou <= 1.0, f"down={down}/{key} IoU out of range {iou}"


def test_H1_value_carve_clears_the_subgrid_wall():
    """H1 (VALUE carve, aperture-free): on the identical enemies that survive
    downsample at ALL THREE resolutions, enemy IoU at finer grid STRONGLY
    exceeds 4x — the sub-grid resolution wall is real and CLEARED. Measured on
    the recorded run: matched-subset IoU 4x -> 2x/1x. ABLE TO FAIL if finer
    grid did not help."""
    r = _load_results()
    ms = r["matched_subset_value"]["per_resolution"]
    assert ms["1"]["n"] >= 1, "empty matched subset"
    assert ms["4"]["mean"] < 0.05, (
        f"4x matched IoU {ms['4']['mean']:.4f} was already high — sub-grid wall "
        "premise absent on this run")
    assert ms["1"]["mean"] > 0.2, (
        f"full-res matched IoU {ms['1']['mean']:.4f} did not clear the floor")
    assert ms["1"]["mean"] > 5 * ms["4"]["mean"], (
        f"finer grid did not materially raise IoU: 4x={ms['4']['mean']:.4f} "
        f"1x={ms['1']['mean']:.4f}")


def test_H1_motion_carve_hits_the_DEEPER_wall():
    """H1 (MOTION carve, the pre-registered PRIMARY, common-fate/texture-blind):
    matched-subset enemy IoU stays FLAT and near-floor across resolution — the
    common-fate carve does NOT grab even a fully-resolved enemy. This is the
    two-sided alternative the prereg named: a deeper wall than sub-grid
    resolution (the stationary enemy's approach is a slow looming, too weak a
    common-fate signal). ABLE TO FAIL: if the motion carve HAD jumped with
    resolution, this assertion breaks and the finding would be different."""
    r = _load_results()
    ms = r["matched_subset_motion"]["per_resolution"]
    assert ms["1"]["mean"] < 0.05, (
        f"motion matched IoU at full-res {ms['1']['mean']:.4f} is NOT near-floor "
        "— the deeper wall would be absent")
    assert abs(ms["1"]["mean"] - ms["4"]["mean"]) < 0.05, (
        f"motion IoU MOVED with resolution (4x={ms['4']['mean']:.4f} "
        f"1x={ms['1']['mean']:.4f}) — the deeper-wall finding would not hold")


def test_H1_enemy_survival_rises_with_resolution():
    """The sub-grid wall itself: the enemy survives downsample into the grid in
    MORE frames as resolution rises (down=1 >= down=4). Value carve unmasked."""
    r = _load_results()
    s4 = r["by_resolution"]["4"]["value_unmasked"]["enemy_survived_frames"]
    s1 = r["by_resolution"]["1"]["value_unmasked"]["enemy_survived_frames"]
    assert s1 >= s4, f"survival did not rise with resolution: 4x={s4} 1x={s1}"


def test_H2_hud_mask_crops_ego_attached_weapon_percept():
    """H2: the fixed HUD-band crop drops the weapon-sprite (ego-attached
    self-apparatus) IoU to ~0 (masked < unmasked, and masked near zero) while
    enemy (world object) IoU is essentially unchanged (the band is above no
    enemy). Value carve at 4x (where the weapon is a strong, stable ego-apparatus
    percept in the 152000 baseline). The weapon is NOT a false object — it is
    correctly perceived apparatus; the crop is a disclosed stepping-stone."""
    r = _load_results()
    res = r["by_resolution"]["4"]
    w_unmasked = res["value_unmasked"]["weapon_sprite_iou"]["mean"]
    w_masked = res["value_masked"]["weapon_sprite_iou"]["mean"]
    assert w_unmasked > 0.05, (
        f"weapon not a strong ego-apparatus percept unmasked ({w_unmasked:.3f}) "
        "— H2 premise absent on this run")
    # the crude fixed-band crop cuts the weapon percept materially (measured
    # ~0.25 -> ~0.065, a ~4x reduction). It does NOT reach 0: the residual is a
    # region STRADDLING the band boundary — exactly the imperfection that marks
    # this as a disclosed stepping-stone scaffold, not the principled treatment.
    assert w_masked < 0.4 * w_unmasked, (
        f"mask did not materially crop the weapon percept: "
        f"{w_unmasked:.3f} -> {w_masked:.3f}")
    assert w_masked < 0.1, f"mask left weapon IoU at {w_masked:.3f}"
    # enemy (world object) IoU EXACTLY unchanged by the mask — enemies render
    # above the band, so no enemy region is ever cropped.
    e_unmasked = res["value_unmasked"]["enemy_iou"]["mean"]
    e_masked = res["value_masked"]["enemy_iou"]["mean"]
    assert abs(e_masked - e_unmasked) < 1e-9, (
        f"mask changed enemy IoU {e_unmasked:.4f} -> {e_masked:.4f} — the band "
        "clips an enemy")
