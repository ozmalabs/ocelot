"""EMOTIONS AS EMERGENT MODULATOR REGIONS gate (seed block 207000) — re-derive
Bach/Dorner PSI/MicroPsi on the integer substrate. A DRIVE system sets six global
cognitive MODULATORS; named emotions are REGIONS in that modulator space. This
REPLACES 204000's 11 authored per-emotion appraisal rules with ~6 modulator
update rules + ~13 region predicates over the shared axes; blends free.

FRAMING (standing project rule): RE-DERIVE, not invent (the architecture is
Bach/Dorner's 2009/2012/2015); understanding, not judgment; the FUNCTIONAL
regulator, NOT a claim to felt qualia.

Pins the pre-registered criteria (MODULATORS_EMERGENCE_PREREG.md):
  * G-emerge (HEADLINE) — the 11-row 204000 emulation table reproduces FROM the
        modulator configuration (drives set -> modulators computed -> region
        assigned), with NO authored per-emotion appraisal rule present: same
        action tendency (byte-identical), same valence SIGN, same arousal BAND
        (the pre-registered HIGH>=600 / MID[150,599] / LOW<150 binning of the
        204000 numbers), exactly one region fires each, the null fires none.
  * G-blend — bliss (pos/low-arousal/high-res), angst (undirected anxiety), grief
        (directed sadness) each fall out as a DISTINCT region of the SAME space,
        with no new modulator/atom/drive.
  * G-social — the affiliation drive: anti-legitimacy (reproach) produces a
        negative-valence social appraisal 204000 could not reach; nurturing-
        absence (w_supergraph~0) reproduces the psychopathy signature FROM the
        drive side.
  * G-minimal-pair — the 204000 discriminators still hold THROUGH the
        modulators: fear/anxiety by the 196000 half-life alone, anger/frustration
        by blocker_present alone, curiosity/boredom by the sign of lp alone.
  * G-discipline — competence is a running accumulator; integer-native (terms AND
        produced values); default-OFF byte-identity; every rule guards on
        ModulatorState.enabled; the mechanism is graph rules (no Python engine).

The test RUNS the measure (able to fail if any tendency/valence/band/one-fire/
null mis-classifies FROM the modulator config, if a blend is a relabel, if
affiliation cannot reach the social appraisal, if a minimal pair does not flip,
if a float enters the rules, or if default-off is not byte-identical).
"""
import importlib

import pytest

M = importlib.import_module("scripts.modulator_emergence_measure")


@pytest.fixture(scope="module")
def res():
    return M.main()


# ----------------------------------------------------------------- G-emerge
def test_G_emerge_eleven_tendencies_from_modulator_config(res):
    ge = res["g_emerge"]
    assert ge["n"] == 11
    assert ge["n_correct"] == 11, [r for r in ge["rows"] if not r["correct"]]
    assert ge["all_correct"]
    assert ge["tendencies_match"]


def test_G_emerge_valence_signs_match(res):
    assert res["g_emerge"]["valence_signs_match"]
    for r in res["g_emerge"]["rows"]:
        assert r["valence"] == r["expected_valence"], r


def test_G_emerge_arousal_bands_match(res):
    assert res["g_emerge"]["arousal_bands_match"]
    for r in res["g_emerge"]["rows"]:
        assert r["arousal_band"] == r["expected_band"], r


def test_G_emerge_one_fire_each(res):
    ge = res["g_emerge"]
    assert ge["one_fire_each"]
    for r in ge["rows"]:
        assert r["n_fired"] == 1, r


def test_G_emerge_null_fires_none(res):
    assert res["g_emerge"]["null_fires_none"]


def test_G_emerge_no_authored_appraisal_present(res):
    # the falsifiable heart: the 204000 core_emotions seed is ABSENT and the
    # table still reproduces -> the 11 authored rules are redundant.
    assert res["source_audit"]["no_authored_appraisal_in_emergent_seed"]


# ----------------------------------------------------------------- G-blend
def test_G_blend_bliss_distinct_from_joy(res):
    assert res["g_blend"]["bliss_distinct"]


def test_G_blend_angst_distinct(res):
    assert res["g_blend"]["angst_distinct"]


def test_G_blend_grief_distinct_from_sadness(res):
    assert res["g_blend"]["grief_distinct"]


def test_G_blend_all_three_are_regions_not_relabels(res):
    assert res["g_blend"]["all_distinct"]


# ----------------------------------------------------------------- G-social
def test_G_social_affiliation_frustration_is_negative(res):
    assert res["criteria"]["g_social_affiliation_frustration_negative"]


def test_G_social_affiliation_praise_is_positive(res):
    assert res["criteria"]["g_social_affiliation_praise_positive"]


def test_G_social_nurturing_absence_removes_somatic_brake(res):
    # psychopathy from the drive side: healthy declines the harmful act, the
    # nurturing-absent (w=0) agent endorses it.
    assert res["criteria"]["g_social_psychopathy_removes_brake"]
    assert not res["g_social"]["healthy"]["endorses"]
    assert res["g_social"]["psychopath"]["endorses"]


# ------------------------------------------------------------- G-minimal-pair
def test_G_minimal_pair_discriminators_hold_through_modulators(res):
    d = res["g_minimal_pair"]
    assert d["all_ok"], d["pairs"]
    for p in d["pairs"]:
        assert p["a"] != p["b"], p


# -------------------------------------------------------------- G-discipline
def test_G_discipline_competence_is_a_running_accumulator(res):
    assert res["competence_accumulator"]["rises_monotonically"], \
        res["competence_accumulator"]["trace"]


def test_G_discipline_integer_native(res):
    assert res["integer_audit"]["all_integer"], res["integer_audit"]["offenders"]
    assert res["integer_values_audit"]["all_integer"], \
        res["integer_values_audit"]["offenders"]


def test_G_discipline_default_off_byte_identical(res):
    assert res["default_off"]["identical"]
    assert res["criteria"]["g_discipline_default_off_no_nodes"]


def test_G_discipline_six_modulators_and_demand_equations_are_rules(res):
    sa = res["source_audit"]
    assert sa["has_demand_equations"]
    assert sa["has_six_modulators"]
    assert sa["region_predicate_per_emotion"]
    assert sa["drive_decay_reuses_196000_scale2"]
    assert sa["modulators_depend_on_shared_atoms"]
    assert sa["every_rule_default_off_guarded"]
    assert sa["adapter_runs_no_python_rule_engine"]
