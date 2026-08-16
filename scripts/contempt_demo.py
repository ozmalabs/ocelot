"""Live demo of CONTEMPT_PREREG.md -- prints the 5 registered
predictions. Output pasted verbatim into the paired RESULTS doc.
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


def crystallize_negative(inner, mt, pat, violation_type="harm"):
    for _ in range(HATE_STABILITY_THRESHOLD + 3):
        r = record_hate_incident(inner, mt, pat, negative=True, violation_type=violation_type)
        if r["crystallized_this_call"]:
            return r
    raise RuntimeError("did not crystallize")


print("=== Prediction 1: default violation_type still routes removal (backward compat) ===")
inner, mt = fresh("mt1")
alex = mint_target_pattern(inner, mt, "Alex")
r1 = crystallize_negative(inner, mt, alex)
print("route=%s removal_ef=%.4f devaluation_ef=%.4f" % (
    r1["consequence_route"], r1["removal_desire_external_field"], r1["devaluation_external_field"]))

print()
print("=== Prediction 2: a controllable norm violation routes to devaluation ===")
inner2, mt2 = fresh("mt2")
alex2 = mint_target_pattern(inner2, mt2, "Alex")
r2 = crystallize_negative(inner2, mt2, alex2, violation_type="norm")
print("route=%s removal_ef=%.4f devaluation_ef=%.4f" % (
    r2["consequence_route"], r2["removal_desire_external_field"], r2["devaluation_external_field"]))

print()
print("=== Prediction 3: controllability still gates independently of violation type ===")
inner3, mt3 = fresh("mt3")
alex3 = mint_target_pattern(inner3, mt3, "Alex")
record_understanding_incident(inner3, alex3, exculpatory=True)
record_understanding_incident(inner3, alex3, exculpatory=True)
r3 = crystallize_negative(inner3, mt3, alex3, violation_type="norm")
print("uncontrollable norm violation -> route=%s" % r3["consequence_route"])

print()
print("=== Prediction 4: devaluation_for's alpha is unamplified, unlike removal_desire_for's ===")
base_alpha = 0.3


def run(violation_type):
    inner_r, mt_r = fresh("mt_run_%s" % violation_type)
    pat_r = mint_target_pattern(inner_r, mt_r, "Alex")
    inner_r.set_attr(pat_r, "confirm_streak", 2.0)
    inner_r.set_attr(pat_r, "incident_count", 1)
    inner_r.set_attr(pat_r, "resentment_debt", 1.0)
    regard_r = next(iter(inner_r.neighbours(pat_r, "tracks_concept")))
    inner_r.set_attr(regard_r, "external_field", -3.0)
    arousal_node_r = next(iter(inner_r.neighbours(pat_r, "tracks_arousal")))
    inner_r.set_attr(arousal_node_r, "level", 1.0)
    return record_hate_incident(inner_r, mt_r, pat_r, negative=True,
                                violation_type=violation_type, base_alpha=base_alpha)


r_removal = run("harm")
r_devaluation = run("norm")
print("removal (amplified): effective_removal_alpha=%.4f" % r_removal["effective_removal_alpha"])
print("devaluation (flat):  devaluation_external_field=%.4f (== base_alpha=%.4f)"
      % (r_devaluation["devaluation_external_field"], base_alpha))

print()
print("=== Prediction 5: per-target isolation ===")
inner4, mt4 = fresh("mt4")
jo = mint_target_pattern(inner4, mt4, "Jo")
crystallize_negative(inner4, mt4, jo, violation_type="norm")
kim = mint_target_pattern(inner4, mt4, "Kim")
r_kim = record_hate_incident(inner4, mt4, kim, negative=True, violation_type="harm")
print("Jo crystallized=%s, Kim's own violation_type=%s (unaffected by Jo's)"
      % (bool(inner4.node(jo)["attrs"]["crystallized"]), inner4.node(kim)["attrs"]["violation_type"]))
