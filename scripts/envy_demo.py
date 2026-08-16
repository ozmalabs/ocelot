"""Live demo of ENVY_PREREG.md -- prints the 5 registered predictions.
Output pasted verbatim into the paired RESULTS doc.
"""
import substrate_rs as sr

from domains.can_self_worth_bridge import (
    ensure_peer_comparison_seed, find_or_build_resident_can,
    mint_domain_self_worth, mint_peer_comparison_context,
    read_relative_self_worth, record_peer_observation,
)
from domains.envy import (
    mint_domain_deservingness_belief, read_envy, record_deservingness_incident,
)

CONFIDENT = {"name": "Confident", "index": 0, "params": {
    "resolution_bins": 8, "arousal": 0.2,
    "prior_world_safe": 0.6, "prior_self_worth": 0.9,
    "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
    "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
    "mood_bias": 0.3,
}}


def fresh():
    s = sr.Substrate()
    inner = s._inner
    ensure_peer_comparison_seed(inner)
    resident_can = find_or_build_resident_can(inner, CONFIDENT)
    return inner, resident_can


print("=== Prediction 1: no disadvantage means no envy, regardless of deservingness ===")
print("read_envy(1.0, -5.0) = %s" % read_envy(1.0, -5.0))
print("read_envy(0.0, -5.0) = %s" % read_envy(0.0, -5.0))

print()
print("=== Prediction 2: a deserved disadvantage produces benign envy ===")
inner, resident_can = fresh()
domain = mint_domain_self_worth(inner, resident_can, "chess")
peer_ctx = mint_peer_comparison_context(inner, domain)
for _ in range(5):
    record_peer_observation(inner, peer_ctx, peer_did_well=True)
rsw = read_relative_self_worth(inner, domain)
print("relative_self_worth (disadvantaged): %.4f" % rsw)
deserv = mint_domain_deservingness_belief(inner, resident_can, "chess")
d = record_deservingness_incident(inner, deserv, deserved=True)
print("deservingness=%.4f -> envy=%s" % (d, read_envy(rsw, d)))

print()
print("=== Prediction 3: an undeserved disadvantage produces malicious envy ===")
inner2, resident_can2 = fresh()
domain2 = mint_domain_self_worth(inner2, resident_can2, "chess")
peer_ctx2 = mint_peer_comparison_context(inner2, domain2)
for _ in range(5):
    record_peer_observation(inner2, peer_ctx2, peer_did_well=True)
rsw2 = read_relative_self_worth(inner2, domain2)
deserv2 = mint_domain_deservingness_belief(inner2, resident_can2, "chess")
d2 = record_deservingness_incident(inner2, deserv2, deserved=False)
print("relative_self_worth=%.4f deservingness=%.4f -> envy=%s" % (rsw2, d2, read_envy(rsw2, d2)))

print()
print("=== Prediction 4: the deservingness belief ALONE flips the verdict ===")
fixed_rsw = -0.791759469228055
print("fixed relative_self_worth=%.4f" % fixed_rsw)
print("  deservingness=+0.3 -> %s" % read_envy(fixed_rsw, 0.3))
print("  deservingness=-0.3 -> %s" % read_envy(fixed_rsw, -0.3))

print()
print("=== Prediction 5: domain isolation ===")
inner3, resident_can3 = fresh()
chess_deserv = mint_domain_deservingness_belief(inner3, resident_can3, "chess")
for _ in range(3):
    record_deservingness_incident(inner3, chess_deserv, deserved=False)
print("chess deservingness (3x undeserved): %.4f"
      % inner3.node(chess_deserv)["attrs"]["external_field"])
football_deserv = mint_domain_deservingness_belief(inner3, resident_can3, "football")
print("football deservingness (untouched): %.4f"
      % inner3.node(football_deserv)["attrs"]["external_field"])
