# Wire in the whole thing — RESULTS

Registered design: `WIRE_IN_PREREG.md`. Built: `dispute_severity_from_
beliefs.json` v1.1.0 (one additive carry-over rule), `domains/rule_
dispute_full_pipeline.py`, demonstrated by `scripts/rule_dispute_full_
pipeline_demo.py`, regressed by `tests/test_rule_dispute_full_pipeline.py`
(7/7 green).

## 1. What this answers

User: *"now wire in the whole thing."* Six independently-built, individually
-tested rungs (severity-as-residual, self-conscious emotions, the dispute
→self-conscious bridge, attribution-as-residual, real CAN self_worth,
persistence, domain-scoped projection + plasticity) are now ONE real,
callable entry point: `run_rule_dispute(inner, claimant=..., claim_pred=...,
truth_pred=..., domain=..., ...)`. One call, and the engine decides
severity, outcome, attribution, and emotion, and the claimant's own
persistent, domain-scoped CAN belief is updated to reflect it.

## 2. The one gap, closed

`dispute_severity_from_beliefs.json` mints its own `DisputeContext`; the
self-conscious bridge needs a `SelfPattern` attached to it. The severity
seed only ever carried witnesses over — never a self-pattern — because
every demo before this rung hand-built the `DisputeContext` directly and
attached the pattern itself. Fixed with a third, additive rule
(`carry_over_belief_disagreement_self_pattern`), mirroring the witness
carry-over's exact shape. `rule_dispute_escalation.json`,
`self_conscious_emotions.json`, and `rule_dispute_self_conscious_bridge
.json` are all confirmed byte-unchanged (git-status-gated test).

## 3. Predictions — all 4 registered, all 4 held, plus one genuine emergent
   finding not predicted in advance

```
ONE CALL, THE WHOLE CHAIN
issue_severity=0.333  dispute_outcome=escalate  attribution_locus=specific_act
emotion=guilt  self_worth: 1 -> 0

REPEATED REAL DISPUTES, SAME DOMAIN
dispute 2: self_worth 0 -> 0    locus=specific_act  emotion=guilt
dispute 3: self_worth 0 -> 0    locus=specific_act  emotion=guilt
dispute 4: self_worth 0 -> -1   locus=specific_act  emotion=guilt
dispute 5: self_worth -1 -> -1  locus=global_self   emotion=shame

A DIFFERENT DOMAIN, SAME RESIDENT
chess self_worth (untouched by monopoly disputes): 1

IDENTICAL BELIEF
{'dispute_minted': False, 'self_worth_before': -1, 'self_worth_after': -1}
```

1. **End to end, one call** — `PASS`. Every stage of the six-rung arc
   fires from a single function call over raw belief predicates.
2. **Persistence across repeated REAL disputes** — `PASS`. `self_worth`
   drifts `1 → 0 → 0 → 0 → -1 → -1` across 5 real, independently-decided
   disputes (not hand-fed synthetic evidence).
3. **A genuinely emergent finding, not registered in advance**: the
   EMOTION itself changes as the pattern solidifies —
   `guilt, guilt, guilt, guilt, shame`. This falls directly out of the
   composition, not a scripted narrative: `attribution_locus` is
   `specific_act` while `self_worth` still CONTRADICTS the failure
   (positive or neutral), and flips to `global_self` the moment
   `self_worth` itself reaches `-1` and a further failure CONFIRMS it —
   the exact Abramson/Seligman/Teasdale depressive-attributional-style
   mechanism the self-conscious-emotions rung built weeks-of-narrative
   earlier, now surfacing as a real behavioral arc from composed,
   independently-built pieces with no new code written to produce it.
4. **Domain isolation holds through the full pipeline** — `PASS`. `chess`
   stays at its projected value after 5 real `monopoly_rules` disputes
   drove that domain to `-1`.
5. **The zero-residual floor holds through the full pipeline** — `PASS`.
   Identical beliefs mint no dispute anywhere in the chain; `self_worth`
   is provably untouched (`before == after`).

No null.

## 4. Honesty notes

**Does establish**: six independently-registered, independently-tested
mechanisms compose cleanly into one real system with almost no new code
(one additive carry-over rule, one orchestration module) — and the
composition itself produces a coherent, theoretically-grounded emotional
arc (repeated small failures read as mistakes; an established pattern of
failure reads as identity) that no single rung was built to produce and
that emerged purely from the pieces fitting together correctly.

**Does NOT establish**: a live trigger from actual bigville gameplay — this
delivers the ONE real ocelot-side entry point; hooking it to a real
`BigvilleOcelotResident` dispute (translating a resident's `HeldRule`/
asserted claim into a `[rel, a0, a1]` predicate from live NL, and reading
real `band_code`/witnesses from bigville's own plumbing) is a separate,
larger, cross-repo integration, named honestly, not attempted here. Nothing
about intensity, mood/arousal integration, or rendering the emotion into
observable behavior — all named in earlier RESULTS docs, still unbuilt.

## 5. Files

- `docs/research/psychology_affect/WIRE_IN_PREREG.md`
- `docs/research/psychology_affect/WIRE_IN_RESULTS.md` (this file)
- `scripts/_build_dispute_severity_from_beliefs_seed.py` (edited, v1.1.0: +1 rule)
- `seeds/dispute_severity_from_beliefs.json` (edited, v1.1.0)
- `tests/test_dispute_severity_from_beliefs.py` (edited: production count)
- `domains/rule_dispute_full_pipeline.py`
- `scripts/rule_dispute_full_pipeline_demo.py`
- `tests/test_rule_dispute_full_pipeline.py` (7/7)
