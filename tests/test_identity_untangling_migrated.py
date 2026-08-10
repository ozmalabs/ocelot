"""IDENTITY UNTANGLING gate — the objecthood "what" wall.

Realizes `VISION_VENTRAL_GROUNDING.md` #1/#5 BY COMPOSITION over the sd loop
(no new Rust; no covariance/Hebbian). See `VISION_IDENTITY_UNTANGLING_PREREG.md`
/ `VISION_IDENTITY_UNTANGLING_RESULTS.md` (seeds 37000-37999).

    IDENTITY = covered_by (the base a discovered transform maps FROM)

REGIME A (held invertible discrete-similarity generators, gen_infer OFF) — the
bounded CROSSING: invariance + discrimination + measured untangling (vs a raw
control SHOWN to tangle) + noise floor + non-rigid-warp floor all hold.

REGIME B (GenInfer general integer-linear discovery, gen_infer ON) — the
DIAGNOSED NEGATIVE the crossing is defined by: the singular (det=0) map collapses
any shape onto a degenerate (collinear) target => a universal-container LEAK;
the reachable set is not a group => "same orbit" is not an equivalence => some
t(O_i) reads as O_j; an out-of-class input is force-explained. This test GATES
the diagnosis (leak present, floor collapses), not a green positive.

Fixtures mirror `scripts/identity_untangling_measure.py` exactly.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from scripts import identity_untangling_measure as M


def _gen_infer_live() -> bool:
    from substrate.boot_core import boot_core
    s, ag = boot_core()
    try:
        s._inner.evaluate({"type": "GenInfer",
                           "goal": {"type": "Lit", "value": [["cell", 0, 0, "x"]]}}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _gen_infer_live():
    pytest.skip("GenInfer Term not in the installed substrate_rs wheel",
                allow_module_level=True)


# ---- REGIME A: the bounded crossing (held invertible discrete-similarity) ----

def test_invariance_every_transformed_view_maps_to_its_own_identity():
    """t(O_i) -> O_i for every object x discrete-similarity transform (each view
    already carries a translation)."""
    A = M.regime_A()
    inv = A["invariance"]
    assert inv["wrong_id"] == 0 and inv["new"] == 0, (
        "INVARIANCE broke: %r" % inv["wrong_detail"])
    assert inv["correct"] == inv["total"], "not all views recognized as their own object"


def test_discrimination_no_generator_maps_distinct_objects_together():
    """The anti-universal-container CRUX (Sec 1.1): present O_j against codebook
    {O_i} only; no held generator may recognize it. Exact 0/42."""
    A = M.regime_A()
    d = A["discrimination"]
    assert d["fails"] == 0, "DISCRIMINATION broke (universal container): %r" % d["fail_detail"]


def test_untangling_orbit_separates_what_the_raw_rep_tangles():
    """The DiCarlo signature: the RAW template baseline ERRS (tangled) while the
    orbit-rep does not (untangled). PASS iff raw_wrong>0 AND orbit_wrong==0."""
    A = M.regime_A()
    u = A["untangling"]
    assert u["raw_wrong"] > 0, (
        "the raw-rep control did NOT tangle => the untangling claim would be "
        "vacuous (positive control on the measure)")
    assert u["orbit_wrong"] == 0, "orbit-rep tangled — did not separate"


def test_floor_a_noise_never_joins_an_existing_orbit():
    """100 random 5-cell 'objects' (seeds 37000-37099): 0 force-maps to an
    existing identity."""
    A = M.regime_A()
    f = A["floor_a_noise"]
    assert f["force_maps"] == 0, "a noise object spuriously joined an orbit: %r" % f["detail"]


def test_floor_b_nonrigid_warp_is_refused_not_force_mapped():
    """A single displaced cell (no global transform explains it) must NOT be
    recognized as an existing object."""
    A = M.regime_A()
    f = A["floor_b_warp"]
    assert f["force_maps"] == 0, "a non-rigid warp was force-mapped: %r" % f["detail"]


# ---- REGIME B: the DIAGNOSED NEGATIVE (general integer-linear discovery) ----

def test_singular_map_leak_collinear_target_is_a_universal_container_failure():
    """B1 — GenInfer enumerates NON-INJECTIVE (det=0) integer maps, so a
    degenerate (collinear) target is in the orbit of EVERYTHING. The discrimination
    measure has TEETH: it CATCHES this (Sec 1.1 — a degenerate 'everything
    matches' must FAIL, and here it does). Reported as the bounded boundary."""
    B = M.regime_B()
    leak = B["B1_collinear_leak"]
    assert leak["leak"] is True, (
        "the singular-map leak did NOT fire — if this ever flips, GenInfer has "
        "begun excluding non-injective maps and Regime B may be clean; re-open "
        "the prereg")
    assert leak["covered_by"] in M.OBJ, "a collinear object was recognized as a full-rank object"


def test_general_class_is_not_a_group_and_collapses_the_floor():
    """B2 — the reachable set of GenInfer is not a group (some t(O_i) reads as
    O_j) AND an out-of-class input is force-explained. This is the diagnosed
    negative for the AMBITIOUS general-integer-linear extension; the named fix
    (restrict to |det|=1) is deferred (gen_infer stays OFF by default)."""
    B = M.regime_B()
    assert B["B2_invariance_genON"]["wrong_id"] > 0, (
        "gen-ON invariance had no cross-object confusion — the not-a-group "
        "diagnosis would not reproduce")
    assert B["B2_floor_b_genON"]["force_maps"] > 0, (
        "gen-ON floor did not collapse — the over-permissiveness diagnosis "
        "would not reproduce")
