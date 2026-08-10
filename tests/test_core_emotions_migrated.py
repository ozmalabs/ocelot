"""THE CORE-EMOTION SET gate (seed block 204000) — each emotion an APPRAISAL ->
ACTION-TENDENCY pattern over the EXISTING signal economy (196000 staleness_decay
freshness/precision, 199000 present readout, 202000 learning-progress + value
atoms). Re-derive (Scherer/Lazarus/Frijda; Russell circumplex; Ekman; Damasio;
Hamilton/Erikson generativity), not invent.

FRAMING (standing project rule): understanding, not judgment; the FUNCTIONAL
regulator, NOT a claim to felt qualia.

Pins the measured criteria:
  * G1  EMULATION — 11 canonical appraisals -> 11 recognised action tendencies,
        exactly one emotion fires per appraisal, the null appraisal fires none,
        and the three minimal-pair discriminators (fear/anxiety on threat
        persistence; anger/frustration on blocker-approachability; curiosity/
        boredom on the sign of learning-progress) flip across the boundary.
  * G2  REFERENCE-FRAME + FULFILMENT — fulfilment fires for SUPERGRAPH
        contribution and is DISTINCT from individual joy (different reference
        frames); it reads the COLLECTIVE ledger (no gain -> no fulfilment) and is
        LOW-hedonic; a minimal social frame (pride) fires.
  * G3  HEDONIC / EUDAIMONIC DISSOCIATION — on the parenthood sweep (individual-
        costly + supergraph-beneficial) individual happiness FALLS while
        supergraph fulfilment RISES; the two value signals cross.
  * G4  VALUE-SIDE DISORDER GLASS-BOX (ties 199000) — psychopathy = the
        w_supergraph knob at ~0: fulfilment collapses while INDIVIDUAL value is
        untouched (reads others but does not value them), the somatic brake on a
        supergraph-harmful act is removed (healthy declines, psychopath endorses),
        and the knob is a PURE reversal. State-knobs OBSERVED reproduce the
        recognised factors (depression suppresses both frames; mania inflates).
  * G5  integer-native (terms AND produced values); default-OFF byte-identity.

The test RUNS the measure (able to fail if any appraisal mis-classifies, if two
emotions fire on one canonical appraisal, if fulfilment collapses to joy, if the
parenthood signals do not dissociate, if the psychopathy knob is not pure or
touches individual value, if a float enters the emotion rules, or if default-off
is not byte-identical). Prereg: VISION_CORE_EMOTIONS_PREREG.md.
"""
import importlib

import pytest

M = importlib.import_module("scripts.core_emotions_measure")


@pytest.fixture(scope="module")
def res():
    return M.main()


# ---------------------------------------------------------------------- G1
def test_G1_all_eleven_tendencies_correct(res):
    g1 = res["g1_emulation"]
    assert g1["n"] == 11
    assert g1["n_correct"] == 11, [r for r in g1["rows"] if not r["correct"]]
    assert g1["all_correct"]


def test_G1_exactly_one_emotion_fires_each(res):
    assert res["g1_emulation"]["one_fire_each"]
    for r in res["g1_emulation"]["rows"]:
        assert r["n_fired"] == 1, r


def test_G1_null_appraisal_fires_none(res):
    assert res["g1_emulation"]["null_fires_none"]


def test_G1_minimal_pair_discriminators(res):
    d = res["g1_discriminators"]
    assert d["all_ok"], d["pairs"]
    # each discriminator flips the classification by a SINGLE knob
    for p in d["pairs"]:
        assert p["a"] != p["b"], p


# ---------------------------------------------------------------------- G2
def test_G2_fulfilment_fires_for_supergraph(res):
    assert res["criteria"]["g2_fulfilment_fires"]


def test_G2_fulfilment_distinct_from_joy(res):
    c = res["criteria"]
    assert c["g2_joy_not_fulfilment"]
    assert c["g2_fulfilment_not_joy"]
    # low-hedonic: fulfilment with zero individual happiness
    assert c["g2_fulfilment_low_hedonic"]


def test_G2_fulfilment_reads_the_collective_ledger(res):
    # supergraph contribution that did NOT raise collective success -> no fulfilment
    assert res["criteria"]["g2_fulfilment_reads_collective"]


def test_G2_minimal_social_frame(res):
    assert res["criteria"]["g2_pride_social_frame"]


# ---------------------------------------------------------------------- G3
def test_G3_hedonic_eudaimonic_dissociation(res):
    c = res["criteria"]
    assert c["g3_happiness_falls"]
    assert c["g3_fulfilment_rises"]
    assert c["g3_signals_dissociate"], res["g3_dissociation"]["curve"]
    # the signature: happiness ends negative, fulfilment ends positive
    curve = res["g3_dissociation"]["curve"]
    assert curve[-1]["happiness"] < 0 < curve[-1]["fulfilment"]


# ---------------------------------------------------------------------- G4
def test_G4_psychopathy_pure_knob(res):
    c = res["criteria"]
    assert c["g4_knob_collapses_fulfilment"]
    assert c["g4_individual_value_untouched"]
    assert c["g4_reads_but_not_values"]
    assert c["g4_pure_knob_reversible"]


def test_G4_somatic_brake_removed(res):
    c = res["criteria"]
    # healthy DECLINES a supergraph-harmful act; the psychopath ENDORSES it
    assert c["g4_healthy_declines_harm"]
    assert c["g4_psychopath_endorses_harm"]
    assert c["g4_psychopathy_removes_brake"]


def test_G4_state_observed_produces_factors(res):
    c = res["criteria"]
    assert c["g4_state_observed_produces_factors"]
    assert c["g4_depression_suppresses_both"]
    assert c["g4_mania_inflates"]


# ---------------------------------------------------------------------- G5
def test_G5_integer_native(res):
    assert res["integer_audit"]["all_integer"], res["integer_audit"]["offenders"]
    assert res["integer_values_audit"]["all_integer"], \
        res["integer_values_audit"]["offenders"]


def test_G5_default_off_byte_identical(res):
    assert res["default_off"]["identical"]
    assert res["criteria"]["g5_default_off_no_nodes"]


# ------------------------------------------------------------------- source
def test_every_emotion_is_a_rule_reusing_the_atoms(res):
    sa = res["source_audit"]
    assert sa["every_emotion_is_a_rule"]
    assert sa["each_sets_own_hit"]
    assert sa["reuses_196000_freshness"]
    assert sa["reuses_202000_learning_progress"]
    assert sa["reuses_202000_value_atom"]
    assert sa["fulfilment_reads_supergraph"]
    assert sa["adapter_runs_no_python_rule_engine"]
