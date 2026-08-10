"""Gate for rung 125000 (does the parallax carve survive real MOTION?).

The rung is a MEASUREMENT reusing the parallax carve; what must be gated is that
the displacement FALLS OUT of depth + camera motion via perspective projection
(not a hand-set shift), rendered WITHOUT fabrication, and that the mechanism
properties the verdict rests on are real:

  * fronto-parallel projection is BYTE-IDENTICAL to the windowed slide it reduces
    to (positive control: a per-column GRADIENT render is NOT);
  * every rendered pixel is a REAL scene neighbour (windowed slide, no wrap);
  * the STATIC-camera control (base=0) gives one blob;
  * the DEPTH ORDER falls out of the projection (nearer = larger residual),
    never told to the carve;
  * a SLANTED plane SHATTERS at exact τ=0 but SURVIVES at √5 for a gentle
    gradient (common-fate is a transitive flood), and a camera ROTATION corrupts
    the depth order (the pre-registered FALSIFY);
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

from parallax_motion_char import (make_projected_scene, project_columns, carve,  # noqa: E402
                                  STAGE_A_BASE, STAGE_A_DEPTHS, SQRT5)
from parallax_real_char import make_real_scene, bsds_paths  # noqa: E402

BLOCK, GRID = 8, 144
_HAVE_BSDS = os.path.isdir(os.path.join(_ROOT, "data", "vision_curriculum",
                                        "BSDS300", "images", "train"))
pytestmark = pytest.mark.skipif(not _HAVE_BSDS, reason="BSDS300 corpus absent (data/ not symlinked)")

BURNED = list(range(116000, 116010))


def test_fronto_parallel_projection_is_byte_identical_to_windowed_slide():
    """Stage A displacement DERIVED from depth reproduces the hand-set windowed
    slide EXACTLY — the ONLY change from 124000 is that the shift falls out of
    1/Z. depths [300,10,5], base 30 -> shifts [0,3,6]."""
    paths = bsds_paths()
    for sd in BURNED:
        sp = make_projected_scene(np.random.default_rng(sd), STAGE_A_DEPTHS, STAGE_A_BASE,
                                  BLOCK, GRID, 1, paths)
        sw = make_real_scene(np.random.default_rng(sd), [0, 3, 6], BLOCK, GRID, 1, paths, select="random")
        assert np.array_equal(sp["a"], sw["a"])
        assert np.array_equal(sp["b"], sw["b_depth"])
        assert sp["s_col"][::48].tolist() == [0, 3, 6]


def test_POSITIVE_CONTROL_a_gradient_render_is_NOT_byte_identical():
    """A SLANTED (per-column gradient) projection must DIFFER from the flat
    windowed slide — else the byte-identity test would be vacuous."""
    paths = bsds_paths()
    sp = make_projected_scene(np.random.default_rng(116000), [7.5], STAGE_A_BASE,
                              BLOCK, GRID, 0, paths, tilt=0.6, tilt_bands=(0,))
    # a flat single-plane render (tilt 0) at the same central depth
    flat = make_projected_scene(np.random.default_rng(116000), [7.5], STAGE_A_BASE,
                                BLOCK, GRID, 0, paths, tilt=0.0, tilt_bands=(0,))
    assert not np.array_equal(sp["b"], flat["b"])
    assert len(set(sp["s_col"].tolist())) > 1        # the gradient IS in the render


def test_no_fabrication_every_pixel_is_a_real_source_neighbour():
    """b[:, x] == src[:, x + off0 - s(x)] EXACTLY — no wrap, no invented edge.
    Reconstruct the render from `a` (the shared crop) via the integer shift and
    require exact equality on the columns whose source lies inside `a`."""
    paths = bsds_paths()
    sc = make_projected_scene(np.random.default_rng(116000), STAGE_A_DEPTHS, STAGE_A_BASE,
                              BLOCK, GRID, 1, paths)
    a, b, s_col, off0 = sc["a"], sc["b"], sc["s_col"], sc["off0"]
    for x in range(GRID):
        src_col = x - int(s_col[x])          # column of `a` this render column came from
        if src_col >= 0:                     # inside the shared static frame
            assert np.array_equal(b[:, x], a[:, src_col])


def test_static_camera_control_gives_one_blob():
    """base=0 -> b==a -> no flow -> one blob (the correct 'no motion' null)."""
    paths = bsds_paths()
    for sd in BURNED[:5]:
        sc = make_projected_scene(np.random.default_rng(sd), STAGE_A_DEPTHS, 0.0, BLOCK, GRID, 1, paths)
        assert np.array_equal(sc["a"], sc["b"])
        assert carve(sc, SQRT5)["eff"] == pytest.approx(1.0)
        assert carve(sc, 0.0)["eff"] == pytest.approx(1.0)


def test_depth_order_falls_out_of_the_projection():
    """The carve is told only pixels; the recovered residual ordering must match
    the true 1/Z ordering (nearer = larger residual) — never labelled."""
    paths = bsds_paths()
    ok = []
    for sd in BURNED:
        sc = make_projected_scene(np.random.default_rng(sd), STAGE_A_DEPTHS, STAGE_A_BASE,
                                  BLOCK, GRID, 1, paths)
        r = carve(sc, SQRT5)
        ok.append(r["depth_order_correct"])
        # nearer band (smallest Z = index 2) has the largest residual
        assert np.argmax(r["band_resid"]) == int(np.argmax(r["inv_Z"]))
    assert all(ok)


def test_slant_shatters_at_exact_tau_survives_at_sqrt5():
    """The Stage-B mechanism: a single slanted plane's within-surface gradient
    SHATTERS the surface at exact equality (eff climbs with tilt) but SURVIVES at
    √5 while the per-block step stays <= √5 (common-fate is a transitive flood).
    The threshold falls OUT of τ, it is not picked."""
    paths = bsds_paths()
    eff0, eff5, steps = {}, {}, {}
    for tilt in (0.0, 0.4, 0.8):
        e0, e5, st = [], [], []
        for sd in BURNED:
            sc = make_projected_scene(np.random.default_rng(sd), [7.5], STAGE_A_BASE,
                                      BLOCK, GRID, 0, paths, tilt=tilt, tilt_bands=(0,))
            e0.append(carve(sc, 0.0)["eff"]); e5.append(carve(sc, SQRT5)["eff"])
            st.append(float(np.abs(np.diff(sc["s_col"][::BLOCK])).max()))
        eff0[tilt] = np.mean(e0); eff5[tilt] = np.mean(e5); steps[tilt] = max(st)
    # τ=0 shatters monotonically; τ=√5 stays ~1 until the per-block step > √5
    assert eff0[0.4] > 2.5 and eff0[0.8] > eff0[0.4]        # exact-equality FALSIFY
    assert eff5[0.4] < 1.2                                   # gentle slant survives at √5
    assert steps[0.4] <= SQRT5 < steps[0.8]                  # threshold falls out of √5
    assert eff5[0.8] > eff5[0.4]                             # breaks once step > √5


def test_camera_rotation_corrupts_the_depth_order_the_registered_FALSIFY():
    """A small camera rotation drives the depth-order rate below 0.9 — the flow it
    induces is a within-field gradient a SINGLE-vector efference cannot null and
    common-fate cannot separate from depth parallax (names common-fate ->
    affine-flow)."""
    paths = bsds_paths()
    dok0, dok = [], []
    for sd in BURNED:
        s0 = make_projected_scene(np.random.default_rng(sd), STAGE_A_DEPTHS, STAGE_A_BASE,
                                  BLOCK, GRID, 1, paths, rot=0.0)
        sr = make_projected_scene(np.random.default_rng(sd), STAGE_A_DEPTHS, STAGE_A_BASE,
                                  BLOCK, GRID, 1, paths, rot=0.04)
        dok0.append(carve(s0, SQRT5)["depth_order_correct"])
        dok.append(carve(sr, SQRT5)["depth_order_correct"])
    assert np.mean(dok0) >= 0.9         # no rotation: order correct
    assert np.mean(dok) < 0.5           # small rotation: order lost (FALSIFY)


def test_char_module_has_no_tuned_threshold():
    """§13: the only numeric literals in the projection are geometry/sweep config
    (depths, base, tilt, rot, block, grid) and the inherited τ sentinels — NO
    verdict threshold compared against a measured quantity. Audited by shape: a
    constant inside a comparison whose other side is a MEASURED value would be a
    threshold; there are none in the char module's carve/render."""
    src = open(os.path.join(_ROOT, "scripts", "parallax_motion_char.py")).read()
    tree = ast.parse(src)
    # No Compare node whose comparator is a bare float literal other than the
    # documented sentinels (0.5 abs-diff confab count, 1e-3 depth floor, 0.0).
    ALLOWED = {0.0, 0.5, 1.0, 1e-3, 1.0}
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for cmp in node.comparators:
                if isinstance(cmp, ast.Constant) and isinstance(cmp.value, float):
                    if cmp.value not in ALLOWED:
                        offenders.append(cmp.value)
    assert not offenders, f"unaudited float threshold(s) in compare: {offenders}"
