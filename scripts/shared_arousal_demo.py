"""Live demo of shared_arousal excitation transfer -- prints the 4
registered predictions (SHARED_AROUSAL_EXCITATION_TRANSFER_PREREG.md
Sec3). Output pasted verbatim into the paired RESULTS doc.
"""
import json

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.shared_arousal import (
    mint_target_arousal, mint_target_concept, record_targeted_incident,
)


def fresh_mt(name):
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    d = json.load(open("seeds/shared_arousal.json"))
    inner.load_seed_manifest(engine_rules_only(d))
    mt = inner.add_node("Microtheory", {"name": name, "temperature": 1.5})
    return inner, mt


print("=== Prediction 1: hostility spikes arousal, amplifies desire update ===")
inner, mt = fresh_mt("mt1")
hostility = mint_target_concept(inner, mt, "regard_for", "Alex")
desire = mint_target_concept(inner, mt, "desire_for", "Alex")
arousal = mint_target_arousal(inner, mt, "Alex")
r1 = record_targeted_incident(inner, hostility, arousal, evidence=-1.0,
                              intensity=0.8, base_alpha=0.3)
print("after hostile incident: arousal_level=%.3f" % r1["arousal_level"])
r2 = record_targeted_incident(inner, desire, arousal, evidence=1.0,
                              intensity=0.1, base_alpha=0.3)
print("desire incident RIGHT AFTER: effective_alpha=%.3f external_field=%.3f"
      % (r2["effective_alpha"], r2["external_field"]))

print()
print("=== control: same desire incident, no prior arousal ===")
inner_c, mt_c = fresh_mt("mt_control")
desire_c = mint_target_concept(inner_c, mt_c, "desire_for", "Alex")
arousal_c = mint_target_arousal(inner_c, mt_c, "Alex")
rc = record_targeted_incident(inner_c, desire_c, arousal_c, evidence=1.0,
                              intensity=0.1, base_alpha=0.3)
print("control: effective_alpha=%.3f external_field=%.3f"
      % (rc["effective_alpha"], rc["external_field"]))

print()
print("=== Prediction 2: symmetry -- desire-driven arousal amplifies a later hostility incident ===")
inner2, mt2 = fresh_mt("mt2")
hostility2 = mint_target_concept(inner2, mt2, "regard_for", "Alex")
desire2 = mint_target_concept(inner2, mt2, "desire_for", "Alex")
arousal2 = mint_target_arousal(inner2, mt2, "Alex")
record_targeted_incident(inner2, desire2, arousal2, evidence=1.0,
                         intensity=0.8, base_alpha=0.3)
r3 = record_targeted_incident(inner2, hostility2, arousal2, evidence=-1.0,
                              intensity=0.1, base_alpha=0.3)
print("hostility incident after a desire spike: effective_alpha=%.3f (vs control base_alpha=0.3)"
      % r3["effective_alpha"])

print()
print("=== Prediction 3: arousal decays without fresh spikes ===")
inner3, mt3 = fresh_mt("mt3")
c3 = mint_target_concept(inner3, mt3, "regard_for", "Alex")
a3 = mint_target_arousal(inner3, mt3, "Alex")
record_targeted_incident(inner3, c3, a3, evidence=-1.0, intensity=0.8, base_alpha=0.3)
level = inner3.node(a3)["attrs"]["level"]
print("tick 0 (post-spike): level=%.4f" % level)
for tick in range(1, 5):
    r = record_targeted_incident(inner3, c3, a3, evidence=-1.0, intensity=0.0, base_alpha=0.3)
    print("tick %d (zero-intensity incident, decay-only): level=%.4f" % (tick, r["arousal_level"]))

print()
print("=== Prediction 4: arousal is per-target, not global ===")
inner4, mt4 = fresh_mt("mt4")
alex_h = mint_target_concept(inner4, mt4, "regard_for", "Alex")
alex_a = mint_target_arousal(inner4, mt4, "Alex")
sam_d = mint_target_concept(inner4, mt4, "desire_for", "Sam")
sam_a = mint_target_arousal(inner4, mt4, "Sam")
record_targeted_incident(inner4, alex_h, alex_a, evidence=-1.0, intensity=0.8, base_alpha=0.3)
r4 = record_targeted_incident(inner4, sam_d, sam_a, evidence=1.0, intensity=0.1, base_alpha=0.3)
print("Sam's desire incident, unaffected by Alex's hostility spike: effective_alpha=%.3f (expect 0.3)"
      % r4["effective_alpha"])
