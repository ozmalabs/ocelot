"""Live demo of DISPOSITION_TRANSPORT_PREREG.md -- prints the 6
registered predictions. Output pasted verbatim into the paired RESULTS
doc.
"""
import os

os.environ.setdefault("BIGVILLE_ROOT", "/home/matt/ozmadev/bigville")

from worlds.bigville_ocelot_adapter import FAMILIARITY_CAP, BigvilleOcelotResident

_PARAM_SPEC_KEYS = (
    "resolution_bins", "arousal", "prior_world_safe", "prior_self_worth",
    "charm_weight", "hostile_weight", "prior_others_trust", "claim_weight",
    "w_supergraph", "w_spite", "mood_bias", "cred_on", "valence",
)


def resident(name, **personality):
    r = BigvilleOcelotResident(name)
    r.seed_character(personality={"emotional_core_enabled": 1.0, **personality})
    return r


print("=== Prediction 1: mood_bias diverges happiness via em_happiness ===")
low = resident("Low", mood_bias=-0.8)
high = resident("High", mood_bias=0.8)
low_state = low.record_action_outcome(action="help", applied=True)
high_state = high.record_action_outcome(action="help", applied=True)
print("low mood_bias  happiness=%.4f total_value=%.4f" % (
    low_state["appraisal"]["happiness"], low_state["appraisal"]["total_value"]))
print("high mood_bias happiness=%.4f total_value=%.4f" % (
    high_state["appraisal"]["happiness"], high_state["appraisal"]["total_value"]))

print()
print("=== Prediction 2: all 13 _PARAM_SPEC keys present ===")
full = resident("Full", **{k: 0.42 for k in _PARAM_SPEC_KEYS})
agent_attrs = full.s.node(full.agent)["attrs"]
present = [k for k in _PARAM_SPEC_KEYS if ("personality_" + k) in agent_attrs]
print("present on agent: %d/13 -> %s" % (len(present), present))
coupler_attrs = full.s.node(full._affect_coupler)["attrs"]
print("coupler trait_* attrs:", {k: v for k, v in coupler_attrs.items() if k.startswith("trait_")})

print()
print("=== Prediction 3: w_spite/cred_on/valence transport but are inert ===")
baseline = resident("Baseline")
varied = resident("Varied", w_spite=0.99, cred_on=0.01, valence=0.99)
baseline_state = baseline.record_action_outcome(action="help", applied=True)
varied_state = varied.record_action_outcome(action="help", applied=True)
print("baseline trait_valence=%.4f  varied trait_valence=%.4f" % (
    baseline.s.node(baseline._affect_coupler)["attrs"]["trait_valence"],
    varied.s.node(varied._affect_coupler)["attrs"]["trait_valence"]))
print("baseline happiness=%.4f  varied happiness=%.4f (expect equal)" % (
    baseline_state["appraisal"]["happiness"], varied_state["appraisal"]["happiness"]))

print()
print("=== Prediction 4: generated ingroup_affinity reaches _speech_bond fallback ===")
generated = resident("Generated", self_priors={
    "ingroup_affinity": 0.15, "outgroup_suspicion": -0.2,
    "self_efficacy_prior": 0.0, "deservingness_prior": 0.0,
})
bond = generated._speech_bond("Stranger", shared_bucket_count=1)
warmth = generated.s.node(bond)["attrs"]["affect_affection"]
default_warmth = min(FAMILIARITY_CAP, 0.4 * 1 / 3.0)
real_warmth = min(FAMILIARITY_CAP, 0.15 * 1 / 3.0)
print("real warmth=%.4f  (old-default-would-have-been=%.4f)  match=%s" % (
    warmth, default_warmth, abs(warmth - real_warmth) < 1e-9))

print()
print("=== Prediction 5: real social_disposition still wins over bucket familiarity ===")
disposed = resident(
    "Disposed",
    self_priors={"ingroup_affinity": 0.95, "outgroup_suspicion": -0.2,
                 "self_efficacy_prior": 0.0, "deservingness_prior": 0.0},
    social_dispositions={"Target": {"regard": 2.0, "admiration": 2.0}},
)
bond2 = disposed._speech_bond("Target", shared_bucket_count=3)
print("affect_affection=%.4f (expect 2.0, the real disposition, not bucket-capped)" %
      disposed.s.node(bond2)["attrs"]["affect_affection"])

print()
print("=== Prediction 6: generated backstory applies via the existing applier ===")
backstory = resident(
    "Backstory",
    self_priors={"ingroup_affinity": 0.4, "outgroup_suspicion": -0.2,
                 "self_efficacy_prior": 0.3, "deservingness_prior": -0.1},
    bonds=[{"holder": "Backstory", "toward": "Carl", "prior": "acquaintance",
           "belief_trust": 0.3, "affect_contempt": 0.0, "affect_trust": 0.1,
           "affect_resentment": 0.0, "affect_gratitude": 0.0, "tie_strength": 0.5}],
)
patterns = list(backstory.s.nodes("TargetPattern"))
names = sorted(backstory.s.node(p)["attrs"]["target"] for p in patterns)
print("TargetPattern count=%d targets=%s" % (len(patterns), names))
