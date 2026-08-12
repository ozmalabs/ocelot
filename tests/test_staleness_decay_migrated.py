"""STALENESS DECAY gate (seed block 196000) — the shared integer-half-life decay
primitive; the held surface DECOUPLES density from latency.

Reads the measured criteria and pins the mechanism-level claims:
  * G1  the DECOUPLING (static density climbs while moving latency stays flat,
        dominating the fixed-lr Pareto trade),
  * G2  FIRST-CLASSNESS (blend + foveation consumers key off the exposed
        freshness graph attribute; source audit),
  * G3  the FALSIFIER (uniform decay smears OR stops accumulating — both diverge),
  * G4  GENERICITY (byte-structurally-identical machinery on a second quantity),
  * G5  INTEGER-NATIVE decay bookkeeping (only the cross-frame blend is float).

The test RUNS the measure (able to fail on a flat static curve, a growing
latency, a non-diverging falsifier, or a float in the decay bookkeeping). G6
(power-law) is measured and reported but NOT gated — the prereg registered a null
as a valid honest result. Prereg: VISION_STALENESS_DECAY_PREREG.md.
"""
import importlib

import pytest

# OPTIONAL DEPENDENCY (red-test triage 2026-08-12): absent 'matplotlib' is a SKIP with a
# named reason, never a red. See tests/optional_deps.py.
from optional_deps import importorskip as _optional_importorskip  # noqa: E402
_optional_importorskip('matplotlib')


M = importlib.import_module("scripts.staleness_decay_measure")


@pytest.fixture(scope="module")
def res():
    # run the full measure once; returns the results dict
    import json
    import os
    M.main()
    with open(os.path.join(M.RESULTS, "staleness_decay.json")) as fh:
        return json.load(fh)


def test_G1_decoupling(res):
    c = res["criteria"]
    assert c["G1a_density_climbs"], res["static_asymptote"]
    assert c["G1b_latency_flat"], res["latency"]["gated"]
    assert c["G1c_decoupling_dominates"], (
        res["static_asymptote"], res["mean_latency"])
    # the gated point dominates BOTH fixed-lr controls' bad axis
    assert res["static_asymptote"]["gated"] <= 1.5 * res["static_asymptote"]["lr_low"]
    assert res["mean_latency"]["gated"] <= res["mean_latency"]["lr_high"] + 2


def test_G2_first_classness(res):
    c = res["criteria"]
    assert c["G2a_blend_keys_off_freshness"], res["mean_latency"]
    assert c["G2b_foveation_keys_off_freshness"], (
        res["G2b_frac_flagged_in_move"], res["G2b_frac_static_flagged"])
    assert c["G2c_source_audit_graph_resident"]


def test_G3_falsifier_both_diverge(res):
    c = res["criteria"]
    assert c["G3a_uniform_long_smears"]
    assert c["G3b_uniform_short_no_density"]
    assert c["G3_falsifier_both_diverge"]


def test_G4_genericity(res):
    c = res["criteria"]
    assert c["G4a_identical_machinery"], (
        res["G4a_skeleton_held"], res["G4a_skeleton_generic"])
    assert c["G4b_decaytrace_halves_exact"], res["G4b_decaytrace_seq"]
    assert res["G4a_skeleton_held"] == res["G4a_skeleton_generic"]


def test_G5_integer_native(res):
    c = res["criteria"]
    assert c["G5a_decay_bookkeeping_integer"], res["G5a_noninteger_cells"]
    assert res["G5a_noninteger_cells"] == 0
    assert c["G5b_only_blend_is_float"], res["G5b_bad_float"]
    # the cross-frame blend IS float (Div/Times) and the bookkeeping is NOT
    assert res["G5b_blend_uses_float"]
    assert res["G5b_bad_float"] == {}


def test_G6_power_law_reported(res):
    # NOT gated (prereg: a null is a valid honest result). Report presence.
    pl = res["power_law"]
    assert "slope" in pl and "r2_power" in pl and "r2_exp" in pl


def test_G7_existing_decay_audit_enumerated(res):
    audit = res["existing_decay_audit"]
    # every enumerated decay is classified, and the float decays are flagged
    assert len(audit["rows"]) >= 4
    assert audit["one_primitive_known_consumers"] is True
    assert "rod light adaptation (photon_retina)" in audit["float_decays"]
