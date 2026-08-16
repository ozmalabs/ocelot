# Wire in the whole thing — PREREG

**Task**: user, after 6 landed rungs (severity-as-residual, self-conscious
emotions, the dispute→self-conscious bridge, attribution-as-residual, real
CAN self_worth, persistence, domain-scoped projection + plasticity):
*"now wire in the whole thing."* Every piece above was independently built
and tested via its own hand-assembled demo/test harness. This document
registers and builds ONE real, callable, end-to-end entry point that
composes all of them, with real persistence, rather than leaving five
separately-demonstrated mechanisms.

## 1. The one real gap, found before building the orchestrator

`dispute_severity_from_beliefs.json` mints `DisputeContext` itself (from a
`BeliefDisagreement`); `rule_dispute_self_conscious_bridge.json` expects a
`SelfPattern` attached to that `DisputeContext` — but the severity seed
only ever carried WITNESSES over to the minted context, never a
`SelfPattern`. A caller starting from raw beliefs (rather than hand-
building a `DisputeContext` directly, as every demo until now did) had
nowhere to attach one. Fixed: `dispute_severity_from_beliefs.json` v1.1.0
adds a THIRD rule, `carry_over_belief_disagreement_self_pattern`,
mirroring the witness carry-over exactly (same dedup idiom, same
mint-and-copy shape) — strictly additive, the other two rules in that seed
are byte-unchanged.

## 2. Design

`domains/rule_dispute_full_pipeline.py::run_rule_dispute` — ONE function,
pure world-adapter sequencing (CLAUDE.md: no new decision anywhere in this
file):

1. `find_or_build_resident_can` — the claimant's real, persistent CAN
   network (reused if this resident has appraised before on this
   substrate).
2. `mint_domain_self_worth` — the claimant's domain-scoped self-worth for
   THIS dispute's domain (e.g. `"monopoly_rules"`), projected from global
   on first use, reused (with whatever drift it already has) thereafter.
3. Build the real `BeliefDisagreement` (claim/truth predicates, band_code,
   audience_gain, witnesses, and a `SelfPattern` snapshotting the
   claimant's CURRENT domain self-worth) and `run_rules()` — the engine
   decides severity, dispute outcome, attribution locus, and emotion,
   entirely via the four already-tested seeds, unchanged.
4. `record_incident_outcome` — feeds the JUST-DECIDED outcome back onto
   the SAME domain Concept `mint_domain_self_worth` returned, using the
   claimant's own `belief_plasticity` (a personality trait, not a
   hard-coded rate).

Returns the full decision trace plus `self_worth_before`/`self_worth_after`
so a caller can observe the persistence effect directly.

## 3. Predictions (confirmed live before finalizing this document, per this
   arc's established practice of verifying before registering)

1. **End to end, one call, real decisions all the way through** — a
   single `run_rule_dispute` call for a real claimant produces a computed
   `issue_severity`, a real `dispute_outcome`, a residual-driven
   `attribution_locus`, a decided `emotion`, AND an updated
   `self_worth_after` — confirmed:
   `{issue_severity: 0.333, dispute_outcome: 'escalate', attribution_
   locus: 'specific_act', emotion: 'guilt', self_worth: 1 -> 0}`.
2. **Persistence across repeated REAL disputes, not just repeated
   synthetic `record_incident_outcome` calls** — 5 consecutive
   `run_rule_dispute` calls for the SAME claimant+domain drift
   `self_worth`: `1 -> 0 -> 0 -> 0 -> -1 -> -1`, and — the emergent,
   unregistered-in-advance but theoretically coherent finding — the
   EMOTION itself changes as the pattern solidifies:
   `guilt, guilt, guilt, guilt, shame` — `specific_act` flips to
   `global_self` once `self_worth` itself reaches `-1` and a further
   failure CONFIRMS rather than contradicts it. Repeated small failures
   read as isolated mistakes; once the pattern is established, the SAME
   kind of failure reads as confirming who you are.
3. **A different domain for the same resident is untouched by disputes in
   another domain** — `chess` stays at the projected value (`1`,
   matching global) after 5 real `monopoly_rules` disputes drove that
   domain to `-1`.
4. **Identical beliefs mint no dispute, self_worth untouched** — the
   already-registered floor (`DISPUTE_SEVERITY_AS_RESIDUAL_PREREG.md`)
   holds through the full pipeline too, returning
   `{"dispute_minted": False}` with `self_worth_after ==
   self_worth_before`.

## 4. Scope boundaries

- Does not hook this into bigville's actual live game loop or
  `BigvilleOcelotResident` — this delivers the ONE real, callable,
  ocelot-side entry point a future adapter would call; the bigville-side
  trigger (detecting a real rule dispute during actual play, translating
  a resident's `HeldRule`/asserted claim into a `[rel, a0, a1]` predicate)
  is a separate, larger, cross-repo integration, named but not attempted
  here — the same honest boundary every prior rung in this arc has kept.
- `band_code`/`witnesses`/`audience_gain`/`belief_plasticity` remain
  caller-supplied data (a real caller would read them from bigville's own
  `band_code`/`tie_strength` plumbing and a resident's drawn personality
  params) — this rung does not invent a live source for them.
- Neither `rule_dispute_escalation.json` nor `self_conscious_emotions.json`
  nor `rule_dispute_self_conscious_bridge.json` is edited — only
  `dispute_severity_from_beliefs.json` gained the one additive carry-over
  rule needed to compose.
