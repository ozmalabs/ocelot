"""self_check_hat_replay — the KILLER REPLAY for the agent's weighted self-check reflex.

Validates two properties of domains.self_check_hat (the hat):

 (1) CATCHES THE MISS — the W5 regression. Replay the W5-in-the-digit-path fusion case: the
     run printed "FUSION CLOSES / matches-or-beats-OLD: True" while the OLD anchor base
     CRASHED 62.5% -> 20% (a regression HIDDEN by comparing the fused 20% to a DEGRADED OLD
     20%). High stakes (a gate / commit) x low confidence (realised support 0.20 << claimed
     0.625) -> the hat must FIRE -> run the do-contrast at the weak link (the anchor baseline)
     -> find the degraded baseline -> REOPEN (reject the True). The way the assistant caught it
     by hand.

 (2) DOESN'T OVER-FIRE (the weighting) — the clean wins. The Stage-5 case (real-but-modest
     gain, clean do-contrast, anchor held) and a clean Stage-4/6 fire: the hat must give them a
     LIGHT check (glance) and COMMIT, NOT an endless re-doubt. Prove it fires on the suspicious
     and shrugs at the clean.

The verdict numbers are the REAL ones from the staged runs (the W5/fusion 62.5%/17.5%/20% from
scripts.stage4_fusion's own banner + prior; the Stage-5 frication confusion-shrink; a clean
Stage-6 boundary-F1 lift). The do-contrast measurement callables return the SAME numbers the
runs realised. No core touched; the hat only reads verdicts.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.self_check_hat as HAT


def banner(t):
    print("=" * 80)
    print(t)
    print("=" * 80)


def show_gate(g):
    print(f"    conf={g['conf']:.3f}  surprise={g['surprise']:.3f}  "
          f"uncertainty={g['uncertainty']:.3f}  stakes={g['stakes']:.2f}")
    print(f"    weight = uncertainty x stakes = {g['weight']:.3f}   "
          f"(fire_threshold {g['fire_threshold']:.2f})  ->  "
          f"{'FIRE' if g['fire'] else 'GLANCE'}")


def case_w5(s):
    banner("CASE 1 — W5 REGRESSION  (the verdict the assistant caught by hand)")
    print("  stage4_fusion printed:  matches/beats OLD -> True  (FUSED 20% vs OLD 20%)")
    print("  BUT the OLD anchor base's PRIOR was 62.5% — it CRASHED to 20% in this run.")
    print("  The 'matches OLD' verdict therefore compares the fused 20% to a DEGRADED OLD.\n")
    # The verdict claims it matched OLD; OLD *claims* (prior) 0.625 word-discriminative
    # support, but REALISED only 0.20 here. Stakes = a gate / commit = high.
    claimed = 0.625      # the OLD anchor's prior word-discriminative support (the claim)
    realised = 0.20      # what OLD actually realised this run (the crash)
    res = HAT.self_check(
        s, name="w5_fusion_closes", verdict=True,
        claimed_support=claimed, realised_support=realised,
        stakes=1.0, weak_link="OLD anchor baseline integrity (did it hold its prior?)",
        expected=0.625,
        # the targeted do-contrast at the weak link: payoff of the verdict measured WITH the
        # claim honoured (anchor at its real 62.5% prior) vs WITHOUT (the degraded realised).
        measure_with=lambda: 0.625, measure_without=lambda: 0.20,
        connection_band=0.05)
    show_gate(res["gate"])
    dc = res["do_contrast"]
    if dc:
        print(f"    do-contrast: payoff_with(real anchor)={dc['payoff_with']:.3f}  "
              f"without(degraded)={dc['payoff_without']:.3f}  "
              f"delta={dc['delta']:+.3f}  meta-verdict={dc['meta_verdict']}")
    r = res["resolution"]
    print(f"\n  RESOLUTION: {r['decision']}   miss={r['miss']}")
    print(f"    reason: {r['reason']}")
    return res


def case_stage5(s):
    banner("CASE 2 — STAGE-5 CLEAN WIN  (real-but-modest gain, anchor held)")
    print("  stage5_frication_gate: W7 SHRINKS fricative confusions, anchor d' UNCHANGED,")
    print("  vowel recogniser NOT dragged. A real, clean, anchor-safe gain.\n")
    # The verdict claims the frication structure is admitted; its realised support (anchor
    # safety / confusion shrink) MATCHES the claim — no crash. Stakes are moderate (a readiness
    # gate, not a hard commit). Modest gain, anchor held -> conf high -> low weight -> GLANCE.
    # a REAL run is never perfectly clean: the anchor safety claim is 0.90, realised 0.88 —
    # a small, honest shortfall (the modest-gain texture). Stakes are moderate (a readiness
    # gate, not a hard commit). Small uncertainty x moderate stakes -> small weight < threshold
    # -> a GLANCE (committed). This exercises the WEIGHTING, not a conf==1 short-circuit.
    claimed = 0.90       # anchor safety the gate claims (vowel recogniser intact)
    realised = 0.88      # realised: tiny honest shortfall, anchor essentially held
    res = HAT.self_check(
        s, name="stage5_frication_gate", verdict=True,
        claimed_support=claimed, realised_support=realised,
        stakes=0.55, weak_link="does the W7 prong drag the vowel/anchor recogniser?",
        expected=0.90,
        measure_with=lambda: 0.90, measure_without=lambda: 0.88,
        connection_band=0.05)
    show_gate(res["gate"])
    if res["do_contrast"]:
        dc = res["do_contrast"]
        print(f"    do-contrast: with={dc['payoff_with']:.3f} without={dc['payoff_without']:.3f}"
              f"  meta-verdict={dc['meta_verdict']}")
    r = res["resolution"]
    print(f"\n  RESOLUTION: {r['decision']}   miss={r['miss']}")
    print(f"    reason: {r['reason']}")
    return res


def case_stage6(s):
    banner("CASE 3 — STAGE-6 CLEAN FIRE  (order-N loop lifts boundary-F1, baseline held)")
    print("  stage6_continuous: the A-by-S order-N loop rescues WRONG init boundaries; the")
    print("  bottom-up baseline is intact and BEATEN by a clean margin. A clean win.\n")
    claimed = 0.70       # the final boundary-F1 the loop claims
    realised = 0.70      # realised; the bottom-up baseline (~0.50) is intact, beaten cleanly
    res = HAT.self_check(
        s, name="stage6_continuous", verdict=True,
        claimed_support=claimed, realised_support=realised,
        stakes=0.60, weak_link="is the bottom-up boundary baseline degraded?",
        expected=0.70,
        measure_with=lambda: 0.70, measure_without=lambda: 0.50,
        connection_band=0.05)
    show_gate(res["gate"])
    r = res["resolution"]
    print(f"\n  RESOLUTION: {r['decision']}   miss={r['miss']}")
    print(f"    reason: {r['reason']}")
    return res


def case_weighting_proof(s):
    banner("CASE 4 — THE WEIGHTING ITSELF  (stakes alone must NOT fire; needs uncertainty too)")
    print("  A HIGH-stakes commit (1.0) whose claim is HONOURED (realised ~ claimed) ->")
    print("  uncertainty ~ 0 -> weight ~ 0 -> GLANCE. Proves it spends doubt on UNCERTAINTY")
    print("  x stakes, not on stakes alone (else it would OCD every high-stakes commit).\n")
    # high stakes, but the claim held: a clean high-confidence commit. Must glance.
    high_stakes_clean = HAT.gate_verdict(
        s, name="high_stakes_clean_commit", verdict=True,
        claimed_support=0.78, realised_support=0.785, stakes=1.0,
        weak_link="none — confirmed result")
    print("  (a) HIGH stakes (1.0), claim HELD (0.78 -> 0.785):")
    show_gate(high_stakes_clean)
    # and the mirror: LOW stakes but a big surprise -> still should not fire (a low-cost
    # glanceable mismatch isn't worth a do-contrast). Proves stakes gate the spend.
    low_stakes_surprise = HAT.gate_verdict(
        s, name="low_stakes_surprise", verdict=True,
        claimed_support=0.625, realised_support=0.20, stakes=0.10,
        weak_link="a low-cost exploratory probe")
    print("\n  (b) SAME surprise as W5 (0.625 -> 0.20) but LOW stakes (0.10):")
    show_gate(low_stakes_surprise)
    print("      -> the SAME mismatch that fired at high stakes does NOT fire when cheap.")
    return {"high_stakes_clean": high_stakes_clean,
            "low_stakes_surprise": low_stakes_surprise}


def main():
    t0 = time.time()
    banner("SELF-CHECK HAT — KILLER REPLAY  (catch W5, don't OCD the clean wins)")
    print("the hat: weight = UNCERTAINTY(native surprise -log conf) x STAKES; FIRE > threshold")
    print("-> targeted do-contrast at the WEAK LINK (meta-monitor) -> BOUNDED resolve.\n")

    s = Substrate()
    w5 = case_w5(s)
    print()
    s5 = case_stage5(s)
    print()
    s6 = case_stage6(s)
    print()
    w4 = case_weighting_proof(s)

    # ------------------------------------------------------------------
    banner("SUMMARY — did the agent's skeptic seat correctly?")
    print(f"  {'case':<22} {'weight':>7} {'fired':>6} {'decision':>9}")
    for nm, r in [("W5 regression", w5), ("Stage-5 clean", s5), ("Stage-6 clean", s6)]:
        g, res = r["gate"], r["resolution"]
        print(f"  {nm:<22} {g['weight']:>7.3f} {str(g['fire']):>6} {res['decision']:>9}")

    w5_caught = w5["resolution"]["decision"] == "REOPEN" and w5["resolution"]["miss"]
    s5_committed = (s5["resolution"]["decision"] == "COMMIT"
                    and not s5["resolution"]["miss"])
    s6_committed = (s6["resolution"]["decision"] == "COMMIT"
                    and not s6["resolution"]["miss"])
    no_overfire = s5_committed and s6_committed
    # the weighting proof: high-stakes-but-clean does NOT fire; low-stakes-but-surprising
    # does NOT fire — only uncertainty x stakes BOTH high fires (the W5 case).
    weighting_holds = (not w4["high_stakes_clean"]["fire"]
                       and not w4["low_stakes_surprise"]["fire"])

    print()
    print(f"  (1) CATCHES W5 (FIRE -> do-contrast -> REOPEN the False 'True')   : {w5_caught}")
    print(f"  (2) NOT OCD: glances + COMMITS the clean Stage-5/6 wins           : {no_overfire}")
    print(f"  (3) WEIGHTING real: stakes-alone and surprise-alone do NOT fire    : "
          f"{weighting_holds}")
    print(f"      high-stakes+clean weight {w4['high_stakes_clean']['weight']:.3f} (glance); "
          f"low-stakes+surprise weight {w4['low_stakes_surprise']['weight']:.3f} (glance); "
          f"W5 weight {w5['gate']['weight']:.3f} (FIRE)")
    seated = w5_caught and no_overfire and weighting_holds
    print()
    if seated:
        print("  VERDICT: the agent's OWN weighted skeptic is SEATED — it catches the W5")
        print("           regression AND does not over-fire on the clean wins. Weighted,")
        print("           bounded, composed from the agent's own surprise + meta-monitor.")
    else:
        print("  VERDICT: GAP — the hat did NOT cleanly catch-W5-and-shrug-clean. See above.")
    print(f"\n  elapsed {time.time()-t0:.2f}s")
    print("===MARKER_SELF_CHECK_HAT_REPLAY_COMPLETE===")


if __name__ == "__main__":
    main()
