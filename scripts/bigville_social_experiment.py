"""Social experiment #1 -- a small, hand-authored cast of theory-testing
archetypes, driven through real Ocelot cognition (BigvilleOcelotResident),
each interaction applied as an actual recorded incident (not a backdoor
read of another resident's hidden state), then their graphs inspected.

Predictions registered here (before reading the output below) --
see docs/research/bigville/BIGVILLE_SOCIAL_EXPERIMENT_1_RESULTS.md for the
predicted-vs-actual writeup:

  Resentful (toward Landlord): repeated negative incidents should
    crystallize hate -> consequence_route="removal", removal_desire_for
    external_field > 0.
  Grateful (toward Landlord): repeated positive incidents should
    crystallize admiration -> consequence_route="admiration",
    admiration_for external_field > 0, gratitude_debt > 0.
  Envier (toward Landlord, an advantaged peer): negative relative_self_
    worth + a seeded negative deservingness_prior should read as
    "malicious" envy (Smith & Kim 2007 / Van de Ven et al. 2009).
  decide_speech: every character's chosen speech KIND toward Landlord is
    predicted to be IDENTICAL regardless of the above (a probe of the
    already-suspected gap: SpeechOption's relational-affect coefficients
    -- warm_aff/hostile_aff/etc -- are never set by worlds/bigville_
    speech_world.py's SPEECH_MENU, so the affect-gain term in
    sp_choose_utterance always multiplies by zero).
"""
import os

os.environ.setdefault("BIGVILLE_ROOT", "/home/matt/ozmadev/bigville")

from domains.can_self_worth_bridge import (
    mint_domain_self_worth, mint_peer_comparison_context,
    read_relative_self_worth, record_peer_observation,
)
from domains.envy import mint_domain_deservingness_belief, read_envy
from domains.hate_attribution import (
    HATE_STABILITY_THRESHOLD, mint_target_pattern, record_hate_incident,
)
from worlds.bigville_ocelot_adapter import BigvilleOcelotResident


def dump_social_state(resident, target):
    """Every Concept this resident holds whose name ends `:target`, plus
    the target's own TargetPattern ledger/crystallization state."""
    out = {}
    for c in resident.s.nodes("Concept"):
        name = resident.s.node(c)["attrs"].get("name", "")
        if name.endswith(":" + target):
            out[name] = round(resident.s.node(c)["attrs"].get("external_field", 0.0), 4)
    for pat in resident.s.nodes("TargetPattern"):
        attrs = resident.s.node(pat)["attrs"]
        if attrs.get("target") == target:
            out["_pattern"] = {
                "crystallized": bool(attrs.get("crystallized")),
                "resentment_debt": round(attrs.get("resentment_debt", 0.0), 4),
                "gratitude_debt": round(attrs.get("gratitude_debt", 0.0), 4),
                "incident_count": attrs.get("incident_count"),
            }
    return out


print("=" * 70)
print("CAST SETUP")
print("=" * 70)

landlord = BigvilleOcelotResident("Landlord")
landlord.seed_character(personality={"emotional_core_enabled": 1.0})
print("Landlord: neutral control, no seeded dispositions toward anyone.")

resentful = BigvilleOcelotResident("Resentful")
resentful.seed_character(personality={
    "emotional_core_enabled": 1.0,
    "social_dispositions": {"Landlord": {"resentment_debt": 1.0, "regard": -0.5}},
})
pat = mint_target_pattern(resentful.inner, resentful._resident_can["mt"], "Landlord")
resentful_crystallize_result = None
for i in range(HATE_STABILITY_THRESHOLD + 3):
    r = record_hate_incident(resentful.inner, resentful._resident_can["mt"], pat,
                             negative=True, violation_type="harm")
    if r["crystallized_this_call"]:
        resentful_crystallize_result = r
        resentful_incidents = i + 1
        break
else:
    resentful_incidents = HATE_STABILITY_THRESHOLD + 3
print("Resentful: seeded baseline resentment toward Landlord, then %d negative "
      "incidents recorded (repeated withheld-rent-style grievances)." % resentful_incidents)

grateful = BigvilleOcelotResident("Grateful")
grateful.seed_character(personality={
    "emotional_core_enabled": 1.0,
    "social_dispositions": {"Landlord": {"gratitude_debt": 1.0, "regard": 0.5}},
})
pat_g = mint_target_pattern(grateful.inner, grateful._resident_can["mt"], "Landlord")
grateful_crystallize_result = None
for i in range(HATE_STABILITY_THRESHOLD + 3):
    r = record_hate_incident(grateful.inner, grateful._resident_can["mt"], pat_g,
                             negative=False, violation_type="harm")
    if r["admiration_crystallized_this_call"]:
        grateful_crystallize_result = r
        grateful_incidents = i + 1
        break
else:
    grateful_incidents = HATE_STABILITY_THRESHOLD + 3
print("Grateful: seeded baseline gratitude toward Landlord, then %d positive "
      "incidents recorded (repeated favors/repairs done well)." % grateful_incidents)

envier = BigvilleOcelotResident("Envier")
envier.seed_character(personality={
    "emotional_core_enabled": 1.0,
    "deservingness_prior": -0.8,
})
domain_concept = mint_domain_self_worth(envier.inner, envier._resident_can, "tabletop")
ctx = mint_peer_comparison_context(envier.inner, domain_concept)
for _ in range(3):
    record_peer_observation(envier.inner, ctx, peer_did_well=True)
relative_self_worth = read_relative_self_worth(envier.inner, domain_concept)
deservingness_concept = mint_domain_deservingness_belief(envier.inner, envier._resident_can, "tabletop")
deservingness_value = envier.s.node(deservingness_concept)["attrs"]["external_field"]
envy_read = read_envy(relative_self_worth, deservingness_value)
print("Envier: seeded negative deservingness_prior, then 3 observations of "
      "Landlord (an advantaged peer) doing well recorded.")

print()
print("=" * 70)
print("PREDICTED vs ACTUAL -- belief state")
print("=" * 70)

resentful_state = dump_social_state(resentful, "Landlord")
print("\nResentful's held state about Landlord:")
for k, v in resentful_state.items():
    print("  %s = %s" % (k, v))
print("  consequence_route (from the crystallizing call) = %r" %
      (resentful_crystallize_result or {}).get("consequence_route"))
print("PREDICTED: crystallized=True, consequence_route='removal', "
      "removal_desire_for > 0")

grateful_state = dump_social_state(grateful, "Landlord")
print("\nGrateful's held state about Landlord:")
for k, v in grateful_state.items():
    print("  %s = %s" % (k, v))
print("  admiration_consequence_route (from the crystallizing call) = %r" %
      (grateful_crystallize_result or {}).get("admiration_consequence_route"))
print("PREDICTED: crystallized=True, consequence_route='admiration', "
      "admiration_for > 0, gratitude_debt > 0")

print("\nEnvier: relative_self_worth=%.4f deservingness=%.4f -> envy=%s" % (
    relative_self_worth, deservingness_value, envy_read))
print("PREDICTED: envy='malicious'")

print()
print("=" * 70)
print("PREDICTED vs ACTUAL -- decide_speech toward Landlord, SPONTANEOUS "
      "(no pending greeting/question -- adjacency norm term silent, only "
      "disposition/affect drives the choice)")
print("=" * 70)
print("PREDICTED (post-fix): kind AND rendered text now diverge by disposition "
      "-- Resentful should route hostile (barb/complaint), Grateful warm "
      "(thanks/greeting/smalltalk).")
for resident in (landlord, resentful, grateful, envier):
    other = "Envier" if resident.name == "Landlord" else "Landlord"
    choice = resident.decide_speech(other, goal_pressure=0.3)
    print("  %-10s -> toward %-10s kind=%-10s act=%-10s spoken=%s text=%r" % (
        resident.name, other, choice["kind"], choice.get("act"),
        choice["spoken"], choice.get("text")))

print()
print("=" * 70)
print("CONTROL -- decide_speech WITH a pending greeting FPP (adjacency "
      "obligation should dominate regardless of disposition, per Sacks-"
      "Schegloff-Jefferson -- a greeting obligates a return greeting)")
print("=" * 70)
for resident in (landlord, resentful, grateful, envier):
    other = "Envier" if resident.name == "Landlord" else "Landlord"
    choice = resident.decide_speech(other, obligation=True, fpp_is_greeting=True,
                                    goal_pressure=1.0)
    print("  %-10s -> toward %-10s kind=%-10s act=%-10s spoken=%s text=%r" % (
        resident.name, other, choice["kind"], choice.get("act"),
        choice["spoken"], choice.get("text")))

print()
print("=" * 70)
print("RUNG 3 -- bucket-familiarity fix: Landlord<->Envier (genuinely neutral, "
      "no social_dispositions either way) with shared_bucket_count=0 vs 3 "
      "(simulating them being drawn from the same cast, sharing role/class/group)")
print("=" * 70)
print("PREDICTED: shared_bucket_count=0 reproduces rung 2's hostile-by-default "
      "finding unchanged; shared_bucket_count=3 gives real warmth "
      "(affect_affection>0) and may flip or narrow the argmax margin.")
for count in (0, 3):
    bond = landlord._speech_bond("Envier", shared_bucket_count=count)
    warmth = landlord.s.node(bond)["attrs"]["affect_affection"]
    choice = landlord.decide_speech("Envier", shared_bucket_count=count, arousal=0.4)
    print("  shared_bucket_count=%d -> affect_affection=%.4f kind=%-10s act=%-10s text=%r" % (
        count, warmth, choice["kind"], choice.get("act"), choice.get("text")))

print()
print("=" * 70)
print("ISOLATION CHECK -- Landlord's own graph is unaffected by others' incidents")
print("=" * 70)
landlord_own_concepts = [resident.s.node(c)["attrs"]["name"]
                         for resident in [landlord]
                         for c in resident.s.nodes("Concept")
                         if resident.s.node(c)["attrs"].get("name", "").endswith(":Resentful")
                         or resident.s.node(c)["attrs"].get("name", "").endswith(":Grateful")]
print("Concepts on Landlord's OWN substrate naming Resentful/Grateful as a target: %s"
      % (landlord_own_concepts or "NONE (expected -- each resident's incidents live only "
         "on their own substrate)"))
