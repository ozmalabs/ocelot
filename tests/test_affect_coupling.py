"""Regression for AFFECT_COUPLING_SHAPE_PREREG.md (Phase 2): the single
reusable Rule (seeds/affect_coupling.json) that automatically couples a
resident's PSI modulator state + disposition gains onto ANY node
carrying a small affinity-tag shape.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("BIGVILLE_ROOT", "/home/matt/ozmadev/bigville")

from pathlib import Path

from worlds.bigville_ocelot_adapter import BigvilleOcelotResident

_BIGVILLE_ROOT = Path(__file__).resolve().parents[2] / "bigville"
_SKIP = pytest.mark.skipif(
    not (_BIGVILLE_ROOT / "bigville" / "seeds" / "bigville_actor_decision.json").is_file(),
    reason="standalone Bigville checkout is not present")


def _resident(name, **personality):
    """emotional_core_enabled=0.0 -- core_emotions.json's OWN rules
    continuously RECOMPUTE AffectiveState.arousal from Appraisal/
    ModulatorState (a real, pre-existing fact found while writing this
    test: a direct set_attr on arousal gets clobbered back to a formula-
    derived value on the next run_rules() once core_emotions is loaded).
    _ensure_affect_coupler/_ensure_speech_graph need only the boot-seeded
    AffectiveState (always present, affective_state_core is in boot_core.
    CORE_SEEDS) -- not core_emotions -- so isolation tests that need a
    KNOWN, externally-set arousal value stay bare."""
    os.environ["BIGVILLE_ROOT"] = str(_BIGVILLE_ROOT)
    r = BigvilleOcelotResident(name)
    r.seed_character(personality={"emotional_core_enabled": 0.0, **personality})
    r._ensure_speech_graph()  # also ensures _affect_coupler exists
    return r


def _set_arousal(resident, value):
    affective_state = next(
        iter(resident.inner.neighbours(resident.agent, "has_affective_state")))
    resident.inner.set_attr(affective_state, "arousal", float(value))
    resident.inner.force_all_dirty()
    resident.inner.run_rules()


def _arm_coupling(resident):
    resident.inner.set_attr(resident._affect_coupler, "coupling_on", 1.0)
    resident.inner.force_all_dirty()
    resident.inner.run_rules()


# ---------------------------------------------------------------------
# 1. Genericity: the SAME unmodified rule tags a SpeechOption AND a
#    throwaway Concept in one fixpoint.
# ---------------------------------------------------------------------
@_SKIP
def test_same_rule_couples_speechoption_and_concept_generically():
    r = _resident("Generic", hostile_weight=0.8)
    r._ensure_speech_graph()
    _arm_coupling(r)
    _set_arousal(r, 0.4)

    concept = r.s.add_node("Concept", {"name": "throwaway", "affinity_hostile": 1.0})
    r.inner.add_edge_unchecked(r._affect_coupler, "couples_affect_to", concept)
    r.inner.force_all_dirty()
    r.inner.run_rules()

    concept_bias = r.s.node(concept)["attrs"].get("affect_bias")
    barb = next(o for o in r._speech_options
               if r.s.node(o)["attrs"].get("name") == "barb")
    barb_bias = r.s.node(barb)["attrs"].get("affect_bias")
    assert concept_bias is not None and concept_bias != 0.0
    assert concept_bias == pytest.approx(barb_bias)  # both affinity_hostile=1.0


# ---------------------------------------------------------------------
# 2. coupling_on=0 is byte-identical to Phase 1 -- confirmed by the
#    UNCHANGED existing adapter test suite; restated here directly.
# ---------------------------------------------------------------------
@_SKIP
def test_coupling_off_by_default_affect_bias_stays_zero():
    r = _resident("Off", hostile_weight=1.0)
    r._ensure_speech_graph()
    _set_arousal(r, 0.9)
    barb = next(o for o in r._speech_options
               if r.s.node(o)["attrs"].get("name") == "barb")
    assert r.s.node(barb)["attrs"]["affect_bias"] == 0.0


# ---------------------------------------------------------------------
# 3. Untagged node -> affect_bias == 0.0 exactly (the Times-identity trap).
# ---------------------------------------------------------------------
@_SKIP
def test_untagged_node_gets_exactly_zero_bias():
    r = _resident("Untagged", hostile_weight=0.8, charm_weight=0.9)
    _arm_coupling(r)
    _set_arousal(r, 0.9)
    untagged = r.s.add_node("Concept", {"name": "no_affinity_tags"})
    r.inner.add_edge_unchecked(r._affect_coupler, "couples_affect_to", untagged)
    r.inner.force_all_dirty()
    r.inner.run_rules()
    assert r.s.node(untagged)["attrs"]["affect_bias"] == 0.0


# ---------------------------------------------------------------------
# 4. Disposition/arousal isolation: hostile_weight diverges at IDENTICAL
#    arousal; arousal also diverges at IDENTICAL hostile_weight. Neither
#    channel alone explains both.
# ---------------------------------------------------------------------
@_SKIP
def test_hostile_weight_diverges_bias_at_identical_arousal():
    low = _resident("LowHostile", hostile_weight=0.0)
    high = _resident("HighHostile", hostile_weight=0.8)
    for r in (low, high):
        r._ensure_speech_graph()
        _arm_coupling(r)
        _set_arousal(r, 0.4)
    barb_low = next(o for o in low._speech_options
                    if low.s.node(o)["attrs"].get("name") == "barb")
    barb_high = next(o for o in high._speech_options
                     if high.s.node(o)["attrs"].get("name") == "barb")
    bias_low = low.s.node(barb_low)["attrs"]["affect_bias"]
    bias_high = high.s.node(barb_high)["attrs"]["affect_bias"]
    assert bias_low != bias_high
    assert bias_high > bias_low  # higher hostile_weight -> more hostile bias


@_SKIP
def test_arousal_diverges_bias_at_identical_hostile_weight():
    calm = _resident("Calm", hostile_weight=0.4)
    aroused = _resident("Aroused", hostile_weight=0.4)
    calm._ensure_speech_graph()
    aroused._ensure_speech_graph()
    _arm_coupling(calm)
    _arm_coupling(aroused)
    _set_arousal(calm, 0.0)
    _set_arousal(aroused, 0.9)
    barb_calm = next(o for o in calm._speech_options
                     if calm.s.node(o)["attrs"].get("name") == "barb")
    barb_aroused = next(o for o in aroused._speech_options
                        if aroused.s.node(o)["attrs"].get("name") == "barb")
    bias_calm = calm.s.node(barb_calm)["attrs"]["affect_bias"]
    bias_aroused = aroused.s.node(barb_aroused)["attrs"]["affect_bias"]
    assert bias_calm != bias_aroused
    assert bias_aroused > bias_calm


# ---------------------------------------------------------------------
# 5. Population-mean resident -> every gain exactly 1.0/0.0.
# ---------------------------------------------------------------------
@_SKIP
def test_population_mean_resident_yields_neutral_gains():
    r = _resident("Mean", arousal=0.40, hostile_weight=0.40,
                 charm_weight=0.50, valence=0.0, mood_bias=0.0)
    _arm_coupling(r)
    attrs = r.s.node(r._affect_coupler)["attrs"]
    assert attrs["reactivity_gain"] == pytest.approx(1.0)
    assert attrs["hostile_gain"] == pytest.approx(1.0)
    assert attrs["warmth_gain"] == pytest.approx(1.0)
    assert attrs["trait_valence"] == pytest.approx(0.0)
    assert attrs["mood_bias"] == pytest.approx(0.0)


# ---------------------------------------------------------------------
# 6. Additive, never overriding: real crystallized hate still routes
#    hostile even with hostile_gain clamped to 0; the reverse also holds.
# ---------------------------------------------------------------------
@_SKIP
def test_real_relationship_dominates_a_zeroed_coupling_channel():
    r = _resident("RealHate", hostile_weight=0.0)  # hostile_gain -> 0
    _arm_coupling(r)
    _set_arousal(r, 0.0)
    r._ensure_speech_graph()
    assert r.s.node(r._affect_coupler)["attrs"]["hostile_gain"] == pytest.approx(0.0)

    choice = r.decide_speech(
        "Landlord",
        relationship={"strength": -2.0, "kind": "feud"},  # real, live relationship
    )
    assert choice["kind"] in ("barb", "complaint")  # existing affect_resentment term still fires


@_SKIP
def test_relative_magnitude_decides_not_an_architectural_cap():
    """CORRECTED (see AFFECT_COUPLING_SHAPE_RESULTS.md's retraction note):
    an earlier gain_cap=2.0 architecturally GUARANTEED disposition could
    never override a real relationship -- that was itself an invented,
    hand-tuned ceiling with no derivation, and the user correctly called
    it out as a violation of "let shapes decide, not numbers." Removed.
    Every _PARAM_SPEC trait is already naturally bounded by its own
    _draw_clip [0,1] range (hostile_ref=0.40 -> natural max gain 2.5 for
    any REAL generated resident), so a population-realistic extreme
    (hostile_weight=1.0, the natural max) does NOT flip even a MODERATE
    real relationship -- but a genuinely out-of-population disposition
    (hostile_weight=5.0 -- a pathological tail case, EMOTIONAL_SYSTEMS_
    UNIFICATION_DESIGN.md sec3b's own psychopathy/mania citations) CAN,
    because the actual relative magnitudes decide, not an architectural
    rule."""
    natural_max = _resident("NaturalMax", hostile_weight=1.0)
    _arm_coupling(natural_max)
    _set_arousal(natural_max, 1.0)
    choice_natural = natural_max.decide_speech(
        "Landlord", relationship={"strength": 1.0, "kind": "chosen"})
    assert choice_natural["kind"] not in ("barb", "complaint")

    pathological = _resident("Pathological", hostile_weight=5.0)
    _arm_coupling(pathological)
    _set_arousal(pathological, 1.0)
    choice_extreme = pathological.decide_speech(
        "Landlord", relationship={"strength": 1.0, "kind": "chosen"})
    assert choice_extreme["kind"] in ("barb", "complaint")


# ---------------------------------------------------------------------
# 7. Settling order: the first-ever and second decide_speech call read
#    the same settled bias (the install-order hazard fix).
# ---------------------------------------------------------------------
@_SKIP
def test_first_and_second_decide_speech_read_same_settled_bias():
    r = _resident("Settle", hostile_weight=0.8)
    _arm_coupling(r)
    _set_arousal(r, 0.5)

    first = r.decide_speech("A")
    barb = next(o for o in r._speech_options
               if r.s.node(o)["attrs"].get("name") == "barb")
    first_bias = r.s.node(barb)["attrs"]["affect_bias"]
    second = r.decide_speech("A")
    second_bias = r.s.node(barb)["attrs"]["affect_bias"]
    assert first_bias == pytest.approx(second_bias)


# ---------------------------------------------------------------------
# 8. Fail-quiet gain: a missing reference mean -> Div-by-zero -> gain
#    silently 0 -- asserted explicitly, not just risked.
# ---------------------------------------------------------------------
@_SKIP
def test_missing_reference_mean_silently_zeroes_the_gain():
    r = _resident("NoRef", hostile_weight=0.8)
    r.inner.set_attr(r._affect_coupler, "hostile_ref", 0.0)  # Div-by-zero
    _arm_coupling(r)
    assert r.s.node(r._affect_coupler)["attrs"]["hostile_gain"] == pytest.approx(0.0)


# ---------------------------------------------------------------------
# 9. RETRACTED: "gain_cap clamps extreme disposition" (an invented,
#    undocumented ceiling that architecturally guaranteed disposition
#    could never override a real relationship -- see AFFECT_COUPLING_
#    SHAPE_RESULTS.md's correction note). No cap exists any more.
#    Replaced with the actual, DERIVED natural bound: every _PARAM_SPEC
#    trait this normalises is already drawn against an explicit [0,1]
#    _draw_clip range, so a population-realistic resident's gain is
#    already naturally bounded WITHOUT any extra clamp -- confirmed here
#    directly, and an out-of-population value is confirmed UNBOUNDED
#    (test_relative_magnitude_decides_not_an_architectural_cap exercises
#    that case against a real decision).
# ---------------------------------------------------------------------
# rel=1e-4 (not pytest's default 1e-6): the gain now round-trips through
# an integer-quantized log-weight (AFFECT_COUPLING_SHAPE_PREREG.md's log-
# weight correction) at a DYNAMIC log_weight_scale -- the honest,
# declared precision budget is now ~1e-4 relative, not float64's
# undeclared ~1e-15. This tolerance is the datum, not a loosened test.
@_SKIP
def test_natural_max_disposition_gain_is_unclamped():
    r = _resident("NaturalMax", hostile_weight=1.0)  # _draw_clip's own max
    _arm_coupling(r)
    assert r.s.node(r._affect_coupler)["attrs"]["hostile_gain"] == pytest.approx(2.5, rel=1e-4)


@_SKIP
def test_out_of_population_disposition_gain_is_genuinely_unbounded():
    r = _resident("Pathological", hostile_weight=5.0)
    _arm_coupling(r)
    assert r.s.node(r._affect_coupler)["attrs"]["hostile_gain"] == pytest.approx(12.5, rel=1e-4)
