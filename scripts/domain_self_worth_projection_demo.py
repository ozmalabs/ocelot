"""Live demonstration harness for domains/can_self_worth_bridge.py's
mint_domain_self_worth -- Rotter (1954)'s generalized-vs-specific-
expectancy mechanism.

Per docs/research/psychology_affect/DOMAIN_SELF_WORTH_PROJECTION_PREREG.md
Sec4.

Run: python3 scripts/domain_self_worth_projection_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runners" / "dsl" / "python"))

import substrate_rs as sr  # noqa: E402
from domains.can_self_worth_bridge import (  # noqa: E402
    ensure_can_seed, find_or_build_resident_can, mint_domain_self_worth,
    record_incident_outcome,
)

CONFIDENT = {"name": "Confident", "index": 0, "params": {
    "resolution_bins": 8, "arousal": 0.2,
    "prior_world_safe": 0.6, "prior_self_worth": 0.9,
    "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
    "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
    "mood_bias": 0.3,
}}


def main():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    resident = find_or_build_resident_can(inner, CONFIDENT)

    print("=" * 78)
    print("PREDICTION 1: a brand-new domain projects the current global state")
    print("=" * 78)
    print("global self_worth:", resident["self_worth"])
    speaking = mint_domain_self_worth(inner, resident, "public_speaking")
    print("self_worth:public_speaking (no track record yet):",
          inner.node(speaking)["attrs"]["state"])

    print()
    print("=" * 78)
    print("PREDICTION 2/3: domain-specific evidence decouples it -- and a")
    print("SECOND domain can hold the OPPOSITE belief, simultaneously")
    print("=" * 78)
    for i in range(1, 6):
        st = record_incident_outcome(
            inner, {"self_worth": speaking}, standard_met=False,
            attribution_locus="global_self")
        print("public_speaking after %d failures: %s   (global self_worth still: %s)" % (
            i, st, inner.node(resident["concepts"]["self_worth"])["attrs"]["state"]))

    chess = mint_domain_self_worth(inner, resident, "chess")
    print("self_worth:chess (freshly minted, projects global):",
          inner.node(chess)["attrs"]["state"])
    for i in range(1, 4):
        st = record_incident_outcome(
            inner, {"self_worth": chess}, standard_met=True,
            attribution_locus="specific_act")
        print("chess after %d successes: %s" % (i, st))

    print()
    print("public_speaking:", inner.node(speaking)["attrs"]["state"],
          " chess:", inner.node(chess)["attrs"]["state"],
          " global:", inner.node(resident["concepts"]["self_worth"])["attrs"]["state"])
    print("(low/negative in one domain, unchanged-positive in another, ")
    print(" simultaneously -- the user's own original question, confirmed)")

    print()
    print("=" * 78)
    print("PREDICTION 4: idempotent minting -- a second call reuses the")
    print("drifted domain Concept, does not reset it")
    print("=" * 78)
    speaking_again = mint_domain_self_worth(inner, resident, "public_speaking")
    print("same node:", speaking_again == speaking,
          " state preserved:", inner.node(speaking_again)["attrs"]["state"])

    print()
    print("=" * 78)
    print("PREDICTION 6: belief plasticity is a PERSONALITY TRAIT (Dweck's")
    print("fixed vs growth mindset) -- alpha, not a fixed constant")
    print("=" * 78)
    for label, plasticity in (("Rigid (fixed mindset, alpha=0.05)", 0.05),
                              ("Flexible (growth mindset, alpha=0.5)", 0.5)):
        s2 = sr.Substrate()
        inner2 = s2._inner
        ensure_can_seed(inner2)
        r2 = find_or_build_resident_can(inner2, CONFIDENT)
        domain2 = mint_domain_self_worth(inner2, r2, "public_speaking")
        states = []
        for _ in range(8):
            st = record_incident_outcome(
                inner2, {"self_worth": domain2}, standard_met=False,
                attribution_locus="global_self", alpha=plasticity)
            states.append(st)
        print("%-40s global=1 -> %s" % (label, states))
    print("(the SAME incidents, the SAME starting belief -- the only")
    print(" difference is the personality trait)")


if __name__ == "__main__":
    main()
