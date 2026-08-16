"""Live demo of HATE_STABILITY_AROUSAL_COUPLING_PREREG.md -- prints the 4
registered predictions. Output pasted verbatim into the paired RESULTS
doc.
"""
import json

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.hate_attribution import (
    AROUSAL_DECAY, AROUSAL_INTENSITY, HATE_STABILITY_THRESHOLD,
    mint_target_pattern, record_hate_incident,
)


def fresh(name):
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    for seed_path in ("seeds/shared_arousal.json", "seeds/hate_attribution.json"):
        d = json.load(open(seed_path))
        inner.load_seed_manifest(engine_rules_only(d))
    mt = inner.add_node("Microtheory", {"name": name, "temperature": 1.5})
    return inner, mt


print("=== Predictions 1/3: streak increment at baseline vs built-up arousal ===")
inner, mt = fresh("mt1")
alex = mint_target_pattern(inner, mt, "Alex")
prev = None
for i in range(4):
    r = record_hate_incident(inner, mt, alex, negative=True)
    increment_note = ""
    if prev is not None:
        expected = 1.0 + prev["arousal_level"]
        increment_note = " (increment=%.4f, expected 1+prev_arousal=%.4f)" % (
            r["confirm_streak"] - prev["confirm_streak"], expected)
    print("incident %d: locus=%-14s streak=%.4f arousal=%.4f crystallized_this_call=%s%s"
          % (i, r["attribution_locus"], r["confirm_streak"], r["arousal_level"],
             r["crystallized_this_call"], increment_note))
    prev = r

print()
print("=== Prediction 2: hot vs cold -- incidents needed to crystallize ===")
inner_hot, mt_hot = fresh("mt_hot")
pat_hot = mint_target_pattern(inner_hot, mt_hot, "Alex")
hot_n = 0
for _ in range(10):
    r = record_hate_incident(inner_hot, mt_hot, pat_hot, negative=True)
    hot_n += 1
    if r["crystallized_this_call"]:
        break
print("hot (back-to-back): crystallized after %d incidents" % hot_n)

inner_cold, mt_cold = fresh("mt_cold")
pat_cold = mint_target_pattern(inner_cold, mt_cold, "Sam")
arousal_node = next(iter(inner_cold.neighbours(pat_cold, "tracks_arousal")))
cold_n = 0
for _ in range(10):
    r = record_hate_incident(inner_cold, mt_cold, pat_cold, negative=True)
    cold_n += 1
    if r["crystallized_this_call"]:
        break
    for _ in range(20):
        lvl = inner_cold.node(arousal_node)["attrs"]["level"]
        inner_cold.set_attr(arousal_node, "level", lvl * AROUSAL_DECAY)
print("cold (arousal decayed between incidents): crystallized after %d incidents (pre-coupling pace: %d)"
      % (cold_n, HATE_STABILITY_THRESHOLD + 1))

print()
print("=== Prediction 4: per-target isolation ===")
inner4, mt4 = fresh("mt4")
jo = mint_target_pattern(inner4, mt4, "Jo")
for _ in range(3):
    record_hate_incident(inner4, mt4, jo, negative=True)
print("Jo's streak after 3 back-to-back incidents: %.4f (already past threshold %d)"
      % (inner4.node(jo)["attrs"]["confirm_streak"], HATE_STABILITY_THRESHOLD))
kim = mint_target_pattern(inner4, mt4, "Kim")
record_hate_incident(inner4, mt4, kim, negative=True)
r = record_hate_incident(inner4, mt4, kim, negative=True)
print("Kim's 2nd incident streak (unaffected by Jo's build-up): %.4f (expect 1+%.1f=%.1f)"
      % (r["confirm_streak"], AROUSAL_INTENSITY, 1.0 + AROUSAL_INTENSITY))
