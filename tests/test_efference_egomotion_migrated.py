"""GATE for EFFERENCE-COPY EGOMOTION CANCELLATION (block 155000-155999).

The GENERAL capability, grounded in active inference / sensory attenuation: an
agent predicts the sensory consequences of its OWN motion (egomotion optic
flow) via an efference copy, CANCELS them, and the residual is the world /
the other. Under turning: predict the ~uniform egomotion flow from the agent's
own turn, cancel it, carve the residual -> independently-moving objects; the
view-fixed zero-observed-flow region is the agent's own APPARATUS. Doom is only
the eval.

Gated, each ABLE TO FAIL (reads measured/graph values, never an exact-d2 magic
constant, skips if VizDoom absent):

  H1 (SYNTHETIC, always runs) the mechanism on ideal ground truth:
    (i)   under egomotion + a view-fixed apparatus, the RAW carve FAILS to
          isolate the independent object (and reports the APPARATUS as its
          world object); the efference (cancel + fold-apparatus) carve isolates
          the object EXACTLY. ABLE TO FAIL: the raw carve provably succeeds on
          the SAME scene with the apparatus removed, so the assertion is not
          vacuous.
    (ii)  the apparatus is identified (zero observed flow while the world flows)
          and is NOT carved as a world object; a moving object is NOT mislabeled
          apparatus.
    (iii) static background -> residual ~ 0 (exact).

  CONTROLS: no-egomotion -> cancellation is a byte-identical no-op; static
    scene + egomotion -> nothing carved; moving object + no egomotion -> carved
    identically with/without cancellation.

  SELF-GROUNDING: when the apparatus fills >half the view, an OBSERVATION-based
    estimate reads 'no flow' and cannot identify the apparatus; the COMMAND-based
    efference copy knows the agent turned and isolates the object.

  H2 (DOOM, skips if VizDoom absent AND no results file): read from the recorded
    run — the efference carve's enemy IoU under turning EXCEEDS the uncancelled
    baseline (CONFIRM) OR is an honestly-named DEGRADE with a diagnosed cause
    (egomotion not sensor-visible / sub-pixel). Direction asserted; the absolute
    IoU is the finding.

No Rust added, no seed, no default moved (new files only) => the shipped
translation carve is byte-identical BY CONSTRUCTION; the efference carve with
zero egomotion + no apparatus folding IS the raw carve, asserted here.
"""
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (os.path.join(ROOT, "scripts"), ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from domains.engine_provenance import engine_preamble
    engine_preamble()
except Exception:
    pass

import efference_egomotion_probe as E   # noqa: E402

RESULTS = os.path.join(ROOT, "results", "efference_egomotion.json")
GH, GW = E.SYNTH_GH, E.SYNTH_GW


def _have_vizdoom():
    try:
        import vizdoom  # noqa: F401
        return True
    except Exception:
        return False


def _primary_scene():
    """The primary H1 scene: uniform egomotion (0,6) + independent object
    (own motion (0,-2)) + a view-fixed apparatus band."""
    return E.make_scene(GH, GW, (0, 6), obj_motion=(0, -2), obj_center=(14, 40),
                        obj_R=6, apparatus_rows=18, bg_noise=0)


# ============================================================
#  Mechanical read-out correctness on CONSTRUCTED known fields
# ============================================================
def test_cancel_is_arithmetic_subtraction():
    vy = np.full((5, 5), 3.0); vx = np.full((5, 5), 7.0)
    ry, rx = E.cancel(vy, vx, 3.0, 7.0)
    assert np.allclose(ry, 0.0) and np.allclose(rx, 0.0)


def test_zero_flow_mask_flags_only_still_cells():
    vy = np.zeros((4, 4)); vx = np.zeros((4, 4))
    vx[0, 0] = 5.0                       # one moving cell
    m = E.zero_flow_mask(vy, vx)
    assert not m[0, 0] and m[1, 1] and m.sum() == 15


def test_calibrate_gain_recovers_known_uniform_flow():
    # a field that is (0,6) over the majority + a zero apparatus band: the robust
    # median recovers the egomotion (6), NOT biased to 0 by the apparatus.
    sc = E.make_scene(GH, GW, (0, 6), obj_motion=(0, 0), obj_center=(0, 0),
                      obj_R=0, apparatus_rows=18, bg_noise=0)
    gain = E.calibrate_gain([(sc["vy"], sc["vx"])])
    assert abs(gain[1] - 6.0) < 1e-6 and abs(gain[0]) < 1e-6, gain


# ============================================================
#  H1 (i) — residual carve isolates the object where raw FAILS
# ============================================================
def test_h1_raw_carve_fails_but_efference_isolates_object():
    sc = _primary_scene()
    E_true = (0, 6)
    raw = E.raw_carve(sc["vy"], sc["vx"], GH, GW)
    raw_obj = E.best_iou_to(raw, sc["gt_object"])
    eff, app_cells, ry, rx = E.efference_carve(sc["vy"], sc["vx"], E_true, GH, GW)
    eff_obj = E.best_iou_to(eff, sc["gt_object"])
    # the residual carve isolates the object; the raw carve does not
    assert eff_obj > 0.8, f"efference failed to isolate object: {eff_obj}"
    assert raw_obj < 0.2, f"raw carve unexpectedly isolated object: {raw_obj}"
    assert eff_obj - raw_obj > 0.5


def test_h1_assertion_is_not_vacuous_raw_succeeds_without_apparatus():
    # ABLE-TO-FAIL guard: on the SAME scene with the apparatus REMOVED, the raw
    # carve isolates the object fine -> the failure above is caused by the
    # apparatus, and the raw carve is not simply broken.
    sc = E.make_scene(GH, GW, (0, 6), obj_motion=(0, -2), obj_center=(14, 40),
                      obj_R=6, apparatus_rows=0, bg_noise=0)
    raw = E.raw_carve(sc["vy"], sc["vx"], GH, GW)
    assert E.best_iou_to(raw, sc["gt_object"]) > 0.8


def test_h1_apparatus_folding_is_the_decisive_operation():
    # honest decomposition: cancelling a UNIFORM egomotion WITHOUT folding the
    # apparatus does NOT isolate the object (redundant with segment_motion's
    # built-in dominant subtraction); the apparatus identification does the work.
    sc = _primary_scene()
    eff_na, _, _, _ = E.efference_carve(sc["vy"], sc["vx"], (0, 6), GH, GW,
                                        use_apparatus=False)
    assert E.best_iou_to(eff_na, sc["gt_object"]) < 0.2


# ============================================================
#  H1 (ii) — apparatus identification / discrimination
# ============================================================
def test_h1_apparatus_identified_and_not_carved_as_object():
    sc = _primary_scene()
    eff, app_cells, _, _ = E.efference_carve(sc["vy"], sc["vx"], (0, 6), GH, GW)
    # the recovered zero-flow region matches the known apparatus
    assert E.iou(app_cells, sc["gt_apparatus"]) > 0.9
    # and the apparatus is NOT among the carved world regions
    assert E.best_iou_to(eff, sc["gt_apparatus"]) < 0.1
    # the raw carve, by contrast, DOES report the apparatus as its world object
    raw = E.raw_carve(sc["vy"], sc["vx"], GH, GW)
    assert E.best_iou_to(raw, sc["gt_apparatus"]) > 0.8


def test_h1_moving_object_not_mislabeled_apparatus():
    sc = _primary_scene()
    _, app_cells, _, _ = E.efference_carve(sc["vy"], sc["vx"], (0, 6), GH, GW)
    overlap = len(set(sc["gt_object"]) & set(app_cells))
    assert overlap == 0, "a moving object was mislabeled apparatus"


# ============================================================
#  H1 (iii) — static background residual ~ 0
# ============================================================
def test_h1_static_background_residual_is_zero():
    sc = _primary_scene()
    _, _, ry, rx = E.efference_carve(sc["vy"], sc["vx"], (0, 6), GH, GW)
    bg = np.array(sorted(sc["gt_background"]))
    resid = np.sqrt(ry[bg[:, 0], bg[:, 1]] ** 2 + rx[bg[:, 0], bg[:, 1]] ** 2)
    assert float(np.mean(resid)) < 0.01


# ============================================================
#  CONTROLS
# ============================================================
def test_control_no_egomotion_is_byte_identical_noop():
    # E = 0 -> predicted flow 0 -> world_flowing False -> no apparatus fold ->
    # residual == observed -> carve byte-identical to the raw carve.
    sc = E.make_scene(GH, GW, (0, 0), obj_motion=(0, -4), obj_center=(20, 40),
                      obj_R=6, apparatus_rows=0, bg_noise=0)
    raw = E.raw_carve(sc["vy"], sc["vx"], GH, GW)
    eff, app_cells, _, _ = E.efference_carve(sc["vy"], sc["vx"], (0, 0), GH, GW)
    assert E.carves_identical(raw, eff)
    assert len(app_cells) == 0


def test_control_static_scene_plus_egomotion_carves_nothing():
    sc = E.make_scene(GH, GW, (0, 6), obj_motion=(0, 0), obj_center=(0, 0),
                      obj_R=0, apparatus_rows=18, bg_noise=0)
    eff, _, ry, rx = E.efference_carve(sc["vy"], sc["vx"], (0, 6), GH, GW)
    assert len(eff) == 0
    assert float(np.mean(np.abs(ry)) + np.mean(np.abs(rx))) < 1e-9


def test_control_moving_object_no_egomotion_carved_identically():
    sc = E.make_scene(GH, GW, (0, 0), obj_motion=(0, -4), obj_center=(25, 45),
                      obj_R=7, apparatus_rows=0, bg_noise=0)
    raw = E.raw_carve(sc["vy"], sc["vx"], GH, GW)
    eff, _, _, _ = E.efference_carve(sc["vy"], sc["vx"], (0, 0), GH, GW)
    assert E.carves_identical(raw, eff)
    assert E.best_iou_to(eff, sc["gt_object"]) > 0.8


# ============================================================
#  SELF-GROUNDING — command beats observation when the view is self-dominated
# ============================================================
def test_self_grounding_command_succeeds_where_observation_cannot():
    # apparatus fills >half the view -> observed median flow ~ 0 ('world not
    # moving'); the efference copy (gain from the agent's own turn) knows better.
    sc = E.make_scene(GH, GW, (0, 6), obj_motion=(0, -2), obj_center=(8, 40),
                      obj_R=5, apparatus_rows=36, bg_noise=0)
    st = E.flow_stats(sc["vy"], sc["vx"])
    assert (st["median"][0] ** 2 + st["median"][1] ** 2) ** 0.5 < E.ZERO_FLOOR
    # efference: command-supplied gain (0,6)
    eff, app_eff, _, _ = E.efference_carve(sc["vy"], sc["vx"], (0, 6), GH, GW)
    # model-free: cancel the observed median (~0) -> apparatus ID disabled
    mf, app_mf, _, _ = E.efference_carve(sc["vy"], sc["vx"], st["median"], GH, GW)
    assert E.best_iou_to(eff, sc["gt_object"]) > 0.8 and len(app_eff) > 0
    assert E.best_iou_to(mf, sc["gt_object"]) < 0.2 and len(app_mf) == 0


# ============================================================
#  EFFERENCE vs DOMINANT-FLOW comparison (the self-grounding point)
# ============================================================
def test_efference_gain_matches_robust_estimate_and_is_unbiased():
    # the command-calibrated gain equals the robust MEDIAN estimate and the true
    # egomotion; the naive MEAN estimate is biased by the apparatus.
    sc = _primary_scene()
    st = E.flow_stats(sc["vy"], sc["vx"])
    gain = E.calibrate_gain([(sc["vy"], sc["vx"])])
    assert abs(gain[1] - 6.0) < 1e-6                     # efference == true
    assert abs(st["median"][1] - 6.0) < 1e-6             # median (robust) == true
    assert abs(st["mean"][1] - 6.0) > 1.0                # mean is biased low


# ============================================================
#  H2 — DOOM, read from the recorded run (skips if absent)
# ============================================================
def _h2_from_results():
    if not os.path.exists(RESULTS):
        return None
    with open(RESULTS) as fh:
        return json.load(fh).get("h2_doom")


@pytest.mark.skipif(not _have_vizdoom(), reason="vizdoom absent")
def test_h2_doom_efference_confirms_or_named_degrade():
    h2 = _h2_from_results()
    if h2 is None or "error" in (h2 or {}):
        pytest.skip("no recorded H2 Doom run")
    raw = h2["raw_enemy_iou"]["mean"]
    eff = h2["efference_enemy_iou"]["mean"]
    vis = h2["egomotion_visibility"]
    # CONFIRM (efference recovers the enemy under turning above the uncancelled
    # baseline) OR a diagnosed DEGRADE: the egomotion is not sensor-visible
    # (low coherent flow), so cancellation is a measured no-op (eff == raw).
    confirmed = eff > raw + 0.02
    coherent = (vis["dominant_moving_flow_median"][0] ** 2 +
                vis["dominant_moving_flow_median"][1] ** 2) ** 0.5
    diagnosed_degrade = (abs(eff - raw) < 1e-6) and (coherent < E.ZERO_FLOOR + 1.0)
    assert confirmed or diagnosed_degrade, (raw, eff, vis)


@pytest.mark.skipif(not _have_vizdoom(), reason="vizdoom absent")
def test_h2_doom_apparatus_flow_below_enemy_flow():
    # the enemy (a textured mover) has materially more flow than the view-fixed
    # weapon apparatus — the honest inversion under a non-flowing background.
    h2 = _h2_from_results()
    if h2 is None or "error" in (h2 or {}):
        pytest.skip("no recorded H2 Doom run")
    assert h2["enemy_flow_mag_mean"] > h2["apparatus_flow_mag_mean"]
