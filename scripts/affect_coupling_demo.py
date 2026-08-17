"""Live demo of AFFECT_COUPLING_SHAPE_PREREG.md -- prints the 9
registered predictions. Output pasted verbatim into the paired RESULTS
doc.
"""
import os

os.environ.setdefault("BIGVILLE_ROOT", "/home/matt/ozmadev/bigville")

from worlds.bigville_ocelot_adapter import BigvilleOcelotResident


def resident(name, **personality):
    r = BigvilleOcelotResident(name)
    r.seed_character(personality={"emotional_core_enabled": 0.0, **personality})
    r._ensure_speech_graph()
    return r


def set_arousal(r, value):
    a = next(iter(r.inner.neighbours(r.agent, "has_affective_state")))
    r.inner.set_attr(a, "arousal", float(value))
    r.inner.force_all_dirty()
    r.inner.run_rules()


def arm(r):
    r.inner.set_attr(r._affect_coupler, "coupling_on", 1.0)
    r.inner.force_all_dirty()
    r.inner.run_rules()


def barb_bias(r):
    opt = next(o for o in r._speech_options if r.s.node(o)["attrs"].get("name") == "barb")
    return r.s.node(opt)["attrs"]["affect_bias"]


print("=== Prediction 1: same rule couples SpeechOption AND Concept generically ===")
r1 = resident("P1", hostile_weight=0.8)
arm(r1)
set_arousal(r1, 0.4)
concept = r1.s.add_node("Concept", {"name": "throwaway", "affinity_hostile": 1.0})
r1.inner.add_edge_unchecked(r1._affect_coupler, "couples_affect_to", concept)
r1.inner.force_all_dirty()
r1.inner.run_rules()
print("Concept affect_bias=%.4f  SpeechOption(barb) affect_bias=%.4f" % (
    r1.s.node(concept)["attrs"]["affect_bias"], barb_bias(r1)))

print()
print("=== Prediction 2: coupling_on=0 -> affect_bias stays 0.0 ===")
r2 = resident("P2", hostile_weight=1.0)
set_arousal(r2, 0.9)
print("barb affect_bias=%.4f (coupling never armed)" % barb_bias(r2))

print()
print("=== Prediction 3: untagged node -> affect_bias == 0.0 exactly ===")
r3 = resident("P3", hostile_weight=0.8, charm_weight=0.9)
arm(r3)
set_arousal(r3, 0.9)
untagged = r3.s.add_node("Concept", {"name": "no_tags"})
r3.inner.add_edge_unchecked(r3._affect_coupler, "couples_affect_to", untagged)
r3.inner.force_all_dirty()
r3.inner.run_rules()
print("untagged affect_bias=%.4f" % r3.s.node(untagged)["attrs"]["affect_bias"])

print()
print("=== Prediction 4: disposition/arousal isolation ===")
low = resident("Low", hostile_weight=0.0); arm(low); set_arousal(low, 0.4)
high = resident("High", hostile_weight=0.8); arm(high); set_arousal(high, 0.4)
print("identical arousal=0.4: hostile_weight=0.0 -> barb=%.4f, hostile_weight=0.8 -> barb=%.4f" % (
    barb_bias(low), barb_bias(high)))
calm = resident("Calm", hostile_weight=0.4); arm(calm); set_arousal(calm, 0.0)
aroused = resident("Aroused", hostile_weight=0.4); arm(aroused); set_arousal(aroused, 0.9)
print("identical hostile_weight=0.4: arousal=0.0 -> barb=%.4f, arousal=0.9 -> barb=%.4f" % (
    barb_bias(calm), barb_bias(aroused)))

print()
print("=== Prediction 5: population-mean resident -> gains exactly neutral ===")
mean = resident("Mean", arousal=0.40, hostile_weight=0.40, charm_weight=0.50, valence=0.0, mood_bias=0.0)
arm(mean)
ca = mean.s.node(mean._affect_coupler)["attrs"]
print("reactivity_gain=%.4f hostile_gain=%.4f warmth_gain=%.4f trait_valence=%.4f mood_bias=%.4f" % (
    ca["reactivity_gain"], ca["hostile_gain"], ca["warmth_gain"], ca["trait_valence"], ca["mood_bias"]))

print()
print("=== Prediction 6 (CORRECTED -- relative magnitude decides, not a cap) ===")
rh = resident("RealHate", hostile_weight=0.0); arm(rh); set_arousal(rh, 0.0)
print("hostile_gain=%.4f" % rh.s.node(rh._affect_coupler)["attrs"]["hostile_gain"])
choice = rh.decide_speech("Landlord", relationship={"strength": -2.0, "kind": "feud"})
print("real feud relationship -> kind=%s" % choice["kind"])

natural = resident("NaturalMax", hostile_weight=1.0); arm(natural); set_arousal(natural, 1.0)
choice2 = natural.decide_speech("Landlord", relationship={"strength": 1.0, "kind": "chosen"})
print("natural-population-max hostile_gain=%.4f, moderate real warmth -> kind=%s" % (
    natural.s.node(natural._affect_coupler)["attrs"]["hostile_gain"], choice2["kind"]))

pathological = resident("Pathological", hostile_weight=5.0); arm(pathological); set_arousal(pathological, 1.0)
choice3 = pathological.decide_speech("Landlord", relationship={"strength": 1.0, "kind": "chosen"})
print("out-of-population hostile_gain=%.4f, SAME moderate real warmth -> kind=%s" % (
    pathological.s.node(pathological._affect_coupler)["attrs"]["hostile_gain"], choice3["kind"]))

print()
print("=== Prediction 7: settling order -- first and second call agree ===")
rs = resident("Settle", hostile_weight=0.8); arm(rs); set_arousal(rs, 0.5)
rs.decide_speech("A")
first = barb_bias(rs)
rs.decide_speech("A")
second = barb_bias(rs)
print("first=%.4f second=%.4f match=%s" % (first, second, abs(first - second) < 1e-9))

print()
print("=== Prediction 8: missing reference mean -> Div-by-zero -> gain silently 0 ===")
rn = resident("NoRef", hostile_weight=0.8)
rn.inner.set_attr(rn._affect_coupler, "hostile_ref", 0.0)
arm(rn)
print("hostile_gain=%.4f (expect 0.0, fail-quiet)" % rn.s.node(rn._affect_coupler)["attrs"]["hostile_gain"])

print()
print("=== Prediction 9 (CORRECTED -- natural bound, no cap) ===")
re_ = resident("Extreme", hostile_weight=1.0)
arm(re_)
print("hostile_weight=1.0 (_draw_clip's own max) -> hostile_gain=%.4f (natural bound, unclamped)" %
      re_.s.node(re_._affect_coupler)["attrs"]["hostile_gain"])
oop = resident("OutOfPopulation", hostile_weight=5.0)
arm(oop)
print("hostile_weight=5.0 (out-of-population) -> hostile_gain=%.4f (genuinely unbounded)" %
      oop.s.node(oop._affect_coupler)["attrs"]["hostile_gain"])
