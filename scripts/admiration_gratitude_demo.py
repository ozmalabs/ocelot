"""Live demo of ADMIRATION_GRATITUDE_PREREG.md -- prints the bug-fix
check plus the 6 registered predictions. Output pasted verbatim into the
paired RESULTS doc.
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


def crystallize_positive(inner, mt, pat):
    for _ in range(HATE_STABILITY_THRESHOLD + 3):
        r = record_hate_incident(inner, mt, pat, negative=False)
        if r["crystallized_this_call"] or r["admiration_crystallized_this_call"]:
            return r
    raise RuntimeError("did not crystallize")


print("=== Bug fix: repeated positive incidents never crystallize Hate ===")
inner, mt = fresh("mt1")
alex = mint_target_pattern(inner, mt, "Alex")
r1 = crystallize_positive(inner, mt, alex)
print("crystallized_this_call(Hate)=%s admiration_crystallized_this_call=%s route=%s gratitude_debt=%.4f"
      % (r1["crystallized_this_call"], r1["admiration_crystallized_this_call"],
         r1["admiration_consequence_route"], r1["gratitude_debt"]))
print("Hate nodes: %d, Admiration nodes: %d" % (len(list(inner.nodes("Hate"))), len(list(inner.nodes("Admiration")))))

print()
print("=== Prediction 3: controllability gates admiration's routing ===")
inner2, mt2 = fresh("mt2")
alex2 = mint_target_pattern(inner2, mt2, "Alex")
record_understanding_incident(inner2, alex2, exculpatory=True)
record_understanding_incident(inner2, alex2, exculpatory=True)
r2 = crystallize_positive(inner2, mt2, alex2)
print("uncontrollable positive pattern: route=%s admiration_ef=%.4f" % (
    r2["admiration_consequence_route"], r2["admiration_external_field"]))

print()
print("=== Prediction 4: gratitude_debt accumulates on every positive incident ===")
inner3, mt3 = fresh("mt3")
alex3 = mint_target_pattern(inner3, mt3, "Alex")
for i in range(3):
    r = record_hate_incident(inner3, mt3, alex3, negative=False)
    print("incident %d: gratitude_debt=%.4f admiration_crystallized_this_call=%s" % (
        i, r["gratitude_debt"], r["admiration_crystallized_this_call"]))

print()
print("=== Prediction 5: gratitude_debt amplifies admiration alpha (arousal held equal) ===")
base_alpha = 0.3
crystallization_arousal = 1.0


def run(pre_debt):
    inner_r, mt_r = fresh("mt_run_%s" % pre_debt)
    pat_r = mint_target_pattern(inner_r, mt_r, "Alex")
    inner_r.set_attr(pat_r, "confirm_streak", 2.0)
    inner_r.set_attr(pat_r, "incident_count", 1)
    inner_r.set_attr(pat_r, "gratitude_debt", pre_debt)
    regard_r = next(iter(inner_r.neighbours(pat_r, "tracks_concept")))
    inner_r.set_attr(regard_r, "external_field", 3.0)
    arousal_node_r = next(iter(inner_r.neighbours(pat_r, "tracks_arousal")))
    inner_r.set_attr(arousal_node_r, "level", crystallization_arousal)
    r = record_hate_incident(inner_r, mt_r, pat_r, negative=False, base_alpha=base_alpha)
    return r["effective_admiration_alpha"]


alpha_no_debt = run(pre_debt=0.0)
alpha_with_debt = run(pre_debt=1.0)
print("zero gratitude_debt: effective_admiration_alpha=%.4f (expect base_alpha*(1+arousal)=%.4f)"
      % (alpha_no_debt, base_alpha * (1.0 + crystallization_arousal)))
print("gratitude_debt=1.0:  effective_admiration_alpha=%.4f (expect base_alpha*(1+arousal)*(1+debt)=%.4f)"
      % (alpha_with_debt, base_alpha * (1.0 + crystallization_arousal) * 2.0))

print()
print("=== Prediction 6: per-target isolation ===")
inner4, mt4 = fresh("mt4")
jo = mint_target_pattern(inner4, mt4, "Jo")
crystallize_positive(inner4, mt4, jo)
kim = mint_target_pattern(inner4, mt4, "Kim")
r_kim = record_hate_incident(inner4, mt4, kim, negative=True)
print("Kim (unaffected by Jo's admiration): gratitude_debt=%.4f admiration_crystallized_this_call=%s"
      % (r_kim["gratitude_debt"], r_kim["admiration_crystallized_this_call"]))
