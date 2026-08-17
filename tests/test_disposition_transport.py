"""Regression for DISPOSITION_TRANSPORT_PREREG.md (Phase 1 of
AFFECT_COUPLING_SHAPE_PREREG.md's build plan) -- every _PARAM_SPEC
disposition trait reaches a BigvilleOcelotResident, and the generated
disposition backstory (self_priors/bonds) applies via the EXISTING
bigville_disposition_apply.py applier instead of a parallel one.

No new rules exist yet -- this phase is pure transport. Predictions that
depend on an ALREADY-EXISTING consumer (mood_bias -> em_happiness) are
the only behavioral changes; everything else lands and does nothing yet
(a deliberate null, confirmed here).
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

_PARAM_SPEC_KEYS = (
    "resolution_bins", "arousal", "prior_world_safe", "prior_self_worth",
    "charm_weight", "hostile_weight", "prior_others_trust", "claim_weight",
    "w_supergraph", "w_spite", "mood_bias", "cred_on", "valence",
)


def _resident(name, **personality):
    monkeypatch_env = {"BIGVILLE_ROOT": str(_BIGVILLE_ROOT)}
    os.environ.update(monkeypatch_env)
    r = BigvilleOcelotResident(name)
    r.seed_character(personality={"emotional_core_enabled": 1.0, **personality})
    return r


# ---------------------------------------------------------------------
# 1. mood_bias, an ALREADY-EXISTING consumer (em_happiness), moves
#    behavior with zero new rules -- the one non-null prediction.
# ---------------------------------------------------------------------
@_SKIP
def test_mood_bias_diverges_happiness_via_existing_rule():
    low = _resident("Low", mood_bias=-0.8)
    high = _resident("High", mood_bias=0.8)

    low_state = low.record_action_outcome(action="help", applied=True)
    high_state = high.record_action_outcome(action="help", applied=True)

    assert low_state["appraisal"]["happiness"] != high_state["appraisal"]["happiness"]
    assert low_state["appraisal"]["total_value"] != high_state["appraisal"]["total_value"]


# ---------------------------------------------------------------------
# 2. All 13 traits present, named not counted.
# ---------------------------------------------------------------------
@_SKIP
def test_all_thirteen_param_spec_keys_present_on_agent_and_coupler():
    r = _resident("Full", **{k: 0.42 for k in _PARAM_SPEC_KEYS})
    agent_attrs = r.s.node(r.agent)["attrs"]
    for key in _PARAM_SPEC_KEYS:
        assert ("personality_" + key) in agent_attrs, key
        assert agent_attrs["personality_" + key] == pytest.approx(0.42)

    coupler_attrs = r.s.node(r._affect_coupler)["attrs"]
    expect = {
        "mood_bias": 0.42, "trait_valence": 0.42, "trait_arousal": 0.42,
        "trait_hostile_weight": 0.42, "trait_charm_weight": 0.42,
        "trait_w_spite": 0.42, "trait_cred_on": 0.42,
    }
    for key, value in expect.items():
        assert coupler_attrs[key] == pytest.approx(value), key


# ---------------------------------------------------------------------
# 3. w_spite/cred_on/valence land but change NOTHING yet (deliberate null).
# ---------------------------------------------------------------------
@_SKIP
def test_unconsumed_traits_are_transported_but_inert():
    baseline = _resident("Baseline")
    varied = _resident("Varied", w_spite=0.99, cred_on=0.01, valence=0.99)

    baseline_state = baseline.record_action_outcome(action="help", applied=True)
    varied_state = varied.record_action_outcome(action="help", applied=True)

    # trait_valence differs (transported) ...
    assert (varied.s.node(varied._affect_coupler)["attrs"]["trait_valence"]
            != baseline.s.node(baseline._affect_coupler)["attrs"]["trait_valence"])
    # ... but no rule reads it yet, so the appraisal outcome is unaffected.
    assert baseline_state["appraisal"]["happiness"] == pytest.approx(
        varied_state["appraisal"]["happiness"])
    assert baseline_state["appraisal"]["total_value"] == pytest.approx(
        varied_state["appraisal"]["total_value"])


# ---------------------------------------------------------------------
# 4. Real generated ingroup_affinity differs from the hardcoded 0.4
#    fallback, and _speech_bond's existing cap still applies.
# ---------------------------------------------------------------------
@_SKIP
def test_generated_ingroup_affinity_reaches_speech_bond_fallback():
    from worlds.bigville_ocelot_adapter import FAMILIARITY_CAP

    # Below the default (0.4) and below FAMILIARITY_CAP even at shared_
    # bucket_count=1, so the real generated value (not the cap, not the
    # hardcoded default) is what's actually being compared.
    r = _resident("Generated", self_priors={
        "ingroup_affinity": 0.15, "outgroup_suspicion": -0.2,
        "self_efficacy_prior": 0.0, "deservingness_prior": 0.0,
    })
    assert r.personality.get("ingroup_affinity") == pytest.approx(0.15)

    bond = r._speech_bond("Stranger", shared_bucket_count=1)
    warmth = r.s.node(bond)["attrs"]["affect_affection"]
    default_warmth = min(FAMILIARITY_CAP, 0.4 * 1 / 3.0)
    real_warmth = min(FAMILIARITY_CAP, 0.15 * 1 / 3.0)
    assert warmth == pytest.approx(real_warmth)
    assert warmth != pytest.approx(default_warmth)


# ---------------------------------------------------------------------
# 5. A real seeded social_dispositions entry still wins outright over
#    bucket familiarity -- the existing branch structure is untouched.
# ---------------------------------------------------------------------
@_SKIP
def test_real_social_disposition_still_wins_over_bucket_familiarity():
    r = _resident(
        "Disposed",
        self_priors={"ingroup_affinity": 0.95, "outgroup_suspicion": -0.2,
                     "self_efficacy_prior": 0.0, "deservingness_prior": 0.0},
        social_dispositions={"Target": {"regard": 2.0, "admiration": 2.0}},
    )
    bond = r._speech_bond("Target", shared_bucket_count=3)
    assert r.s.node(bond)["attrs"]["affect_affection"] == pytest.approx(2.0)


# ---------------------------------------------------------------------
# 6. Applying a generated backstory mints real target-scoped Concepts
#    (person, group buckets, self) via the reused applier -- not a
#    parallel implementation.
# ---------------------------------------------------------------------
@_SKIP
def test_generated_backstory_applies_via_existing_applier():
    r = _resident(
        "Backstory",
        self_priors={"ingroup_affinity": 0.4, "outgroup_suspicion": -0.2,
                     "self_efficacy_prior": 0.3, "deservingness_prior": -0.1},
        bonds=[{"holder": "Backstory", "toward": "Carl", "prior": "acquaintance",
               "belief_trust": 0.3, "affect_contempt": 0.0, "affect_trust": 0.1,
               "affect_resentment": 0.0, "affect_gratitude": 0.0, "tie_strength": 0.5}],
    )
    # Carl (person) + 4 own buckets (unspecified/unspecified/unspecified/
    # unspecified since no identity dims were supplied) + 1 outgroup bucket.
    assert len(list(r.s.nodes("TargetPattern"))) == 6
    names = {r.s.node(p)["attrs"]["target"] for p in r.s.nodes("TargetPattern")}
    assert "Carl" in names
