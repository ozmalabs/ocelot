# Attribution locus as a residual too — PREREG

**Task**: user, immediately after the severity-as-residual fix: *"wire
attribution_locus as a residual too."* `rule_dispute_self_conscious_bridge
.json`'s `attribution_locus` was a hand-picked lookup keyed on the dispute's
escalate/defuse outcome (Tangney & Dearing's correction-style theory) — a
real mechanism, but still a CATEGORY chosen from a flag, not computed from
a genuine comparison. This rung replaces it with the residual between the
INCIDENT and the agent's own HELD SELF-PATTERN, mirroring `issue_severity`'s
own fix exactly. Named as follow-on in `SELF_CONSCIOUS_EMOTIONS_RESULTS.md`
§5 item 2: *"a repeated failure trending toward global_self, a first-time
one toward specific_act."*

**Unlike the two prior rungs this session, this document edits
`rule_dispute_self_conscious_bridge.json` directly** rather than adding a
fourth additive layer — that seed is this session's OWN bridge/glue layer
(not a foundational, independently-published rung like
`rule_dispute_escalation.json`/`self_conscious_emotions.json`, both of
which remain untouched), and is meant to be refined in place as its own
mapping is corrected, exactly as `rule_dispute_escalation.json` itself was
refined in place for its own Rung 2 (witnesses) within this same arc.

## 1. Theoretical grounding

- **Weiner (1985), "An Attributional Theory of Achievement Motivation and
  Emotion"**: attributions vary on STABILITY (stable/unstable) as well as
  locus — a stable cause implies the outcome fits a persistent pattern; an
  unstable one implies a one-off exception. Global-self (Lewis) IS the
  stable reading; specific-act IS the unstable one.
- **Abramson, Seligman & Teasdale (1978), "Learned Helplessness in Humans:
  Critique and Reformulation"**: the depressive attributional style
  attributes NEGATIVE outcomes to stable, global, internal causes — a
  failure that CONFIRMS an already-negative self-pattern is read globally
  ("I'm just bad at this"), not as an isolated act.
- **Miller & Ross (1975), "Self-Serving Biases in the Attribution of
  Causality: Fact or Fiction?"**: the mirror-image finding for a POSITIVE
  self-pattern — people with a positive self-view attribute failures AWAY
  from the global self (specific/external), protecting the pattern.
- **Net effect, both citations converging on the SAME structural claim**:
  attribution locus is not a free choice per incident — it is governed by
  whether the incident's own outcome CONFIRMS or CONTRADICTS the agent's
  existing self-pattern. A confirming incident reads as global (stable,
  pattern-consistent); a contradicting one reads as specific (unstable,
  an exception). **This is a residual, computed between the incident's own
  implied signal and the held pattern — exactly the same SHAPE as
  `issue_severity := 1-StructSim(claim, truth)`, applied to a different
  pair of held quantities.**
- **Absence of any held pattern → circumstance.** With no track record at
  all (first encounter), there is nothing to confirm or contradict — the
  only honest attribution is to circumstance, not to a pattern that does
  not yet exist. This recovers Miller (1996)'s embarrassment mode for
  exactly the case where it belongs: a first-time incident, no established
  reputation to draw on.

## 2. Design

`SelfPattern{held_self_worth}` (0 or 1 per `BeliefDisagreement`, optional
`bd -has_self_pattern-> SelfPattern` edge) — a scalar in `[-1, 1]`,
mirroring CAN's own `self_worth` Concept range and Bowlby-IWM-prior
character (`worlds/bigville_can_beliefs.py`), supplied as data (the VALUE
of a held self-pattern is external context, exactly as `band_code` always
has been — what changes here is that the OUTPUT category is now computed,
not the input).

```
this_incident_signal = standard_met ? +1.0 : -1.0

no SelfPattern edge                              -> circumstance
SelfPattern present, signs AGREE (confirms)      -> global_self
SelfPattern present, signs DISAGREE (contradicts) -> specific_act
```

Sign agreement is tested via `Gt(Times(held_self_worth,
this_incident_signal), 0.0)` — existing Terms, zero new Rust. `Count`/
`Neighbours`/`PickUnique` (the last already used defensively elsewhere in
this codebase, panicking on ambiguity rather than silently picking one of
several — VISION_PROTOCOL §1.1's own precedent) handle the optional-edge
read.

**`witness_judgment` (for carried-over `WitnessBelief` nodes) is UNCHANGED**
— still keyed to the dispute's escalate/defuse outcome. That is a genuinely
different, correctly-external signal (what OTHERS perceive), not the
agent's own attribution — conflating the two would be the same error the
severity fix corrected in the other direction.

## 3. Predictions

1. **A failure confirming an already-negative pattern → shame.**
   `held_self_worth=-0.6` (a somewhat negative self-view), standard
   violated → signs agree (both negative) → `global_self` → `shame`.
2. **The identical failure, but the agent's pattern is POSITIVE → guilt,
   not shame.** `held_self_worth=+0.6`, same violation → signs disagree →
   `specific_act` → `guilt`. Same incident, opposite emotion, purely from
   the agent's own track record — the discriminating claim.
3. **A first-time incident (no SelfPattern at all) → circumstance**, and,
   if witnessed, `embarrassment` becomes reachable again — **a direct,
   registered RETRACTION of `RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_RESULTS.md`
   §2 prediction 3's "never embarrassment"** finding, which was an artifact
   of the cruder escalate/defuse-only mapping, not a structural property of
   the appraisal mechanism itself.
4. **Success confirming a positive pattern → hubristic pride; success
   contradicting a negative pattern → authentic pride.** The same
   sign-agreement mechanism applies on the `standard_met=True` side, not
   only to failures (Tracy & Robins 2007's own bifurcation, now residual-
   driven instead of a bare data flag).
5. **`witness_judgment` is unaffected** — the escalate/defuse-keyed
   mapping for carried-over witnesses is byte-unchanged; only
   `attribution_locus`'s source changes.

## 4. Scope boundaries

- `held_self_worth` is supplied data — wiring it to a LIVE CAN belief
  network (`worlds/bigville_can_beliefs.py`'s real `self_worth` Concept,
  updated over many real ticks) is a separate, larger, cross-repo
  integration, named but not attempted here (mirrors `resolution_bins`'s
  own staged rollout earlier this session: synthetic input now, live
  wiring named as explicit follow-on).
- Does not model the finer imposter-syndrome cell (an unexpected success
  that contradicts a NEGATIVE self-pattern attributed to luck/circumstance
  rather than a specific act, Clance & Imes 1978) — the simpler two-
  dimensional Weiner/Abramson-Seligman-Teasdale split is what's built;
  the imposter-syndrome refinement is a real, precise, named follow-on,
  not an oversight.
- `standard_met` stays unconditionally `0.0`/data as before — this rung is
  scoped to `attribution_locus` only, per the user's own instruction.
