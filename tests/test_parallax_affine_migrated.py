"""Gate for rung 126000 — affine-flow grouping + full-field efference vs 125000's
rotation FALSIFY.

The rung is a MEASUREMENT extending the parallax carve; what must be gated is the
mechanism the verdict rests on:

  * the DEFAULT carve `(single-vector efference, common-fate)` is 125000 EXACT
    (byte-identical) — the FALSIFY baseline re-earned in-tree;
  * the rotation FALSIFY is REPRODUCED under the single-vector arm (positive
    control: the break is real, not an artefact of the new code);
  * FULL-FIELD efference (as a search-centre remap) RESCUES the depth order under
    a rotation that broke the single-vector carve;
  * AFFINE grouping is NOT load-bearing: it changes NOTHING under rotation
    (full_affine == full_cf, single_affine == single_cf) and reduces to
    common-fate on translation;
  * full-field POST-HOC subtraction (not search-centre) FAILS — the search-centre
    application is the mechanism, not the field value;
  * the char module introduces NO tuned threshold (§13).
"""
import os, sys, ast
import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "scripts"), _ROOT, os.path.join(_ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from parallax_affine_char import (scene, carve_single, carve_full, COMMON_FATE, AFFINE,  # noqa: E402
                                  efference_field)
from parallax_motion_char import carve as carve125, STAGE_A_DEPTHS, STAGE_A_BASE  # noqa: E402
from parallax_char import group_common_fate, SQRT5  # noqa: E402
from parallax_real_char import bsds_paths  # noqa: E402
from domains.motion_group_world import vector_field  # noqa: E402

BLOCK, GRID = 8, 144
_HAVE_BSDS = os.path.isdir(os.path.join(_ROOT, "data", "vision_curriculum",
                                        "BSDS300", "images", "train"))
pytestmark = pytest.mark.skipif(not _HAVE_BSDS, reason="BSDS300 corpus absent (data/ not symlinked)")

BURNED = list(range(116000, 116012))
DEPTHS, BASE = STAGE_A_DEPTHS, STAGE_A_BASE


def _sc(sd, **kw):
    return scene(sd, kw.pop("depths", DEPTHS), BASE, kw.pop("ref", 1), paths=bsds_paths(), **kw)


def test_default_carve_is_125000_byte_identical():
    """(single-vector, common-fate) reproduces 125000's carve EXACTLY — the §9
    default preserves the committed result, and re-earns the FALSIFY baseline."""
    for sd in BURNED:
        sc = _sc(sd)
        a = carve_single(sc, SQRT5, COMMON_FATE); b = carve125(sc, SQRT5)
        assert abs(a["eff"] - b["eff"]) < 1e-12
        assert a["depth_order_correct"] == b["depth_order_correct"]


def test_rotation_FALSIFY_reproduced_under_single_vector():
    """Positive control: the single-vector arm (125000) still loses the depth
    order under a small rotation — the break is real."""
    dok0, dokr = [], []
    for sd in BURNED:
        dok0.append(carve_single(_sc(sd, rot=0.0), SQRT5, COMMON_FATE)["depth_order_correct"])
        dokr.append(carve_single(_sc(sd, rot=0.04), SQRT5, COMMON_FATE)["depth_order_correct"])
    assert np.mean(dok0) >= 0.9        # no rotation: order correct
    assert np.mean(dokr) < 0.5         # small rotation: FALSIFY reproduced


def test_full_field_efference_RESCUES_rotation():
    """Full-field efference (search-centre remap) recovers the depth order at a
    rotation that broke the single-vector carve — the load-bearing fix."""
    # rot 0.02 is the FALSIFY ONSET (125000 itself: 0.44) — too marginal at n=12;
    # 0.04/0.08 are where the single-vector break is unambiguous.
    for rot in (0.04, 0.08):
        single = np.mean([carve_single(_sc(sd, rot=rot), SQRT5, COMMON_FATE)["depth_order_correct"]
                          for sd in BURNED])
        full = np.mean([carve_full(_sc(sd, rot=rot), SQRT5, COMMON_FATE)["depth_order_correct"]
                        for sd in BURNED])
        assert single < 0.5, (rot, single)      # single-vector broken
        assert full >= 0.9, (rot, full)         # full-field rescued


def test_affine_is_NOT_load_bearing_under_rotation():
    """The 2x2's credit assignment: affine grouping changes NOTHING under
    rotation. full_affine == full_cf AND single_affine == single_cf, exactly."""
    for rot in (0.02, 0.04, 0.08):
        for carve in (carve_single, carve_full):
            cf = np.mean([carve(_sc(sd, rot=rot), SQRT5, COMMON_FATE)["depth_order_correct"] for sd in BURNED])
            af = np.mean([carve(_sc(sd, rot=rot), SQRT5, AFFINE)["depth_order_correct"] for sd in BURNED])
            assert cf == af, (carve.__name__, rot, cf, af)


def test_full_field_POSTHOC_subtraction_FAILS():
    """The mechanism is the search-centre APPLICATION, not the field VALUE:
    subtracting the SAME full predicted field POST-HOC (after a saturated sensor)
    does NOT rescue — the rotation flow exceeds the aperture before subtraction."""
    dok = []
    for sd in BURNED:
        sc = _sc(sd, rot=0.04)
        V = vector_field(sc["a"], sc["b"], sc["block"])
        ex = efference_field(sc, True)
        R = V.copy(); R[..., 1] = R[..., 1] - ex[None, :]
        lab, nl = group_common_fate(R, SQRT5)
        depths = np.asarray(sc["depths"], float)
        br = np.array([float(R[sc["owner"] == i][..., 1].mean()) if (sc["owner"] == i).any() else np.nan
                       for i in range(sc["N"])])
        dok.append(list(np.argsort(-br)) == list(np.argsort(-1.0 / depths)))
    assert np.mean(dok) < 0.5          # post-hoc fails where search-centre rescues


def test_affine_reduces_to_common_fate_on_translation():
    """Degenerate reduction: on piecewise-constant (translation) residual fields
    the MDL-guarded affine engages no slope and mostly reproduces common-fate
    (differs only on isolated confab specks — a MINORITY)."""
    ident = 0
    for sd in BURNED:
        sc = _sc(sd)
        V = vector_field(sc["a"], sc["b"], sc["block"])
        R = V - np.array([0.0, float(int(round(BASE / DEPTHS[1])))])
        lcf, _ = group_common_fate(R, SQRT5); laf, _ = AFFINE(R, SQRT5)
        ident += int(np.array_equal(lcf, laf))
    assert ident >= 0.6 * len(BURNED)   # majority identical; NOT load-bearing anyway


def test_char_module_has_no_tuned_threshold():
    """§13: no Compare against a bare float literal other than the documented
    sentinels (0.0 no-rot guard, 1.0 slope-count, 1e-3 depth floor). τ (=√5), the
    affine MDL threshold and the aperture are inherited/derived, never picked."""
    src = open(os.path.join(_ROOT, "scripts", "parallax_affine_char.py")).read()
    tree = ast.parse(src)
    ALLOWED = {0.0, 1.0, 1e-3}
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for cmp in node.comparators:
                if isinstance(cmp, ast.Constant) and isinstance(cmp.value, float):
                    if cmp.value not in ALLOWED:
                        offenders.append(cmp.value)
    assert not offenders, f"unaudited float threshold(s): {offenders}"
