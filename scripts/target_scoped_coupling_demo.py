"""Live demo of TARGET_SCOPED_COUPLING_PREREG.md -- prints the 5
registered predictions. Output pasted verbatim into the paired RESULTS
doc.
"""
import os

os.environ.setdefault("BIGVILLE_ROOT", "/home/matt/ozmadev/bigville")

from domains.hate_attribution import (
    HATE_STABILITY_THRESHOLD, mint_target_pattern, record_hate_incident,
)
from worlds.bigville_ocelot_adapter import BigvilleOcelotResident

_TRACKS_EDGES = {
    "regard_for": "tracks_concept", "removal_desire_for": "tracks_removal_desire",
    "pity_for": "tracks_pity", "admiration_for": "tracks_admiration",
    "devaluation_for": "tracks_devaluation", "controllability_for": "tracks_controllability",
}


def resident(name, **personality):
    r = BigvilleOcelotResident(name)
    r.seed_character(personality={"emotional_core_enabled": 1.0, **personality})
    return r


def arm(r):
    r.inner.set_attr(r._affect_coupler, "coupling_on", 1.0)
    r.inner.force_all_dirty()
    r.inner.run_rules()


def concept(inner, pat, name):
    return next(iter(inner.neighbours(pat, _TRACKS_EDGES[name])))


print("=== Predictions 1/2: affinity tags are selective, pity/controllability uncoupled ===")
r1 = resident("Tags")
pat1 = mint_target_pattern(r1.inner, r1._resident_can["mt"], "Target")
r1._couple_target_pattern(pat1)
arm(r1)
for name in _TRACKS_EDGES:
    attrs = r1.s.node(concept(r1.inner, pat1, name))["attrs"]
    print("%-20s affinity_warm=%s affinity_hostile=%s affect_bias=%s" % (
        name, attrs.get("affinity_warm"), attrs.get("affinity_hostile"),
        attrs.get("affect_bias", "<no couples_affect_to edge>")))

print()
print("=== Prediction 3: independent update paths, mixed history ===")
r3 = resident("Independent", hostile_weight=0.6, charm_weight=0.6)
pat3 = mint_target_pattern(r3.inner, r3._resident_can["mt"], "Target")
r3._couple_target_pattern(pat3)
arm(r3)
a3 = next(iter(r3.inner.neighbours(r3.agent, "has_affective_state")))
r3.inner.set_attr(a3, "arousal", 0.5)
r3.inner.force_all_dirty()
r3.inner.run_rules()
record_hate_incident(r3.inner, r3._resident_can["mt"], pat3, negative=True)
record_hate_incident(r3.inner, r3._resident_can["mt"], pat3, negative=True)
for name in ("regard_for", "removal_desire_for", "admiration_for", "devaluation_for"):
    v = r3.s.node(concept(r3.inner, pat3, name))["attrs"]["external_field"]
    print("%-20s external_field=%.4f" % (name, v))

print()
print("=== Prediction 4: spite_gain isolates removal_desire_for from regard_for ===")
def crystallize(inner, mt, pat, spite_gain):
    for _ in range(HATE_STABILITY_THRESHOLD + 3):
        r = record_hate_incident(inner, mt, pat, negative=True, spite_gain=spite_gain)
        if r["crystallized_this_call"]:
            return r
    raise RuntimeError("did not crystallize")

low = resident("LowSpite", w_spite=0.05)
high = resident("HighSpite", w_spite=0.6)
arm(low); arm(high)
pat_low = mint_target_pattern(low.inner, low._resident_can["mt"], "Target")
pat_high = mint_target_pattern(high.inner, high._resident_can["mt"], "Target")
low._couple_target_pattern(pat_low)
high._couple_target_pattern(pat_high)
sg_low = low.s.node(low._affect_coupler)["attrs"]["spite_gain"]
sg_high = high.s.node(high._affect_coupler)["attrs"]["spite_gain"]
r_low = crystallize(low.inner, low._resident_can["mt"], pat_low, sg_low)
r_high = crystallize(high.inner, high._resident_can["mt"], pat_high, sg_high)
print("spite_gain: low=%.4f high=%.4f" % (sg_low, sg_high))
print("removal_desire_for: low=%.4f high=%.4f" % (
    r_low["removal_desire_external_field"], r_high["removal_desire_external_field"]))
print("regard_for (should match): low=%.4f high=%.4f" % (
    r_low["regard_external_field"], r_high["regard_external_field"]))

print()
print("=== Prediction 5: crystallization threshold unaffected by spite_gain ===")
def incidents_to_crystallize(w_spite, spite_gain):
    r = resident("Threshold%s" % w_spite, w_spite=w_spite)
    pat = mint_target_pattern(r.inner, r._resident_can["mt"], "Target")
    for i in range(HATE_STABILITY_THRESHOLD + 3):
        result = record_hate_incident(r.inner, r._resident_can["mt"], pat,
                                      negative=True, spite_gain=spite_gain)
        if result["crystallized_this_call"]:
            return i + 1
    raise RuntimeError("did not crystallize")

n_low = incidents_to_crystallize(0.15, 1.0)
n_high = incidents_to_crystallize(0.6, 4.0)
print("incidents to crystallize: spite_gain=1.0 -> %d, spite_gain=4.0 -> %d" % (n_low, n_high))
