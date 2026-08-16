"""Live demo of SELF_CONSCIOUS_CONSEQUENCE_PREREG.md -- prints the 5
registered predictions. Output pasted verbatim into the paired RESULTS
doc.
"""
import substrate_rs as sr

from domains.can_self_worth_bridge import (
    ensure_can_seed, find_or_build_resident_can, mint_domain_self_worth,
    record_self_conscious_consequence,
)
from domains.rule_dispute_full_pipeline import run_rule_dispute

CONFIDENT = {"name": "Confident", "index": 0, "params": {
    "resolution_bins": 8, "arousal": 0.2,
    "prior_world_safe": 0.6, "prior_self_worth": 0.9,
    "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
    "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
    "mood_bias": 0.3,
}}

BOB = dict(CONFIDENT, name="Bob")


def fresh():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    return inner


print("=== Predictions 1/2: guilt -> reparative only, shame -> withdrawal only ===")
inner = fresh()
resident_can = find_or_build_resident_can(inner, CONFIDENT)
mint_domain_self_worth(inner, resident_can, "chess")
r_guilt = record_self_conscious_consequence(inner, resident_can, "chess", emotion="guilt")
print("guilt:", r_guilt)
r_shame = record_self_conscious_consequence(inner, resident_can, "chess", emotion="shame")
print("shame:", r_shame)

print()
print("=== Prediction 3: every other classification moves neither ===")
for emotion in ["hubristic_pride", "authentic_pride", "embarrassment", "none"]:
    inner2 = fresh()
    resident_can2 = find_or_build_resident_can(inner2, CONFIDENT)
    mint_domain_self_worth(inner2, resident_can2, "chess")
    r = record_self_conscious_consequence(inner2, resident_can2, "chess", emotion=emotion)
    print("%s: %s" % (emotion, r))

print()
print("=== Prediction 4: repeated guilt accumulates ===")
inner3 = fresh()
resident_can3 = find_or_build_resident_can(inner3, CONFIDENT)
mint_domain_self_worth(inner3, resident_can3, "chess")
for i in range(3):
    r = record_self_conscious_consequence(inner3, resident_can3, "chess", emotion="guilt")
    print("guilt %d: reparative_desire_state=%.4f" % (i, r["reparative_desire_state"]))

print()
print("=== Prediction 5: domain isolation ===")
inner4 = fresh()
resident_can4 = find_or_build_resident_can(inner4, CONFIDENT)
mint_domain_self_worth(inner4, resident_can4, "chess")
mint_domain_self_worth(inner4, resident_can4, "monopoly")
record_self_conscious_consequence(inner4, resident_can4, "chess", emotion="guilt")
record_self_conscious_consequence(inner4, resident_can4, "chess", emotion="guilt")
r_monopoly = record_self_conscious_consequence(inner4, resident_can4, "monopoly", emotion="guilt")
print("monopoly, unaffected by chess's 2 prior guilts:", r_monopoly)

print()
print("=== Integration: the real guilt -> shame flip scenario ===")
inner5 = sr.Substrate()._inner
for i in range(5):
    r = run_rule_dispute(
        inner5, claimant=BOB,
        claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])
    print("dispute %d: emotion=%s reparative=%.4f withdrawal=%.4f" % (
        i, r["emotion"], r["reparative_desire_state"], r["withdrawal_desire_state"]))
