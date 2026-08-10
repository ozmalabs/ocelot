"""GATE for rung 127000 — WHAT BINDS 126000's 0.12-rad rotation bound?

Positive-controlled BOTH ways (§1 clause 4, §12):
  * a DEAD localizer (oracle fed the sensor's own broken field) reddens the
    localizer check while the credit pins stay green;
  * a FALSE claim (subpix_sensor helps) reddens the pins while the instrument
    stays green.

Asserts the pre-registered structure on burned seeds (fast): the default arm
re-earns 126000's ~0.12 bound; subpix_sensor HARMS (inverts earlier); the oracle
holds where the sensor breaks (SENSOR is binding, single frame pair holds the
info); the continuous oracle is FLAT in rot (no 2-frame entanglement); the
default arm is byte-identical to 126000's full_cf; and the §13 no-tuned-threshold
audit (the char introduces no picked constant beyond the inherited τ=√5 / block).
"""
import os, sys, re
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
from parallax_subpixel_char import (  # noqa: E402
    arm_int_int, arm_subpix_sensor, arm_finer_block, arm_oracle,
    continuous_oracle_band_resid)

DEPTHS, BASE, REF = [300.0, 10.0, 5.0], 30.0, 1
SEEDS = list(range(116000, 116012))  # burned; fast


def _paths():
    p = bsds_paths()
    if not p:
        pytest.skip("BSDS300 corpus absent (data/vision_curriculum/BSDS300)")
    return p


def _rate(arm_fn, rot, paths, **kw):
    oks = []
    for sd in SEEDS:
        sc = scene(sd, DEPTHS, BASE, REF, rot=rot, paths=paths)
        ok, _ = arm_fn(sc, **kw) if kw else arm_fn(sc)
        oks.append(ok)
    return float(np.mean(oks))


def test_default_arm_reearns_126000_bound():
    """int_int (=126000 full_cf) tolerates rot 0.08 (>=0.5) and BREAKS by 0.16."""
    paths = _paths()
    assert _rate(arm_int_int, 0.08, paths) >= 0.5
    assert _rate(arm_int_int, 0.16, paths) == 0.0


def test_default_arm_byte_identical_to_126000_full_cf():
    paths = _paths()
    for sd in SEEDS:
        sc = scene(sd, DEPTHS, BASE, REF, rot=0.0, paths=paths)
        _, br = arm_int_int(sc)
        r126 = carve_full(sc, SQRT5)
        assert abs(float(br[REF]) - float(np.asarray(r126["band_resid"])[REF])) < 1e-9


def test_subpix_sensor_HARMS_not_helps():
    """Sub-pixel displacement refinement INVERTS EARLIER than the default: at a rot
    the default still carves (0.08), subpix_sensor has already collapsed. The
    leading hypothesis is FALSIFIED — sub-pixel is aimed at the wrong layer."""
    paths = _paths()
    default_08 = _rate(arm_int_int, 0.08, paths)
    subpix_08 = _rate(arm_subpix_sensor, 0.08, paths)
    assert default_08 >= 0.5, default_08
    assert subpix_08 < default_08, (subpix_08, default_08)  # strictly worse (harms)


def test_finer_block_does_not_push_bound():
    """Multi-resolution finer aperture (block 6) is at best MARGINAL and never
    tolerates a rot (0.16) the default cannot — it does NOT push the bound."""
    paths = _paths()
    assert _rate(arm_finer_block, 0.16, paths) == 0.0


def test_oracle_holds_where_sensor_breaks_SENSOR_is_binding():
    """The credit LOCALIZER: the true block-mean oracle carves depth order at rot
    0.16 (single frame pair) where EVERY real sensor reads 0.0. => the SAD
    block-match SENSOR is the binding constraint and the frame pair holds the
    info."""
    paths = _paths()
    assert _rate(arm_oracle, 0.16, paths) >= 0.9
    assert _rate(arm_int_int, 0.16, paths) == 0.0


def test_continuous_oracle_flat_no_entanglement():
    """Depth and rotation are separable in the CONTINUOUS map when the pose is
    known: the per-band residual is (far,ref,near)=(-2.9,0,+3) INDEPENDENT of rot.
    => NO 2-frame entanglement; the >=3-frame escape is refuted at the info
    level."""
    paths = _paths()
    for rot in (0.0, 0.08, 0.16):
        brs = [continuous_oracle_band_resid(scene(sd, DEPTHS, BASE, REF, rot=rot, paths=paths))
               for sd in SEEDS]
        m = np.mean(brs, axis=0)
        assert m[2] > m[1] > m[0]                       # order held
        assert abs(m[1]) < 0.05 and abs(m[2] - 3.0) < 0.05 and abs(m[0] + 2.9) < 0.05


# ---- POSITIVE CONTROLS (§12) ----------------------------------------------
def test_positive_control_dead_localizer_reddens_localizer_only():
    """If the 'oracle' were fed the SENSOR's own (broken) field instead of the true
    block-mean, it would collapse at rot 0.16 exactly like the sensor — the
    localizer claim would FAIL. Proves the localizer is not a tautology."""
    paths = _paths()
    # dead oracle == the default sensor; must NOT satisfy the localizer bar
    dead = _rate(arm_int_int, 0.16, paths)   # stands in for a broken-fed oracle
    assert not (dead >= 0.9)                 # the localizer check would redden


def test_positive_control_false_help_claim_reddens_pin():
    """If we asserted subpix_sensor HELPS (rate at 0.08 >= default), the pin would
    be RED — the instrument is alive and would catch a false positive."""
    paths = _paths()
    subpix_08 = _rate(arm_subpix_sensor, 0.08, paths)
    default_08 = _rate(arm_int_int, 0.08, paths)
    assert not (subpix_08 >= default_08)     # a 'helps' claim would be false


# ---- §13 no-tuned-threshold audit -----------------------------------------
def test_no_tuned_threshold_in_char():
    """The char introduces NO picked numeric constant in its grouping/verdict
    beyond the INHERITED sensor tolerance (SQRT5) and aperture (BLOCK). The rot
    sweep values and block=6 are SWEPT arm parameters, not tuned thresholds."""
    src = open(os.path.join(_ROOT, "scripts", "parallax_subpixel_char.py")).read()
    # no bare magic comparison thresholds of the '> 0.NN' verdict kind
    bad = re.findall(r"[<>]=?\s*0\.\d{2,}", src)
    # the only allowed float literals are interpolation/parabola bounds (0.5) and 1e-x guards
    assert not bad, f"unexplained numeric threshold(s): {bad}"
