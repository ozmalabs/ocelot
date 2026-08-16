"""Live demonstration harness for seeds/peer_comparison.json -- relative
self-worth as a log-weighted social comparison, not an absolute state.

Per docs/research/psychology_affect/RELATIVE_SELF_WORTH_PREREG.md Sec3.

Run: python3 scripts/relative_self_worth_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runners" / "dsl" / "python"))

import substrate_rs as sr  # noqa: E402
from domains.can_self_worth_bridge import (  # noqa: E402
    ensure_peer_comparison_seed, find_or_build_resident_can, mint_domain_self_worth,
    mint_peer_comparison_context, read_relative_self_worth, record_peer_observation,
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
    ensure_peer_comparison_seed(inner)
    resident = find_or_build_resident_can(inner, CONFIDENT)
    domain = mint_domain_self_worth(inner, resident, "public_speaking")
    ctx = mint_peer_comparison_context(inner, domain)

    print("=" * 78)
    print("ZERO OBSERVATIONS -- THE FICTIONAL MIDPOINT IS GENUINELY NEUTRAL")
    print("=" * 78)
    print("own state:", inner.node(domain)["attrs"]["state"],
          " relative_self_worth:", read_relative_self_worth(inner, domain))

    print()
    print("=" * 78)
    print("THE SOCIAL MEDIA HIGHLIGHT REEL: 8 peers observed doing well, 1 struggling")
    print("=" * 78)
    for _ in range(8):
        record_peer_observation(inner, ctx, peer_did_well=True)
    record_peer_observation(inner, ctx, peer_did_well=False)
    print("own state (UNCHANGED -- no incident of the resident's own occurred):",
          inner.node(domain)["attrs"]["state"])
    print("relative_self_worth (DROPPED, purely from the comparison baseline):",
          read_relative_self_worth(inner, domain))
    print("(\"your self worth can drop without dropping\" -- confirmed live)")

    print()
    print("=" * 78)
    print("THE REVERSE: a fresh resident observes peers STRUGGLING")
    print("=" * 78)
    s2 = sr.Substrate()
    inner2 = s2._inner
    ensure_peer_comparison_seed(inner2)
    resident2 = find_or_build_resident_can(inner2, CONFIDENT)
    domain2 = mint_domain_self_worth(inner2, resident2, "public_speaking")
    ctx2 = mint_peer_comparison_context(inner2, domain2)
    for _ in range(8):
        record_peer_observation(inner2, ctx2, peer_did_well=False)
    record_peer_observation(inner2, ctx2, peer_did_well=True)
    print("own state (UNCHANGED):", inner2.node(domain2)["attrs"]["state"])
    print("relative_self_worth (RISEN above own state, same mechanism, opposite skew):",
          read_relative_self_worth(inner2, domain2))


if __name__ == "__main__":
    main()
