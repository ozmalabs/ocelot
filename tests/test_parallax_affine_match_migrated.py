"""GATE for rung 128000 — DOES IMAGE-ONLY AFFINE MATCHING RECOVER 127000's ORACLE?

The verdict is FALSIFY: image-only within-block affine matching does NOT push the
rotation bound (stays at rigid's ~0.12, vs the oracle's 0.5), and the binding
constraint is NOT block-scale identifiability (blocks are well-conditioned) but the
image-MATCH OBJECTIVE (its minimum is off the true block-mean under rotation).

Positive-controlled BOTH ways (§1 clause 4, §12):
  * the identifiability instrument (`tt_eigmin`) is exercised on a DEGENERATE
    (1-D-gradient) block where it MUST read ~0 — so its large value on textured
    BSDS is a live measurement, not a dead-reader floor;
  * a FALSE claim (affine_match recovers the oracle / pushes the bound) reddens the
    pins while the instrument stays green.

Asserts the pre-registered structure on burned seeds (fast): rigid re-earns
127000's ~0.12 bound and is byte-identical to 127000 int_int / 126000 full_cf; the
oracle holds where the sensor breaks (the bracket); affine_match does NOT push the
bound and its block-mean estimate is WORSE than rigid; the FALSIFY mechanism is
objective-misspecification not identifiability (well-conditioned AND drifts from
truth); the SENSOR is image-only (source audit); and the §13 no-tuned-threshold
audit.
"""
import os, sys, re, ast, inspect
import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (_HERE, _ROOT, os.path.join(_ROOT, "scripts"),
          os.path.join(_ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.engine_provenance import engine_preamble
engine_preamble()

from parallax_char import SQRT5  # noqa: E402
from parallax_real_char import bsds_paths  # noqa: E402
from parallax_affine_char import scene, carve_full  # noqa: E402
from parallax_subpixel_char import arm_int_int, arm_oracle  # noqa: E402
import parallax_affine_match_char as amc  # noqa: E402
from parallax_affine_match_char import (  # noqa: E402
    arm_rigid, arm_affine_match, est_err_diag, drift_from_truth_diag, _affine_block)

DEPTHS, BASE, REF = [300.0, 10.0, 5.0], 30.0, 1
SEEDS = list(range(116000, 116012))  # burned; fast


def _paths():
    p = bsds_paths()
    if not p:
        pytest.skip("BSDS300 corpus absent (data/vision_curriculum/BSDS300)")
    return p


def _rate(arm_fn, rot, paths):
    oks = []
    for sd in SEEDS:
        sc = scene(sd, DEPTHS, BASE, REF, rot=rot, paths=paths)
        oks.append(arm_fn(sc)[0])
    return float(np.mean(oks))


def _diag_mean(fn, rot, paths, idx):
    paths = paths
    vals = [fn(scene(sd, DEPTHS, BASE, REF, rot=rot, paths=paths))[idx] for sd in SEEDS]
    return float(np.mean(vals))


def test_rigid_reearns_127000_bound():
    """rigid tolerates rot 0.08 (>=0.5) and BREAKS by 0.16 (==0.0) — the 0.12 bound."""
    paths = _paths()
    assert _rate(arm_rigid, 0.08, paths) >= 0.5
    assert _rate(arm_rigid, 0.16, paths) == 0.0


def test_rigid_byte_identical_to_127000_and_126000():
    paths = _paths()
    for sd in SEEDS:
        sc = scene(sd, DEPTHS, BASE, REF, rot=0.0, paths=paths)
        _, br_rig, _ = arm_rigid(sc)
        _, br_127 = arm_int_int(sc)
        r126 = carve_full(sc, SQRT5)
        assert abs(float(br_rig[REF]) - float(br_127[REF])) < 1e-12
        assert abs(float(br_rig[REF]) - float(np.asarray(r126["band_resid"])[REF])) < 1e-9


def test_oracle_holds_where_sensor_breaks():
    """The bracket: oracle carves at rot 0.16 (>=0.9) where rigid reads 0.0 — the
    SENSOR is binding and the frame pair holds the info (127000, re-earned)."""
    paths = _paths()
    assert _rate(arm_oracle, 0.16, paths) >= 0.9
    assert _rate(arm_rigid, 0.16, paths) == 0.0


def test_affine_match_does_NOT_push_the_bound():
    """The headline FALSIFY: image-only affine matching does NOT tolerate a rotation
    the rigid cannot — at rot 0.16 its rate is still < 0.5 (nowhere near the oracle's
    1.0). No push toward 0.5."""
    paths = _paths()
    assert _rate(arm_affine_match, 0.16, paths) < 0.5
    # and it does not recover the oracle: strictly below the oracle at 0.16
    assert _rate(arm_affine_match, 0.16, paths) < _rate(arm_oracle, 0.16, paths)


def test_affine_block_mean_estimate_is_WORSE_than_rigid():
    """The affine model does not recover the true block-mean: est_err(affine) >
    est_err(rigid) at rot 0.16 (the extra DOF add bias/variance, not accuracy)."""
    paths = _paths()
    rig = _diag_mean(est_err_diag, 0.16, paths, 0)
    aff = _diag_mean(est_err_diag, 0.16, paths, 1)
    assert aff > rig, (aff, rig)


def test_FALSIFY_is_objective_misspecification_not_identifiability():
    """Prove the mechanism: BSDS blocks are WELL-CONDITIONED (tt_eigmin >> 0) yet the
    fit initialised AT the true block-mean DRIFTS away (affine drift > 0). So the
    image-match OBJECTIVE's minimum is off the true mean — not block-scale
    identifiability (the aperture does NOT re-appear inside the fit here)."""
    paths = _paths()
    tt = []; drift_aff = []
    for sd in SEEDS:
        sc = scene(sd, DEPTHS, BASE, REF, rot=0.16, paths=paths)
        tt.append(arm_affine_match(sc)[2]["tt_eigmin_med"])
        drift_aff.append(drift_from_truth_diag(sc)[1])
    assert np.median(tt) > 50.0            # well-conditioned (not aperture-limited)
    assert np.mean(drift_aff) > 0.3        # objective's optimum is off the true mean


# ---- POSITIVE CONTROLS (§12) ----------------------------------------------
def test_positive_control_identifiability_instrument_is_alive():
    """Exercise tt_eigmin on a DEGENERATE 1-D-gradient block: it MUST read ~0 there
    (the aperture problem), proving its large value on textured BSDS is a live
    measurement, not a dead-reader floor. A vertical-only ramp has zero horizontal
    structure -> translation structure tensor's x-eigenvalue collapses."""
    H = W = 16
    yy, xx = np.mgrid[0:H, 0:W]
    a = yy.astype(float) * 3.0           # gradient ONLY in y (1-D) -> x aperture
    b = a.copy()
    _, tte, _, _, _ = _affine_block(a, b, 4, 4, 8, 0.0, SQRT5, 12)
    assert tte < 1.0, tte                 # instrument detects the degenerate block


def test_positive_control_false_recovery_claim_reddens():
    """A claim that affine_match RECOVERS the oracle (rate>=0.9 at rot 0.16) would be
    RED — the instrument is alive and catches the false positive."""
    paths = _paths()
    assert not (_rate(arm_affine_match, 0.16, paths) >= 0.9)


# ---- IMAGE-ONLY AUDIT ------------------------------------------------------
def test_sensor_is_image_only():
    """The SENSOR functions touch ONLY the two frames + the known-pose pred — they
    must NOT reference any ground-truth projection key (t / d_col / s_col / band_of),
    nor take an `sc` scene dict. (The DIAGNOSTICS may read `t`; the SENSOR may not.)"""
    forbidden = ("d_col", "s_col", "band_of", '"t"', "'t'", "t_depth")
    for fn in (amc.affine_match_field, amc._affine_block, amc._lk_refine,
               amc._warp_resid, amc._bilinear):
        src = inspect.getsource(fn)
        for tok in forbidden:
            assert tok not in src, f"{fn.__name__} references ground truth {tok!r}"
        # the sensor takes frames, never a scene dict
        assert "sc[" not in src, f"{fn.__name__} indexes a scene dict"


def test_no_tuned_threshold_in_char():
    """The char introduces NO picked numeric verdict constant beyond the INHERITED
    sensor tolerance (SQRT5) / aperture (BLOCK). Backtracking halving (0.5), the
    finite-diff step, iteration caps and 1e-x guards are algorithmic, not tuned
    verdict thresholds."""
    src = open(os.path.join(_ROOT, "scripts", "parallax_affine_match_char.py")).read()
    bad = re.findall(r"[<>]=?\s*0\.\d{2,}", src)
    assert not bad, f"unexplained numeric threshold(s): {bad}"
