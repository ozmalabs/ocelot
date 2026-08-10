"""Gate for rung 124000 (parallax under real photometry).

The rung is a MEASUREMENT reusing the parallax carve; the thing that must be
gated is the STIMULUS CONSTRUCTION — that the real-texture windowed slide is an
EXACT rigid shift of `a` (no wrap, no fabrication), the honest analog of the
synthetic toroidal roll, and that the geometry is byte-identical to the
synthetic construction so the ONLY new variable is photometry. Each gate is
positive-controlled: a FABRICATING construction FAILS it.
"""
import os, sys
import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "scripts"), _ROOT, os.path.join(_ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from parallax_char import make_scene, group_common_fate  # noqa: E402
from parallax_real_char import make_real_scene, bsds_paths  # noqa: E402

SHIFTS = [0, 3, 6]; BLOCK = 8; GRID = 144; REF = 1
_HAVE_BSDS = os.path.isdir(os.path.join(_ROOT, "data", "vision_curriculum",
                                        "BSDS300", "images", "train"))
pytestmark = pytest.mark.skipif(not _HAVE_BSDS, reason="BSDS300 corpus absent (data/ not symlinked)")


def _scene():
    return make_real_scene(np.random.default_rng(116000), SHIFTS, BLOCK, GRID, REF, bsds_paths())


def test_windowed_depth_is_an_exact_rigid_shift_of_a():
    """b_depth[:, x in band i] == a[:, x - s_i] EXACTLY (no fabrication). For this
    geometry every x - s_i is a valid column of `a`, so the whole depth frame is
    an exact integer shift of the shared static frame."""
    sc = _scene(); a = sc["a"]; edges = sc["edges"]
    for i, s in enumerate(SHIFTS):
        for x in range(edges[i], edges[i + 1]):
            assert x - s >= 0
            assert np.array_equal(sc["b_depth"][:, x], a[:, x - s]), (i, x, s)


def test_a_toroidal_fabrication_would_FAIL_the_exact_shift_gate():
    """POSITIVE CONTROL: rolling `a` toroidally (the wrong, fabricating analog)
    differs from the windowed slide on the FLAT frame's wrap region, where the
    windowed construction sources REAL left-neighbours from src, not `a`'s wrapped
    right edge. If it did not differ, the gate above would be vacuous."""
    sc = _scene(); a = sc["a"]; s_ref = SHIFTS[REF]
    fabricated = np.roll(a, s_ref, axis=1)          # toroidal: left cols <- a's right edge
    # windowed b_flat sources real src neighbours for the leftmost s_ref columns;
    # a fabricating toroidal roll uses a's right edge there -> they MUST differ.
    assert not np.array_equal(sc["b_flat"][:, :s_ref], fabricated[:, :s_ref])
    # and they AGREE on the non-wrap overlap (x >= s_ref), proving it is a real shift
    assert np.array_equal(sc["b_flat"][:, s_ref:], a[:, : GRID - s_ref])


def test_geometry_byte_identical_to_synthetic():
    """owner / edges / ground-truth field come from the SAME geometry as the
    synthetic construction — only the pixels differ (the rung's whole claim)."""
    real = _scene()
    synth = make_scene(np.random.default_rng(116000), SHIFTS, BLOCK, grid=GRID, ref_idx=REF)
    assert real["edges"] == synth["edges"]
    assert np.array_equal(real["owner"], synth["owner"])
    assert np.array_equal(real["t_depth"], synth["t_depth"])
    assert np.array_equal(real["delta_ref"], synth["delta_ref"])


def test_static_frame_is_shared_and_bands_leave_no_special_trace():
    """`a` is ONE array; the depth bands sit at fixed columns unrelated to image
    content, so the boundary-column gradient is not systematically larger than the
    frame's — a static carver cannot key on the depth boundaries."""
    sc = _scene(); a = sc["a"]; gx = np.abs(np.diff(a, axis=1))
    bcols = [sc["edges"][i] - 1 for i in range(1, sc["N"])]
    bnd = float(np.mean([gx[:, c] for c in bcols])); within = float(np.mean(gx))
    # boundary gradient within a small factor of the overall gradient (no dedicated edge)
    assert 0.3 < bnd / within < 3.0, (bnd, within)


def test_carve_survives_real_photometry_smoke():
    """A smoke gate on the headline: the real-texture DEPTH field carves into a
    few-and-large knee (participation ratio in the object band) while FLAT does
    not. The full n=80 verdict lives in the results doc; this just guards the
    mechanism from silently dying."""
    from parallax_real_measure import carve_one, SQRT5
    sc = _scene()
    rec = carve_one(sc, SQRT5)
    p = np.array([f for f in rec["DEPTH"]["top5"] if f > 0]); p = p / p.sum()
    eff_depth = 1.0 / np.sum(p * p)
    assert 2.3 <= eff_depth <= 3.7, eff_depth              # few-but-plural
    assert rec["DEPTH"]["largest"] < 0.5                    # not one blob
    assert rec["FLAT"]["largest"] > 0.9                     # FLAT is one blob
