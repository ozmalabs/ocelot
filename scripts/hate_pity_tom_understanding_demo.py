"""Live demo of HATE_PITY_TOM_UNDERSTANDING_PREREG.md -- prints the 4
registered predictions. Output pasted verbatim into the paired RESULTS
doc.
"""
import json

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.hate_attribution import (
    HATE_STABILITY_THRESHOLD, mint_target_pattern, record_hate_incident,
    record_understanding_incident,
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


def crystallize(inner, mt, pat):
    for _ in range(HATE_STABILITY_THRESHOLD + 3):
        r = record_hate_incident(inner, mt, pat, negative=True)
        if r["crystallized_this_call"]:
            return r
    raise RuntimeError("did not crystallize")


print("=== Prediction 1: no understanding at all -> routes to removal ===")
inner, mt = fresh("mt1")
alex = mint_target_pattern(inner, mt, "Alex")
r1 = crystallize(inner, mt, alex)
print("consequence_route=%s removal_ef=%.4f pity_ef=%.4f controllability_ef=%.4f"
      % (r1["consequence_route"], r1["removal_desire_external_field"],
         r1["pity_external_field"], r1["controllability_external_field"]))

print()
print("=== Prediction 2: exculpatory understanding before crystallization -> routes to pity ===")
inner2, mt2 = fresh("mt2")
alex2 = mint_target_pattern(inner2, mt2, "Alex")
record_understanding_incident(inner2, alex2, exculpatory=True)
record_understanding_incident(inner2, alex2, exculpatory=True)
r2 = crystallize(inner2, mt2, alex2)
print("consequence_route=%s removal_ef=%.4f pity_ef=%.4f controllability_ef=%.4f"
      % (r2["consequence_route"], r2["removal_desire_external_field"],
         r2["pity_external_field"], r2["controllability_external_field"]))

print()
print("=== Prediction 3: boundary -- zero controllability (no info) routes to removal ===")
inner3, mt3 = fresh("mt3")
alex3 = mint_target_pattern(inner3, mt3, "Alex")
controllability3 = next(iter(inner3.neighbours(alex3, "tracks_controllability")))
print("controllability_for external_field before crystallization: %.4f"
      % inner3.node(controllability3)["attrs"]["external_field"])
r3 = crystallize(inner3, mt3, alex3)
print("consequence_route=%s" % r3["consequence_route"])

print()
print("=== Prediction 4: per-target isolation ===")
inner4, mt4 = fresh("mt4")
jo = mint_target_pattern(inner4, mt4, "Jo")
record_understanding_incident(inner4, jo, exculpatory=True)
record_understanding_incident(inner4, jo, exculpatory=True)
kim = mint_target_pattern(inner4, mt4, "Kim")
r_kim = crystallize(inner4, mt4, kim)
print("Kim (no understanding, unaffected by Jo's): consequence_route=%s" % r_kim["consequence_route"])
r_jo = crystallize(inner4, mt4, jo)
print("Jo (own exculpatory understanding): consequence_route=%s" % r_jo["consequence_route"])
