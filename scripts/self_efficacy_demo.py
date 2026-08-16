"""Live demo of SELF_EFFICACY_PREREG.md -- prints the 5 registered
predictions. Output pasted verbatim into the paired RESULTS doc.
"""
import substrate_rs as sr

from domains.can_self_worth_bridge import ensure_can_seed, find_or_build_resident_can
from domains.self_efficacy import (
    mint_domain_self_efficacy, read_persistence_disposition,
    record_self_efficacy_incident, sync_competence_to_affective_state,
)

CONFIDENT = {"name": "Confident", "index": 0, "params": {
    "resolution_bins": 8, "arousal": 0.2,
    "prior_world_safe": 0.6, "prior_self_worth": 0.9,
    "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
    "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
    "mood_bias": 0.3,
}}

s = sr.Substrate()
inner = s._inner
ensure_can_seed(inner)
resident_can = find_or_build_resident_can(inner, CONFIDENT)
concept = mint_domain_self_efficacy(inner, resident_can, "chess")

print("=== Predictions 1/2/3: success raises, failure lowers, persistence flips ===")
for i in range(3):
    v = record_self_efficacy_incident(inner, concept, success=True)
    print("success %d: efficacy=%.4f disposition=%s" % (i, v, read_persistence_disposition(v)))
for i in range(6):
    v = record_self_efficacy_incident(inner, concept, success=False)
    print("failure %d: efficacy=%.4f disposition=%s" % (i, v, read_persistence_disposition(v)))

print()
print("=== Prediction 4: no cross-domain generalization ===")
monopoly_concept = mint_domain_self_efficacy(inner, resident_can, "monopoly")
print("monopoly efficacy (unaffected by chess history): %.4f"
      % inner.node(monopoly_concept)["attrs"]["external_field"])

print()
print("=== Prediction 5: sync wires the confirmed-dead AffectiveState.competence field ===")
affect = inner.add_node("AffectiveState", {"competence": 0.0})
print("before sync: %.4f" % inner.node(affect)["attrs"]["competence"])
synced = sync_competence_to_affective_state(inner, affect, concept)
print("after sync: %.4f (returned: %.4f)" % (inner.node(affect)["attrs"]["competence"], synced))
