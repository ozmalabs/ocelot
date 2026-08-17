"""Live demo of AROUSAL_CHANNEL_RETIREMENT_PREREG.md -- prints the
registered predictions. Output pasted verbatim into the paired RESULTS
doc.
"""
import os

os.environ.setdefault("BIGVILLE_ROOT", "/home/matt/ozmadev/bigville")

from worlds.bigville_ocelot_adapter import BigvilleOcelotResident


def resident(name, **personality):
    r = BigvilleOcelotResident(name)
    r.seed_character(personality={"emotional_core_enabled": 1.0, **personality})
    return r


print("=== Prediction 1: hostile_weight=0, coupling OFF (default), high arousal ===")
r1 = resident("Neutral0Off")
choice1 = r1.decide_speech("Stranger", arousal=0.8)
print("kind=%s (old term would have unconditionally produced barb here)" % choice1["kind"])

print()
print("=== Prediction 1b: hostile_weight=0, coupling ON, high arousal -> NOT barb ===")
r1b = resident("Neutral0On", hostile_weight=0.0)
r1b._ensure_speech_graph()
r1b.inner.set_attr(r1b._affect_coupler, "coupling_on", 1.0)
r1b.inner.force_all_dirty()
r1b.inner.run_rules()
choice1b = r1b.decide_speech("Stranger", arousal=0.8)
print("kind=%s" % choice1b["kind"])

print()
print("=== Prediction 2: hostile_weight=1, coupling ON, high arousal -> still barb ===")
r2 = resident("Hostile1On", hostile_weight=1.0)
r2._ensure_speech_graph()
r2.inner.set_attr(r2._affect_coupler, "coupling_on", 1.0)
r2.inner.force_all_dirty()
r2.inner.run_rules()
choice2 = r2.decide_speech("Stranger", arousal=0.8)
print("kind=%s" % choice2["kind"])

print()
print("=== Prediction 4: arousal=0.0 isolation test is untouched by this phase ===")
resentful = resident("Resentful", social_dispositions={"Target": {"resentment_debt": 1.0, "regard": -0.8}})
grateful = resident("Grateful", social_dispositions={"Target": {"gratitude_debt": 1.0, "regard": 0.8}})
rc = resentful.decide_speech("Target", arousal=0.0)
gc = grateful.decide_speech("Target", arousal=0.0)
print("resentful kind=%s  grateful kind=%s  (still diverge, unaffected by this phase)" % (
    rc["kind"], gc["kind"]))

print()
print("=== Prediction 5: retiring the Python max-blend, arousal=0.0 case unaffected ===")
r5 = resident("Calm", social_dispositions={"Target": {"regard": 0.5}})
choice5 = r5.decide_speech("Target", arousal=0.0)
print("kind=%s (unaffected by max-blend retirement at the isolating arousal=0.0 case)" % choice5["kind"])
