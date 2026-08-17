"""Regression for TARGET_SCOPED_COUPLING_PREREG.md (affect-coupling
Phase 4): the target-scoped social-disposition family (hate_attribution.py)
opts into the generic coupling rule, with distinct Concepts staying
distinct (the amygdala-modularity constraint).
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("BIGVILLE_ROOT", "/home/matt/ozmadev/bigville")

from pathlib import Path

from domains.hate_attribution import (
    HATE_STABILITY_THRESHOLD, mint_target_pattern, record_hate_incident,
)
from worlds.bigville_ocelot_adapter import BigvilleOcelotResident

_BIGVILLE_ROOT = Path(__file__).resolve().parents[2] / "bigville"
_SKIP = pytest.mark.skipif(
    not (_BIGVILLE_ROOT / "bigville" / "seeds" / "bigville_actor_decision.json").is_file(),
    reason="standalone Bigville checkout is not present")

_TRACKS_EDGES = {
    "regard_for": "tracks_concept", "removal_desire_for": "tracks_removal_desire",
    "pity_for": "tracks_pity", "admiration_for": "tracks_admiration",
    "devaluation_for": "tracks_devaluation", "controllability_for": "tracks_controllability",
}


def _resident(name, **personality):
    os.environ["BIGVILLE_ROOT"] = str(_BIGVILLE_ROOT)
    r = BigvilleOcelotResident(name)
    r.seed_character(personality={"emotional_core_enabled": 1.0, **personality})
    return r


def _arm(r):
    r.inner.set_attr(r._affect_coupler, "coupling_on", 1.0)
    r.inner.force_all_dirty()
    r.inner.run_rules()


def _concept(inner, pattern, name):
    return next(iter(inner.neighbours(pattern, _TRACKS_EDGES[name])))


# ---------------------------------------------------------------------
# 1/2. Affinity tagging is selective and correct.
# ---------------------------------------------------------------------
@_SKIP
def test_affinity_tags_match_the_registered_pathway_per_concept():
    r = _resident("Tags")
    pat = mint_target_pattern(r.inner, r._resident_can["mt"], "Target")
    r._couple_target_pattern(pat)
    expected_warm = {"regard_for", "admiration_for"}
    expected_hostile = {"removal_desire_for", "devaluation_for"}
    expected_none = {"pity_for", "controllability_for"}
    for name in expected_warm:
        attrs = r.s.node(_concept(r.inner, pat, name))["attrs"]
        assert attrs.get("affinity_warm") == 1.0, name
        assert attrs.get("affinity_hostile", 0.0) == 0.0, name
    for name in expected_hostile:
        attrs = r.s.node(_concept(r.inner, pat, name))["attrs"]
        assert attrs.get("affinity_hostile") == 1.0, name
        assert attrs.get("affinity_warm", 0.0) == 0.0, name
    for name in expected_none:
        attrs = r.s.node(_concept(r.inner, pat, name))["attrs"]
        assert "affinity_warm" not in attrs
        assert "affinity_hostile" not in attrs


@_SKIP
def test_pity_and_controllability_are_not_coupled_at_all():
    """Selective, not blanket: pity_for/controllability_for never get a
    couples_affect_to edge, so they never receive affect_bias even when
    coupling is armed -- distinct from "tagged but zero", genuinely
    excluded (a ToM belief and a low-controllability outcome are not on
    either affect pathway)."""
    r = _resident("NoCouple", hostile_weight=0.9)
    pat = mint_target_pattern(r.inner, r._resident_can["mt"], "Target")
    r._couple_target_pattern(pat)
    _arm(r)
    for name in ("pity_for", "controllability_for"):
        concept = _concept(r.inner, pat, name)
        assert "affect_bias" not in r.s.node(concept)["attrs"]


# ---------------------------------------------------------------------
# 3. Independent update paths: mixed incident history leaves each
#    Concept's own value independently driven, never conflated.
# ---------------------------------------------------------------------
@_SKIP
def test_concepts_update_independently_not_conflated():
    r = _resident("Independent", hostile_weight=0.6, charm_weight=0.6)
    pat = mint_target_pattern(r.inner, r._resident_can["mt"], "Target")
    r._couple_target_pattern(pat)
    _arm(r)
    a = next(iter(r.inner.neighbours(r.agent, "has_affective_state")))
    r.inner.set_attr(a, "arousal", 0.5)
    r.inner.force_all_dirty()
    r.inner.run_rules()

    record_hate_incident(r.inner, r._resident_can["mt"], pat, negative=True)
    record_hate_incident(r.inner, r._resident_can["mt"], pat, negative=True)

    regard = r.s.node(_concept(r.inner, pat, "regard_for"))["attrs"]["external_field"]
    removal = r.s.node(_concept(r.inner, pat, "removal_desire_for"))["attrs"]["external_field"]
    admiration = r.s.node(_concept(r.inner, pat, "admiration_for"))["attrs"]["external_field"]
    devaluation = r.s.node(_concept(r.inner, pat, "devaluation_for"))["attrs"]["external_field"]

    # driven by real negative incidents -- nonzero, and distinct from each
    # other (regard accumulates every incident's signal; removal_desire
    # only accumulates on the crystallizing call).
    assert regard != 0.0
    assert removal != 0.0
    assert regard != removal
    # untouched by any positive incident -- stayed exactly 0, proving the
    # coupling did not leak activity from the hostile pathway into the
    # warm one (or vice versa).
    assert admiration == 0.0
    assert devaluation == 0.0


# ---------------------------------------------------------------------
# 4. spite_gain isolates removal_desire_for from regard_for.
# ---------------------------------------------------------------------
@_SKIP
def test_spite_gain_diverges_removal_desire_not_regard():
    def crystallize(inner, mt, pat, spite_gain):
        for _ in range(HATE_STABILITY_THRESHOLD + 3):
            r = record_hate_incident(inner, mt, pat, negative=True, spite_gain=spite_gain)
            if r["crystallized_this_call"]:
                return r
        raise AssertionError("did not crystallize")

    low = _resident("LowSpite", w_spite=0.05)
    high = _resident("HighSpite", w_spite=0.6)
    _arm(low)
    _arm(high)
    pat_low = mint_target_pattern(low.inner, low._resident_can["mt"], "Target")
    pat_high = mint_target_pattern(high.inner, high._resident_can["mt"], "Target")
    low._couple_target_pattern(pat_low)
    high._couple_target_pattern(pat_high)

    sg_low = low.s.node(low._affect_coupler)["attrs"]["spite_gain"]
    sg_high = high.s.node(high._affect_coupler)["attrs"]["spite_gain"]
    assert sg_low != sg_high

    r_low = crystallize(low.inner, low._resident_can["mt"], pat_low, sg_low)
    r_high = crystallize(high.inner, high._resident_can["mt"], pat_high, sg_high)

    assert r_low["removal_desire_external_field"] != r_high["removal_desire_external_field"]
    assert r_low["regard_external_field"] == pytest.approx(r_high["regard_external_field"])


# ---------------------------------------------------------------------
# 5. Crystallization threshold unchanged -- disposition shades
#    magnitude, never gates.
# ---------------------------------------------------------------------
@_SKIP
def test_crystallization_threshold_unaffected_by_spite_gain():
    def incidents_to_crystallize(spite_gain):
        r = _resident("Threshold%s" % spite_gain, w_spite=0.6 if spite_gain != 1.0 else 0.15)
        pat = mint_target_pattern(r.inner, r._resident_can["mt"], "Target")
        for i in range(HATE_STABILITY_THRESHOLD + 3):
            result = record_hate_incident(r.inner, r._resident_can["mt"], pat,
                                          negative=True, spite_gain=spite_gain)
            if result["crystallized_this_call"]:
                return i + 1
        raise AssertionError("did not crystallize")

    assert incidents_to_crystallize(1.0) == incidents_to_crystallize(4.0)


# ---------------------------------------------------------------------
# 6. spite_gain=1.0 (default) is byte-identical to every pre-existing
#    caller -- the untouched HATE_RESENTMENT_PASSION_COUPLING regression.
# ---------------------------------------------------------------------
@_SKIP
def test_default_spite_gain_matches_pre_phase4_behavior():
    r = _resident("Regression")
    pat = mint_target_pattern(r.inner, r._resident_can["mt"], "Target")
    r.inner.set_attr(pat, "confirm_streak", 2.0)
    r.inner.set_attr(pat, "incident_count", 1)
    r.inner.set_attr(pat, "resentment_debt", 1.0)
    regard = next(iter(r.inner.neighbours(pat, "tracks_concept")))
    r.inner.set_attr(regard, "external_field", -3.0)
    arousal_node = next(iter(r.inner.neighbours(pat, "tracks_arousal")))
    r.inner.set_attr(arousal_node, "level", 1.0)
    result = record_hate_incident(r.inner, r._resident_can["mt"], pat,
                                  negative=True, base_alpha=0.3)
    assert result["effective_removal_alpha"] == pytest.approx(1.2)  # 0.3*(1+1)*(1+1)*1.0
