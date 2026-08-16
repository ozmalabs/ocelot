"""Live demo of HATE_RESENTMENT_PASSION_COUPLING_PREREG.md -- prints the
4 registered predictions. Output pasted verbatim into the paired RESULTS
doc.
"""
import json

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.hate_attribution import mint_target_pattern, record_hate_incident


def fresh(name):
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    for seed_path in ("seeds/shared_arousal.json", "seeds/hate_attribution.json"):
        d = json.load(open(seed_path))
        inner.load_seed_manifest(engine_rules_only(d))
    mt = inner.add_node("Microtheory", {"name": name, "temperature": 1.5})
    return inner, mt


print("=== Prediction 3 (residue check): resentment_debt matches the residue exactly ===")
inner, mt = fresh("mt1")
pat = mint_target_pattern(inner, mt, "Alex")
inner.set_attr(pat, "confirm_streak", 1.0)
inner.set_attr(pat, "incident_count", 1)
regard = next(iter(inner.neighbours(pat, "tracks_concept")))
inner.set_attr(regard, "external_field", -2.0)
arousal_node = next(iter(inner.neighbours(pat, "tracks_arousal")))
inner.set_attr(arousal_node, "level", 1.0)
r_exc = record_hate_incident(inner, mt, pat, negative=False)
print("streak after exception=%.4f resentment_debt=%.4f (should match)"
      % (r_exc["confirm_streak"], r_exc["resentment_debt"]))

print()
print("=== Prediction 4: resentment_debt accumulates across multiple exceptions ===")
inner2, mt2 = fresh("mt2")
pat2 = mint_target_pattern(inner2, mt2, "Alex")
inner2.set_attr(pat2, "confirm_streak", 2.0)
inner2.set_attr(pat2, "incident_count", 1)
regard2 = next(iter(inner2.neighbours(pat2, "tracks_concept")))
inner2.set_attr(regard2, "external_field", -3.0)
arousal_node2 = next(iter(inner2.neighbours(pat2, "tracks_arousal")))
inner2.set_attr(arousal_node2, "level", 1.0)
r1 = record_hate_incident(inner2, mt2, pat2, negative=False)
print("after exception 1: resentment_debt=%.4f" % r1["resentment_debt"])
inner2.set_attr(pat2, "confirm_streak", 2.0)
inner2.set_attr(regard2, "external_field", -3.0)
inner2.set_attr(arousal_node2, "level", 1.0)
r2 = record_hate_incident(inner2, mt2, pat2, negative=False)
print("after exception 2: resentment_debt=%.4f (should be roughly double)" % r2["resentment_debt"])

print()
print("=== Predictions 1/2/3: effective_removal_alpha, zero vs nonzero debt (arousal held equal) ===")
base_alpha = 0.3
crystallization_arousal = 1.0


def run(pre_debt):
    inner_r, mt_r = fresh("mt_run_%s" % pre_debt)
    pat_r = mint_target_pattern(inner_r, mt_r, "Alex")
    inner_r.set_attr(pat_r, "confirm_streak", 2.0)
    inner_r.set_attr(pat_r, "incident_count", 1)
    inner_r.set_attr(pat_r, "resentment_debt", pre_debt)
    regard_r = next(iter(inner_r.neighbours(pat_r, "tracks_concept")))
    inner_r.set_attr(regard_r, "external_field", -3.0)
    arousal_node_r = next(iter(inner_r.neighbours(pat_r, "tracks_arousal")))
    inner_r.set_attr(arousal_node_r, "level", crystallization_arousal)
    r = record_hate_incident(inner_r, mt_r, pat_r, negative=True, base_alpha=base_alpha)
    return r["effective_removal_alpha"]


alpha_no_debt = run(pre_debt=0.0)
alpha_with_debt = run(pre_debt=1.0)
print("zero resentment_debt: effective_removal_alpha=%.4f (expect base_alpha*(1+arousal)=%.4f)"
      % (alpha_no_debt, base_alpha * (1.0 + crystallization_arousal)))
print("resentment_debt=1.0:  effective_removal_alpha=%.4f (expect base_alpha*(1+arousal)*(1+debt)=%.4f)"
      % (alpha_with_debt, base_alpha * (1.0 + crystallization_arousal) * 2.0))
