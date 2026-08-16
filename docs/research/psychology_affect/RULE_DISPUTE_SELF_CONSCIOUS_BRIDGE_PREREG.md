# Rule-dispute → self-conscious-emotion bridge — PREREG

**Task**: user asked to "wire it live off the rule-dispute escalation
outcome" — the follow-on named in
`RULE_DISPUTE_ESCALATION_RESULTS.md` §5 item 1 and
`SELF_CONSCIOUS_EMOTIONS_RESULTS.md` §5 item 1: a decided
`RuleDisputeSignal` (`seeds/rule_dispute_escalation.json`) mechanically mints
a `SelfConsciousContext` (`seeds/self_conscious_emotions.json`) for the
disputant who was wrong, carrying the dispute's own witnesses over.

## 1. Design

Two seeds, two prior rungs, bridged by a THIRD small seed
(`seeds/rule_dispute_self_conscious_bridge.json`, depends on both) rather
than editing either existing rule — neither prior rung's own
well-tested decision logic is touched.

**Who gets appraised**: the disputant whose CLAIM was contradicted by the
rulebook — by construction of `RULE_DISPUTE_ESCALATION_PREREG.md`'s own
scoping (§2: "a resident's `HeldRule`... contradicted by another resident's
ASSERTED CLAIM"), this bridge always appraises the claim-holder, so
`standard_met=0.0` unconditionally — the premise of a rule dispute existing
at all is that someone was wrong about the rule.

**`attribution_locus` from the dispute outcome** (the actual new mapping,
registered before building): Tangney & Dearing (2002, *Shame and Guilt*)
— HOW a correction is delivered shapes whether it is internalized as
global-self (harsh, character-focused, confrontational) or specific-act
(calm, behavior-focused) attribution. An `escalate` verdict IS a hostile,
confrontational correction by construction (`rule_dispute_escalation`'s own
Felson-grounded pressure formula); a `defuse` verdict IS a calm one.

```
outcome == "escalate"  -> attribution_locus = "global_self"  -> shame
outcome == "defuse"    -> attribution_locus = "specific_act" -> guilt
```

**Witnesses carry over, with a derived judgment**: each `WitnessPresence`
already present on the dispute's `DisputeContext` mints a corresponding
`WitnessBelief`. An escalated (public, confrontational) dispute reads to
onlookers as "yes, a clear wrong occurred" (`judgment="violated"`); a
defused one reads as resolved without a clear public verdict
(`judgment="met"`) — same `outcome`-keyed mapping as the attribution locus,
not a second independent judgment call.

**A registered, honest scoping consequence**: this bridge NEVER produces
`attribution_locus="circumstance"`, so it never produces `embarrassment` —
a genuine rules dispute is, by construction, an attributable epistemic
error (you were wrong about a fact), not a circumstantial mishap (tripping,
Miller 1996's paradigm case). Embarrassment stays reachable only through a
different, non-dispute trigger — this is a scope boundary, not a defect.

## 2. Predictions

1. **Escalated dispute → shame.** The Free Parking scenario
   (`RULE_DISPUTE_ESCALATION_RESULTS.md` §2: near-strangers, high severity,
   witnessed, `outcome=escalate`) bridges to `emotion=shame` for the
   claim-holder.
2. **Defused dispute → guilt**, not shame. The close-friends/low-severity/
   private scenario (same doc, `outcome=defuse`) bridges to `emotion=guilt`.
3. **Never embarrassment.** No combination of registered dispute inputs
   produces `attribution_locus=circumstance` — swept across the full
   `(band_code, issue_severity, witness count)` grid from both prior
   rungs' own test suites, `emotion` is always `shame` or `guilt`, never
   `embarrassment` or `none`.
4. **Witness count is carried over exactly** — a dispute with 3 witnesses
   bridges to exactly 3 `WitnessBelief` nodes.
5. **Idempotent bridging.** Running the bridge rules twice on the same
   decided dispute does not double-mint a second `SelfConsciousContext` or
   duplicate `WitnessBelief` nodes (the `bridged_to`/`mirrored_as` dedup
   guards, mirroring `gap_awareness.json`'s own re-fire discipline).
6. **End-to-end, not synthetic**: running the REAL
   `rule_dispute_escalation_demo.py` scenarios through the bridge (not
   hand-built `SelfConsciousContext` inputs) reproduces predictions 1-2.

## 3. Scope boundaries

- Neither `rule_dispute_escalation.json` nor `self_conscious_emotions.json`
  is edited — the bridge is a strictly additive third seed.
- Does not decide WHICH disputant is the claim-holder — that identity is
  assumed given (mirrors both prior rungs treating their own inputs as
  data, not inferred).
- Does not feed the resulting emotion back into anything (no consequence
  mechanic, no relationship/`band_code` decay from a shame verdict) — named
  in both prior RESULTS docs as further, separate follow-on.
