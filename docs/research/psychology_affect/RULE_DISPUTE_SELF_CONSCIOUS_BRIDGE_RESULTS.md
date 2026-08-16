# Rule-dispute → self-conscious-emotion bridge — RESULTS

Registered design: `RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_PREREG.md`. Built:
`seeds/rule_dispute_self_conscious_bridge.json` (via
`scripts/_build_rule_dispute_self_conscious_bridge_seed.py`), demonstrated
by `scripts/rule_dispute_self_conscious_bridge_demo.py`, regressed by
`tests/test_rule_dispute_self_conscious_bridge.py` (12/12 green).

## 1. What this is

User: *"wire it live off the rule-dispute escalation outcome."* A third,
strictly additive seed bridges a decided `RuleDisputeSignal`
(`seeds/rule_dispute_escalation.json`) to a `SelfConsciousContext`
(`seeds/self_conscious_emotions.json`) for the claim-holder who was wrong.
Neither prior seed is edited.

**The mapping** (Tangney & Dearing 2002): an `escalate` verdict IS a
hostile/confrontational correction, which reads as global-self attribution
→ `shame`; a `defuse` verdict IS a calm one, which reads as specific-act
attribution → `guilt`. `standard_met=0.0` unconditionally — a dispute
existing at all means the claim-holder was wrong about the rule. Witnesses
carry over from the dispute's own bystander count, with `judgment` keyed to
the SAME outcome mapping (an escalated dispute reads to onlookers as a
clear violation; a defused one does not).

## 2. Predictions — all 6 registered, all 6 held

```
END-TO-END: the SAME two scenarios rule_dispute_escalation_demo.py used
near-strangers, confident contradiction, whole table watching  dispute=escalate  locus=global_self   witnesses=3 -> shame
close friends, ambiguous issue, private aside                  dispute=defuse    locus=specific_act  witnesses=0 -> guilt

NEVER EMBARRASSMENT -- 105-combination sweep (7 bands x 5 severities x 3 witness counts)
emotions produced across the sweep: ['guilt', 'shame']
embarrassment ever produced: False
```

1. **Escalated dispute → shame** — `PASS`.
2. **Defused dispute → guilt**, not shame — `PASS`.
3. **Never embarrassment** — swept the full registered parameter grid from
   both prior rungs' own test ranges (`band_code` −1..5, `issue_severity`
   0.1..0.9, witness count 0/1/3): every outcome is `shame` or `guilt`,
   never `embarrassment` or `none` — `PASS`, confirming the registered scope
   boundary (a rules dispute is an attributable epistemic error, never a
   circumstantial mishap) holds structurally, not just in the two headline
   examples.
4. **Witness count carried over exactly** — tested 0/1/2/3/5 witnesses,
   each producing exactly that many `WitnessBelief` nodes — `PASS`.
5. **Idempotent bridging** — re-running `run_rules()` after the fixpoint
   does not double-mint a `SelfConsciousContext` or duplicate
   `WitnessBelief` nodes — `PASS`.
6. **End to end on the real demo scenarios**, not synthetic
   `SelfConsciousContext` inputs — `PASS`.

No null. Every registered prediction held on the first run.

## 3. Honesty notes

**Does establish**: the two independently-built, independently-tested
rungs compose cleanly through a strictly additive third seed — neither had
to be edited, and the composition produces the theoretically-expected
emotion family member (never the wrong one, never a degenerate `none`)
across a genuine sweep, not two cherry-picked points.

**Does NOT establish**: that Tangney & Dearing's harsh-vs-calm-correction
finding, borrowed here as the outcome→attribution-locus mapping, is the
UNIQUE correct mapping — it is a documented, literature-motivated but
un-fitted design choice (same honesty class as every prior rung's
constants). This bridge structurally cannot produce `embarrassment`
(Prediction 3) — a genuine, separate trigger for circumstance-attributed
episodes remains unbuilt. Nothing feeds the resulting emotion back into
`band_code`/relationship state (no consequence mechanic) — named in both
prior RESULTS docs, still unbuilt.

## 4. Files

- `docs/research/psychology_affect/RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_PREREG.md`
- `docs/research/psychology_affect/RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_RESULTS.md` (this file)
- `scripts/_build_rule_dispute_self_conscious_bridge_seed.py`
- `seeds/rule_dispute_self_conscious_bridge.json`
- `scripts/rule_dispute_self_conscious_bridge_demo.py`
- `tests/test_rule_dispute_self_conscious_bridge.py` (12/12)
