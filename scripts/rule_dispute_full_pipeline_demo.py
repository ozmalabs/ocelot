"""Live demonstration harness for domains/rule_dispute_full_pipeline.py --
the ONE real, callable, end-to-end entry point over the whole
severity/dispute/self-conscious/CAN-self-worth arc.

Per docs/research/psychology_affect/WIRE_IN_PREREG.md Sec3.

Run: python3 scripts/rule_dispute_full_pipeline_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runners" / "dsl" / "python"))

import substrate_rs as sr  # noqa: E402
from domains.rule_dispute_full_pipeline import run_rule_dispute  # noqa: E402

BOB = {"name": "Bob", "index": 0, "params": {
    "resolution_bins": 8, "arousal": 0.2,
    "prior_world_safe": 0.6, "prior_self_worth": 0.9,
    "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
    "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
    "mood_bias": 0.3,
}}


def main():
    s = sr.Substrate()
    inner = s._inner

    print("=" * 78)
    print("ONE CALL, THE WHOLE CHAIN: raw beliefs -> severity -> outcome ->")
    print("attribution -> emotion -> persisted self_worth")
    print("=" * 78)
    r = run_rule_dispute(
        inner, claimant=BOB,
        claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])
    for k, v in r.items():
        print("  %-18s %s" % (k, v))

    print()
    print("=" * 78)
    print("REPEATED REAL DISPUTES, SAME DOMAIN: identity genuinely accumulates")
    print("=" * 78)
    for i in range(2, 6):
        r = run_rule_dispute(
            inner, claimant=BOB,
            claim_pred=["pays_pot", "free_parking", True],
            truth_pred=["pays_pot", "free_parking", False],
            domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])
        print("dispute %d: self_worth %s -> %s   locus=%-13s emotion=%s" % (
            i, r["self_worth_before"], r["self_worth_after"],
            r["attribution_locus"], r["emotion"]))
    print("(guilt for the first several -- 'I made a mistake' -- then flips")
    print(" to shame once the pattern is established -- 'I am just bad at")
    print(" this' -- an emergent arc, not scripted)")

    print()
    print("=" * 78)
    print("A DIFFERENT DOMAIN, SAME RESIDENT: untouched by monopoly disputes")
    print("=" * 78)
    chess = run_rule_dispute(
        inner, claimant=BOB,
        claim_pred=["is_a", "queen", "strongest_piece"],
        truth_pred=["is_a", "queen", "strongest_piece"],
        domain="chess", band_code=0, witnesses=[])
    print("chess self_worth (projected from global, never touched by",
          "monopoly disputes):", chess["self_worth_before"])

    print()
    print("=" * 78)
    print("IDENTICAL BELIEF: no dispute minted, self_worth untouched")
    print("=" * 78)
    r = run_rule_dispute(
        inner, claimant=BOB,
        claim_pred=["pays_pot", "free_parking", False],
        truth_pred=["pays_pot", "free_parking", False],
        domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])
    print(r)


if __name__ == "__main__":
    main()
