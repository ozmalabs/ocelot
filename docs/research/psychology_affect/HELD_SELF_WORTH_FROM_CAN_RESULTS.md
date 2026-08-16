# held_self_worth from the real CAN self_worth belief — RESULTS

Registered design: `HELD_SELF_WORTH_FROM_CAN_PREREG.md`. Built:
`domains/can_self_worth_bridge.py`, demonstrated by
`scripts/held_self_worth_from_can_demo.py`, regressed by
`tests/test_held_self_worth_from_can.py` (5/5 green). No seed is edited —
confirmed by a git-status-gated test covering all four seeds this arc has
touched.

## 1. What this answers

User: *"wire held_self_worth into the real CAN self_worth belief."*
`held_self_worth` was supplied data (a hand-picked scalar) even after the
attribution-locus rung made it the driver of a genuine residual
comparison. This rung sources it from the actual, live,
`worlds/bigville_can_beliefs.py` + `seeds/can_native_reimplementation.json`
CAN belief network instead — a pure Python world-adapter function
(`can_self_worth_bridge.py`) that builds a resident's real `self_worth`
Concept, relaxes it via the engine's own discrete-asynchronous update rule
under `run_rules()`, and reads the converged `state` back. No graph rule
changes anywhere; this is entirely a data-sourcing wire-up.

## 2. Predictions — both registered, both held

```
REAL CAN self_worth, two residents, the SAME dispute
Confident  prior_self_worth=0.90 -> real CAN self_worth=1  (5 relaxation steps)
Insecure   prior_self_worth=0.10 -> real CAN self_worth=-1 (5 relaxation steps)

THE SAME rule dispute, appraised through each resident's REAL,
independently-relaxed CAN self_worth belief
Confident: near-strangers, confident contradiction, witnessed  locus=specific_act  -> guilt
Insecure: near-strangers, confident contradiction, witnessed   locus=global_self   -> shame
```

1. **Opposite personality priors converge to opposite real CAN states** —
   confirmed empirically BEFORE registering (PREREG Sec1), then locked in
   as a test: `prior_self_worth=0.9` → `identity_field=0.8` → converges to
   `state=+1`; `prior_self_worth=0.1` → `identity_field=-0.8` → converges
   to `state=-1`, both in 5 discrete-async steps — fast, real, not a
   coincidence of the two chosen priors (the sign of `identity_field`
   alone is already a strong pull toward the matching basin).
2. **End to end**: the IDENTICAL dispute (same severity, same band, same
   witnesses), appraised through each resident's own real, independently-
   relaxed CAN belief, produces exactly the theoretically-expected split —
   the confident resident's failure CONTRADICTS their positive `self_worth`
   → `specific_act` → `guilt`; the insecure resident's SAME failure
   CONFIRMS their negative `self_worth` → `global_self` → `shame`. This is
   the same qualitative claim `ATTRIBUTION_LOCUS_AS_RESIDUAL_RESULTS.md`
   already confirmed with hand-picked scalars (`held_self_worth=±0.6`) —
   now confirmed with a real, ticking CAN network supplying the value
   instead, closing the gap that RESULTS doc named as unbuilt.

No null. Both predictions held on the first run.

## 3. Honesty notes

**Does establish**: the full chain — real CAN relaxation → residual
attribution → self-conscious emotion — composes end to end across FOUR
independently-built seeds (`can_native_reimplementation`,
`rule_dispute_escalation`, `self_conscious_emotions`,
`rule_dispute_self_conscious_bridge`) plus one Python world-adapter
function, with zero graph rule edits anywhere in this rung. The CAN
relaxation is fast (5 steps) and decisive (converges to the extreme `±1`
basin, not a wishy-washy intermediate) for the two representative priors
tested.

**Does NOT establish**: that `self_worth` TRACKS a real history of many
interactions over time — this bridge relaxes a STATIC personality-drawn
prior against 4 fixed sibling topics, once, per resident; it does not
persist a resident's CAN network across many real ticks or apply live
evidence (`apply_scenario_evidence`) to it (PREREG Sec4, named follow-on).
Whether a REAL `bigville_cast100.json` resident (rather than the two
representative synthetic draws used here) produces a meaningfully-varied
population of `self_worth` states — not tested, a real, smaller, named
follow-on. What happens for a resident whose network relaxes to the
NEUTRAL `state=0` (a genuinely different, not-yet-empirically-observed
case from either of the two tested residents) — the existing sign-
agreement rule resolves it to `specific_act` by construction (product with
0 is never `>0`), noted as an honest consequence in the PREREG, not
re-tested with a specifically-constructed neutral-converging resident here.

## 4. Files

- `docs/research/psychology_affect/HELD_SELF_WORTH_FROM_CAN_PREREG.md`
- `docs/research/psychology_affect/HELD_SELF_WORTH_FROM_CAN_RESULTS.md` (this file)
- `domains/can_self_worth_bridge.py`
- `scripts/held_self_worth_from_can_demo.py`
- `tests/test_held_self_worth_from_can.py` (5/5)
