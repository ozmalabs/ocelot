"""DISSIPATION IS INFERENCE gate (seed block 197000) — one integer relaxation
dynamics that is a physical law in one frame and MAP perception in the other,
differing ONLY by a relabel.

Runs the measure (able to fail on a non-byte-identical trajectory, a non-monotone
free energy, a recovery that does not reach the reference MAP, an anti-dissipative
run that does NOT break the recovery, or a float in a cell attr).

  G1  THE IDENTITY            — byte-identical trajectory + equal functionals + pure relabel
  G2  PHYSICS HOLDS (2nd law) — free energy monotone down to a fixed point; entropy up
  G3  COGNITION WORKS         — denoises; fixed point MATCHES the reference MAP
  G4  BREAK-ONE-BREAKS-BOTH   — anti-dissipative forces E up AND recovery diverges
  G5  INTEGER-NATIVE / OFF    — no float cell attr; seed unreferenced by any default loader

Prereg: DISSIPATION_IS_INFERENCE_PREREG.md.
"""
import importlib

import pytest

M = importlib.import_module("scripts.dissipation_inference_measure")


@pytest.fixture(scope="module")
def res():
    return M.main()


def test_G1_the_identity(res):
    g = res["G1"]
    assert g["byte_identical_trajectory"], "the two label-runs diverged (relabel leaked into dynamics)"
    assert g["functionals_equal"], (g["E_phys_head"], g["E_cog_head"])
    assert g["relabel_pure"] and not g["relabel_in_dynamics"]
    assert g["pass"]


def test_G2_physics_second_law(res):
    g = res["G2"]
    assert g["monotone_non_increasing"], "free energy INCREASED on the sound path"
    assert g["reached_fixed_point"]
    assert g["entropy_monotone_up"]
    assert g["E_final"] < g["E0"]
    assert g["pass"]


def test_G3_cognition_recovers_the_map(res):
    g = res["G3"]
    assert g["final_err"] < g["input_err"], "settling did not denoise"
    assert g["matches_reference_denoiser"], "fixed point is NOT the reference MAP"
    assert g["max_dev_from_real_map"] <= 1
    assert g["pass"]


def test_G4_break_one_breaks_both(res):
    g = res["G4"]
    # forcing the physics (free energy) UP must break the perceptual recovery
    assert g["E_monotone_up"], "anti-dissipative run did not raise E"
    assert g["err_monotone_up"], "anti-dissipative run did not break recovery"
    assert g["diverged"]
    assert g["pass"]


def test_G5_integer_native_and_default_off(res):
    g = res["G5"]
    assert g["noninteger_attr_writes"] == 0, "a float appeared in an in-frame cell attr"
    assert g["default_off"], g["seed_referenced_by"]
    assert g["pass"]
