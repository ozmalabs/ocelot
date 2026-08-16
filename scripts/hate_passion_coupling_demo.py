"""Live demo of HATE_PASSION_COUPLING_PREREG.md -- prints the 4 registered
predictions. Output pasted verbatim into the paired RESULTS doc.
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


print("=== Predictions 1/2: coupled removal alpha vs formula, back-to-back incidents ===")
inner, mt = fresh("mt_hot")
alex = mint_target_pattern(inner, mt, "Alex")
for i in range(HATE_STABILITY_THRESHOLD + 1):
    r = record_hate_incident(inner, mt, alex, negative=True, base_alpha=0.3)
    print("incident %d: arousal_level=%.4f effective_removal_alpha=%s crystallized_this_call=%s"
          % (i, r["arousal_level"],
             ("%.4f" % r["effective_removal_alpha"]) if r["effective_removal_alpha"] is not None else "n/a",
             r["crystallized_this_call"]))
level = 0.0
for _ in range(HATE_STABILITY_THRESHOLD):
    level = level * AROUSAL_DECAY + AROUSAL_INTENSITY
print("hand-computed pre-incident arousal level = %.4f -> expected alpha = %.4f"
      % (level, 0.3 * (1.0 + level)))

print()
print("=== Prediction 3: hot vs cold crystallization, same structural event ===")
inner_hot, mt_hot = fresh("mt_hot2")
pat_hot = mint_target_pattern(inner_hot, mt_hot, "Alex")
hot = None
for i in range(HATE_STABILITY_THRESHOLD + 1):
    hot = record_hate_incident(inner_hot, mt_hot, pat_hot, negative=True)
print("hot crystallization effective_removal_alpha = %.4f" % hot["effective_removal_alpha"])

inner_cold, mt_cold = fresh("mt_cold")
pat_cold = mint_target_pattern(inner_cold, mt_cold, "Sam")
arousal_node = next(iter(inner_cold.neighbours(pat_cold, "tracks_arousal")))
cold = None
for i in range(HATE_STABILITY_THRESHOLD + 1):
    cold = record_hate_incident(inner_cold, mt_cold, pat_cold, negative=True)
    for _ in range(20):
        lvl = inner_cold.node(arousal_node)["attrs"]["level"]
        inner_cold.set_attr(arousal_node, "level", lvl * AROUSAL_DECAY)
print("cold crystallization effective_removal_alpha = %.4f (arousal decayed to near-zero between incidents)"
      % cold["effective_removal_alpha"])

print()
print("=== Prediction 4: per-target isolation with arousal coupling ===")
inner4, mt4 = fresh("mt4")
jo = mint_target_pattern(inner4, mt4, "Jo")
for _ in range(HATE_STABILITY_THRESHOLD):
    record_hate_incident(inner4, mt4, jo, negative=True)
jo_arousal = inner4.node(next(iter(inner4.neighbours(jo, "tracks_arousal"))))["attrs"]["level"]
print("Jo's built-up arousal: %.4f" % jo_arousal)
kim = mint_target_pattern(inner4, mt4, "Kim")
r = record_hate_incident(inner4, mt4, kim, negative=True)
print("Kim's first incident arousal_level (unaffected by Jo's): %.4f (expect %.4f)"
      % (r["arousal_level"], AROUSAL_INTENSITY))
