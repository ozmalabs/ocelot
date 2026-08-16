"""Live demo of SHAPE_FIT_PREFERENCE_PREREG.md -- prints the 5 registered
predictions. Output pasted verbatim into the paired RESULTS doc.
"""
import json

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.shape_fit_preference import preference_from_shape


def fresh(name):
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    d = json.load(open("seeds/shared_arousal.json"))
    inner.load_seed_manifest(engine_rules_only(d))
    mt = inner.add_node("Microtheory", {"name": name, "temperature": 1.5})
    return inner, mt


PROTO_SIG = [["shape", "round"], ["color", "red"], ["size", "small"]]

print("=== Predictions 1/2/3: the inverted-U over fluency ===")
inner, mt = fresh("mt1")
inner.add_node("ShapeSignature", {"name": "proto", "signature": PROTO_SIG})

for label, goal in [
    ("exact match (fluency=1.0)", list(PROTO_SIG)),
    ("partial match (fluency=2/3)", [["shape", "round"], ["color", "green"], ["size", "small"]]),
    ("total novelty (fluency=0.0)", [["shape", "triangle"], ["color", "green"], ["size", "medium"]]),
]:
    r = preference_from_shape(inner, mt, "stimulus_%s" % label[:6], goal)
    print("%-32s fluency=%.4f preference=%.4f arousal=%.4f"
          % (label, r["fluency"], r["preference"], r["arousal_level"]))

print()
print("=== Prediction 4: symmetry around the midpoint ===")
inner2, mt2 = fresh("mt2")
proto_rels = [["k%d" % i, "v%d" % i] for i in range(10)]
inner2.add_node("ShapeSignature", {"name": "proto10", "signature": proto_rels})
goal_30 = proto_rels[:3] + [["novel%d" % i, "x"] for i in range(7)]
goal_70 = proto_rels[:7] + [["novel%d" % i, "x"] for i in range(3)]
r30 = preference_from_shape(inner2, mt2, "s_30", goal_30)
r70 = preference_from_shape(inner2, mt2, "s_70", goal_70)
print("fluency=0.3: preference=%.6f" % r30["preference"])
print("fluency=0.7: preference=%.6f" % r70["preference"])
print("match:", abs(r30["preference"] - r70["preference"]) < 1e-9)

print()
print("=== Prediction 5: novelty feeds the shared arousal pool ===")
inner3, mt3 = fresh("mt3")
inner3.add_node("ShapeSignature", {"name": "proto", "signature": PROTO_SIG})
r_familiar = preference_from_shape(inner3, mt3, "s_familiar", list(PROTO_SIG))
r_novel = preference_from_shape(inner3, mt3, "s_novel",
    [["shape", "triangle"], ["color", "green"], ["size", "medium"]])
print("familiar stimulus arousal_level: %.4f" % r_familiar["arousal_level"])
print("novel stimulus arousal_level:    %.4f" % r_novel["arousal_level"])
