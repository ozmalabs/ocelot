"""Live demo of HATE_THRESHOLD_LOWER_BOUND_COUPLING_PREREG.md -- prints
the 4 registered predictions. Output pasted verbatim into the paired
RESULTS doc.
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


print("=== Prediction 1: at zero arousal, the gate matches the base constant ===")
inner, mt = fresh("mt1")
pat = mint_target_pattern(inner, mt, "Alex")
inner.set_attr(pat, "confirm_streak", float(HATE_STABILITY_THRESHOLD) - 0.1)
inner.force_all_dirty()
inner.run_rules(3000)
print("streak=%.1f (below base %d): crystallized=%s"
      % (HATE_STABILITY_THRESHOLD - 0.1, HATE_STABILITY_THRESHOLD,
         bool(inner.node(pat)["attrs"]["crystallized"])))
inner.set_attr(pat, "confirm_streak", float(HATE_STABILITY_THRESHOLD))
inner.force_all_dirty()
inner.run_rules(3000)
print("streak=%.1f (== base %d): crystallized=%s"
      % (HATE_STABILITY_THRESHOLD, HATE_STABILITY_THRESHOLD,
         bool(inner.node(pat)["attrs"]["crystallized"])))

print()
print("=== Prediction 2: elevated arousal crystallizes a streak that stays cold at zero arousal ===")
streak_value = float(HATE_STABILITY_THRESHOLD) - 1.0
inner_cold, mt_cold = fresh("cold")
pat_cold = mint_target_pattern(inner_cold, mt_cold, "Alex")
inner_cold.set_attr(pat_cold, "confirm_streak", streak_value)
inner_cold.force_all_dirty()
inner_cold.run_rules(3000)
print("cold (arousal=0): streak=%.1f crystallized=%s"
      % (streak_value, bool(inner_cold.node(pat_cold)["attrs"]["crystallized"])))

inner_hot, mt_hot = fresh("hot")
pat_hot = mint_target_pattern(inner_hot, mt_hot, "Alex")
arousal_hot = next(iter(inner_hot.neighbours(pat_hot, "tracks_arousal")))
inner_hot.set_attr(arousal_hot, "level", 1.0)
inner_hot.set_attr(pat_hot, "confirm_streak", streak_value)
inner_hot.force_all_dirty()
inner_hot.run_rules(3000)
print("hot (arousal=1.0, effective_threshold=%.2f): streak=%.1f crystallized=%s"
      % (HATE_STABILITY_THRESHOLD / 2.0, streak_value,
         bool(inner_hot.node(pat_hot)["attrs"]["crystallized"])))

print()
print("=== Prediction 3: both couplings crystallize sooner than the increment coupling alone ===")
inner3, mt3 = fresh("mt3")
pat3 = mint_target_pattern(inner3, mt3, "Alex")
live_count = 0
for _ in range(20):
    r = record_hate_incident(inner3, mt3, pat3, negative=True)
    live_count += 1
    if r["crystallized_this_call"]:
        break
print("live engine (both couplings): crystallized after %d incidents" % live_count)


def simulate(compare_to_effective_threshold):
    streak = 0.0
    level = 0.0
    for i in range(20):
        if i > 0:
            streak += 1.0 + level
        threshold = (HATE_STABILITY_THRESHOLD / (1.0 + level)
                     if compare_to_effective_threshold else HATE_STABILITY_THRESHOLD)
        level = level * AROUSAL_DECAY + AROUSAL_INTENSITY
        if i > 0 and streak >= threshold:
            return i + 1
    return None


print("simulated, both couplings: %d incidents" % simulate(True))
print("simulated, increment coupling ALONE (fixed base threshold): %d incidents" % simulate(False))

print()
print("=== Prediction 4: per-target isolation ===")
inner4, mt4 = fresh("mt4")
alex = mint_target_pattern(inner4, mt4, "Alex")
arousal_alex = next(iter(inner4.neighbours(alex, "tracks_arousal")))
inner4.set_attr(arousal_alex, "level", 2.0)
inner4.set_attr(alex, "confirm_streak", 1.5)
inner4.force_all_dirty()
inner4.run_rules(3000)
print("Alex (arousal=2.0, effective_threshold=1.0): streak=1.5 crystallized=%s"
      % bool(inner4.node(alex)["attrs"]["crystallized"]))

sam = mint_target_pattern(inner4, mt4, "Sam")
inner4.set_attr(sam, "confirm_streak", 1.5)
inner4.force_all_dirty()
inner4.run_rules(3000)
print("Sam (own arousal=0, same streak=1.5): crystallized=%s"
      % bool(inner4.node(sam)["attrs"]["crystallized"]))
