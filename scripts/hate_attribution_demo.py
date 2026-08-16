"""Live demo of hate_attribution -- prints the 7 registered predictions
(HATE_ATTRIBUTION_PREREG.md Sec3). Output pasted verbatim into the paired
RESULTS doc.
"""
import json

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.hate_attribution import (
    HATE_STABILITY_THRESHOLD, mint_target_pattern, record_hate_incident,
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


def fmt(r):
    return ("locus=%-14s streak=%d crystallized=%-5s (this_call=%-5s) "
            "regard_ef=%+.2f removal_ef=%+.2f" % (
                r["attribution_locus"], r["confirm_streak"], r["crystallized"],
                r["crystallized_this_call"], r["regard_external_field"],
                r["removal_desire_external_field"]))


print("=== Predictions 1/3/5/6: repeated negative incidents toward Alex ===")
inner, mt = fresh("mt1")
alex = mint_target_pattern(inner, mt, "Alex")
for i in range(HATE_STABILITY_THRESHOLD + 2):
    r = record_hate_incident(inner, mt, alex, negative=True)
    print("incident %d: %s" % (i, fmt(r)))

print()
print("=== Prediction 4: a positive exception resets confirm_streak ===")
inner2, mt2 = fresh("mt2")
sam = mint_target_pattern(inner2, mt2, "Sam")
r = record_hate_incident(inner2, mt2, sam, negative=True)
print("incident 0 (negative): %s" % fmt(r))
r = record_hate_incident(inner2, mt2, sam, negative=True)
print("incident 1 (negative, confirms): %s" % fmt(r))
r = record_hate_incident(inner2, mt2, sam, negative=False)
print("incident 2 (positive, exception): %s" % fmt(r))
r = record_hate_incident(inner2, mt2, sam, negative=True)
print("incident 3 (negative, streak restarts): %s" % fmt(r))

print()
print("=== Prediction 7: per-target isolation, ONE substrate ===")
inner3, mt3 = fresh("mt3")
jo = mint_target_pattern(inner3, mt3, "Jo")
kim = mint_target_pattern(inner3, mt3, "Kim")
for i in range(HATE_STABILITY_THRESHOLD + 1):
    record_hate_incident(inner3, mt3, jo, negative=True)
print("Jo crystallized: %s" % bool(inner3.node(jo)["attrs"]["crystallized"]))
r = record_hate_incident(inner3, mt3, kim, negative=True)
print("Kim's first incident (unaffected by Jo's crystallized hate): %s" % fmt(r))
print("Kim crystallized: %s" % bool(inner3.node(kim)["attrs"]["crystallized"]))
