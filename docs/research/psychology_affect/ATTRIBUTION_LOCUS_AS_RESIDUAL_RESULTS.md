# Attribution locus as a residual too — RESULTS

Registered design: `ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md`. Built:
`seeds/rule_dispute_self_conscious_bridge.json` v1.1.0 (edited in place —
this is this session's own bridge/glue layer, not a foundational rung;
`rule_dispute_escalation.json` and `self_conscious_emotions.json` remain
git-status-confirmed untouched), demonstrated by
`scripts/rule_dispute_self_conscious_bridge_demo.py`, regressed by
`tests/test_rule_dispute_self_conscious_bridge.py` (15/15 green).

## 1. What this answers

User: *"wire attribution_locus as a residual too."* `attribution_locus`
was a hand-picked lookup from the dispute's escalate/defuse outcome
(Tangney & Dearing 2002) — a real mechanism, but still a category chosen
from a flag. Replaced with the residual between the incident's own implied
signal and the agent's held `SelfPattern` — signs agree (confirms the
pattern) → `global_self`; signs disagree (contradicts it) → `specific_act`;
no pattern at all → `circumstance`. `witness_judgment` (what OTHERS
perceive) stays keyed to escalate/defuse, correctly unchanged — a
genuinely different signal from the agent's own attribution.

## 2. Predictions — all 5 registered, all 5 held

```
ATTRIBUTION AS A RESIDUAL -- the SAME failure, opposite held self-pattern
failure confirms an already-negative self-pattern       locus=global_self   -> shame
SAME failure, but a positive self-pattern (contradicts it) locus=specific_act  -> guilt

NO TRACK RECORD -> CIRCUMSTANCE, EMBARRASSMENT RECOVERED
first-time incident, no track record, private           locus=circumstance  -> none
SAME first-time incident, witnessed                     locus=circumstance  -> embarrassment

witness_judgment is UNCHANGED
near-strangers, confident contradiction, witnessed      dispute=escalate  witness_judgment=violated  emotion=shame
close friends, ambiguous issue, private                 dispute=defuse    witness_judgment=met       emotion=shame
```

1. **Confirming a negative pattern → shame** (Abramson, Seligman & Teasdale
   1978's depressive attributional style: a failure that fits an existing
   negative self-view reads as stable/global). `PASS`.
2. **The IDENTICAL failure, contradicting a positive pattern → guilt, not
   shame** (Miller & Ross 1975's self-serving bias: the same objective
   outcome, opposite attribution, purely from the agent's own track
   record). `PASS` — the discriminating claim, and it holds with the issue
   itself held completely fixed.
3. **No track record → `circumstance`, and embarrassment becomes reachable
   when witnessed.** `PASS`. **This directly RETRACTS
   `RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_RESULTS.md` §2 prediction 3's "never
   embarrassment"** — that finding was correct FOR v1.0.0's mechanism, but
   was an artifact of the cruder escalate/defuse-only mapping, not a
   structural property of self-conscious appraisal itself. A first-time
   incident with no reputation to draw on genuinely IS the paradigm
   embarrassment case (Miller 1996), and the more theoretically correct
   mechanism recovers it automatically.
4. **The full emotion family (shame, guilt, embarrassment) is reachable
   through the bridge** — confirmed by a 7×3×2×3 sweep (`band_code` ×
   severity × witness-count × held-pattern), a strictly LARGER reachable
   set than v1.0.0's `{shame, guilt}`. `PASS`.
5. **`witness_judgment` is unaffected by the source change** — held
   `held_self_worth` fixed while the dispute outcome differs (escalate vs
   defuse): `witness_judgment` correctly differs (`violated` vs `met`)
   while `emotion` stays identical (`shame` in both), because
   `attribution_locus=global_self` in both cases and only the
   `circumstance` cell ever reads `witness_judgment` at all. `PASS` — this
   is the precise, falsifiable confirmation that the two signals are now
   genuinely decoupled, not merely asserted to be.

No null. Every registered prediction held on the first run.

## 3. Honesty notes

**Does establish**: attribution locus is now a genuine structural
comparison — the SAME incident produces different self-conscious emotions
depending on whether it fits or breaks the agent's own pattern, exactly as
two independently-converging real literatures (learned-helplessness
attributional style; self-serving bias) predict — and the correction
recovers a real emotion (embarrassment) the cruder v1.0.0 mechanism
structurally could not reach, which is itself evidence the residual
framing is the more correct mechanism, not just a stylistic improvement.

**Does NOT establish**: `held_self_worth` as a LIVE, ticking quantity — it
remains supplied data (mirrors CAN's own `self_worth` Bowlby-IWM-prior
character, but is not wired to the real CAN belief network,
`worlds/bigville_can_beliefs.py`, which updates over many real ticks — a
separate, larger, named cross-repo integration). The imposter-syndrome
cell (an unexpected success attributed to circumstance rather than a
specific act, when it contradicts a negative self-pattern — Clance & Imes
1978) is not modeled; the current mechanism would read that case as
`specific_act` (authentic pride), a simplification named honestly in the
PREREG, not discovered as a defect here.

## 4. Files

- `docs/research/psychology_affect/ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md`
- `docs/research/psychology_affect/ATTRIBUTION_LOCUS_AS_RESIDUAL_RESULTS.md` (this file)
- `scripts/_build_rule_dispute_self_conscious_bridge_seed.py` (edited, v1.1.0)
- `seeds/rule_dispute_self_conscious_bridge.json` (edited, v1.1.0)
- `scripts/rule_dispute_self_conscious_bridge_demo.py` (edited)
- `tests/test_rule_dispute_self_conscious_bridge.py` (rewritten, 15/15)
