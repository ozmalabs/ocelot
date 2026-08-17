"""Live demo of BIGVILLE_DISPOSITION_GENERATOR_PREREG.md's ocelot-side
predictions (5-8). Output pasted verbatim into the paired RESULTS doc.
"""
import json

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.bigville_disposition_apply import (
    apply_resident_dispositions, index_bonds_by_holder,
)
from domains.can_self_worth_bridge import ensure_can_seed
from domains.hate_attribution import mint_target_pattern

CAST = json.load(open("seeds/bigville_cast100.json"))["residents"]
DISPOSITIONS = json.load(open("seeds/bigville_dispositions_cast100.json"))
BY_NAME = {r["name"]: r for r in CAST}


def fresh():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    for seed_path in ("seeds/shared_arousal.json", "seeds/hate_attribution.json"):
        d = json.load(open(seed_path))
        inner.load_seed_manifest(engine_rules_only(d))
    return inner


bonds_by_holder = index_bonds_by_holder(DISPOSITIONS["bonds"])
self_priors_by_name = DISPOSITIONS["self_priors"]

print("=== Prediction 4: group membership (own buckets + one out-group) ===")
inner = fresh()
resident = CAST[0]
r = apply_resident_dispositions(inner, resident, bonds_by_holder, self_priors_by_name)
print("resident=%s groups=%s" % (resident["name"], r["groups"]))

print()
print("=== Prediction 5: override wins, no accumulation with generated ===")
inner = fresh()
resident = CAST[10]
name = resident["name"]
other = bonds_by_holder[name][0]["toward"]
generated_belief_trust = bonds_by_holder[name][0]["belief_trust"]
r = apply_resident_dispositions(inner, resident, bonds_by_holder, self_priors_by_name,
                                overrides={"people": {other: {"regard": 1.75}}})
mt = r["resident_can"]["mt"]
pat = mint_target_pattern(inner, mt, other)
regard = next(iter(inner.neighbours(pat, "tracks_concept")))
ef = inner.node(regard)["attrs"]["external_field"]
print("generated belief_trust would have been %.4f; override=1.75; applied external_field=%.4f"
      % (generated_belief_trust, ef))

print()
print("=== Prediction 6: override-only person with no generated bond ===")
inner = fresh()
resident = CAST[20]
name = resident["name"]
generated_targets = {b["toward"] for b in bonds_by_holder.get(name, [])}
other = next(r2["name"] for r2 in CAST if r2["name"] != name and r2["name"] not in generated_targets)
r = apply_resident_dispositions(inner, resident, bonds_by_holder, self_priors_by_name,
                                overrides={"people": {other: {"admiration": 0.9}}})
print("%s in generated bonds? %s ; applied via override? %s" % (
    other, other in generated_targets, other in r["people"]))

print()
print("=== Prediction 7: self-belief domain = role ===")
inner = fresh()
resident = CAST[5]
r = apply_resident_dispositions(inner, resident, bonds_by_holder, self_priors_by_name)
print("resident=%s role=%s self=%s" % (resident["name"], resident["role"], r["self"]))

print()
print("=== Prediction 8: per-resident isolation ===")
inner = fresh()
from domains.can_self_worth_bridge import _find_resident_node
a, b = CAST[0], CAST[1]
apply_resident_dispositions(inner, a, bonds_by_holder, self_priors_by_name)
print("B present before B applied? %s" % (_find_resident_node(inner, b["name"]) is not None))
apply_resident_dispositions(inner, b, bonds_by_holder, self_priors_by_name)
print("B present after B applied? %s" % (_find_resident_node(inner, b["name"]) is not None))
