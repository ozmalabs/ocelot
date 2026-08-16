"""Live demo of RESIDENT_TRUST_PREREG.md -- prints the 4 registered
predictions. Output pasted verbatim into the paired RESULTS doc.
"""
import substrate_rs as sr

from domains.can_self_worth_bridge import ensure_can_seed
from domains.resident_trust import mint_trust_beliefs, read_trust, record_trust_incident


def fresh():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    mt = inner.add_node("Microtheory", {"name": "test_mt", "temperature": 1.5})
    return inner, mt


print("=== Prediction 1: competence alone does not raise trust ===")
inner, mt = fresh()
beliefs = mint_trust_beliefs(inner, mt, "Alex")
record_trust_incident(inner, beliefs, dimension="competence", positive=True)
print("trust after competence-only: %.4f" % read_trust(inner, beliefs))

print()
print("=== Prediction 2: trust rises once BOTH dimensions are positive ===")
record_trust_incident(inner, beliefs, dimension="willingness", positive=True)
print("trust after both positive: %.4f" % read_trust(inner, beliefs))

print()
print("=== Prediction 3: a betrayal caps trust regardless of competence ===")
for _ in range(5):
    record_trust_incident(inner, beliefs, dimension="competence", positive=True)
competence_ef = inner.node(beliefs["competence"])["attrs"]["external_field"]
print("competence now: %.4f, trust: %.4f" % (competence_ef, read_trust(inner, beliefs)))
record_trust_incident(inner, beliefs, dimension="willingness", positive=False)
record_trust_incident(inner, beliefs, dimension="willingness", positive=False)
willingness_ef = inner.node(beliefs["willingness"])["attrs"]["external_field"]
print("after 2 betrayals: willingness=%.4f, competence=%.4f (unchanged), trust=%.4f"
      % (willingness_ef, competence_ef, read_trust(inner, beliefs)))

print()
print("=== Prediction 4: per-target isolation ===")
beliefs_sam = mint_trust_beliefs(inner, mt, "Sam")
print("Sam's trust (unaffected by Alex's history): %.4f" % read_trust(inner, beliefs_sam))
