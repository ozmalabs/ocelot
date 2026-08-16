# Evidence-weighted plasticity + habituated audience gain — PREREG

**Task**: continuing the constants audit — *"Do both"* (`belief_plasticity`
and `audience_gain`, the two remaining flagged "numbers from nowhere" from
`SELF_COMPLEXITY_COUPLING_RESULTS.md` §4). Both get the SAME shape already
applied twice this arc (`peer_comparison`'s log-odds, `coupling_weight`'s
self-complexity decay): weighted against a REAL, observed graph quantity,
Laplace-style ("+1, made up when absent"), not a flat constant — reused
deliberately, not two new formulas invented.

## 1. `belief_plasticity` — weighted against the domain's own accumulated
   evidence

**Grounding**: two independently-converging, well-established findings.
(a) Bayesian precision-weighting: how much a single new observation should
move a belief is inversely proportional to how much evidence the belief
already rests on — an update rule that ignores accumulated evidence and
applies a flat rate forever is not Bayesian in even an approximate sense.
(b) Asch (1946, "Forming Impressions of Personality," *Journal of
Abnormal and Social Psychology*) — the PRIMACY effect in impression
formation: early information carries disproportionate weight in forming
an overall judgment; later, similar information moves the judgment less.
Both predict the SAME shape: a domain's FIRST incident should move belief
close to full personality-trait strength; the Nth incident should move it
proportionally less.

**Design**: `effective_alpha = belief_plasticity / (domain_incident_count
+ 1)`. `belief_plasticity` KEEPS its existing meaning (the personality
trait, Dweck's fixed-vs-growth axis, unchanged — this is NOT removed, only
further weighted) — a rigid person's belief moves slowly from the start
AND slows further with accumulated history; a flexible person's moves
faster from the start AND ALSO slows with history, just from a higher
baseline. `domain_incident_count` is a REAL observed quantity: how many
times `record_incident_outcome` has already fired for THIS domain Concept
— tracked as a plain integer attr (`incident_count`), incremented
mechanically in Python (the SAME class of bookkeeping
`find_or_build_resident_can`'s own idempotency check already performs —
observing/counting graph state, not a branching decision).

**Confirmed by direct probe before registering**: `belief_plasticity=0.5`
against a domain projected to `1` (matching earlier rungs' own Confident
resident), 8 repeated `standard_met=False` incidents:

```
incident 1: effective_alpha=0.500  state=0
incident 4: effective_alpha=0.125  state=-1
incident 8: effective_alpha=0.062  state=-1 (holds)
```

Compare to the pre-audit flat `alpha=0.5` trajectory
(`DOMAIN_SELF_WORTH_PROJECTION_RESULTS.md`): flipped to `-1` by incident
2. The weighted version takes longer (4 incidents) but still flips with
sustained evidence — belief perseverance, not belief paralysis.

## 2. `audience_gain` — weighted against the claimant's own dispute
   experience

**Grounding**: habituation (Thompson & Spencer 1966, "Habituation: A
Model Phenomenon for the Study of Neuronal Substrates of Behavior,"
*Psychological Review* — the foundational citation for the general
learning phenomenon; social-evaluative anxiety specifically is documented
to habituate with repeated public exposure, the basis of real exposure-
therapy practice for public-speaking/social anxiety). A resident who has
been through many public disputes before should feel LESS audience
pressure from the Nth one than a resident experiencing their first.

**Design**: computed by the CALLER (`domains/rule_dispute_full_pipeline
.py`), NOT inside `seeds/rule_dispute_escalation.json` — that seed stays
untouched, matching every prior rung's own discipline (git-status-gated,
confirmed each time). `effective_audience_gain = base_audience_gain /
(claimant_dispute_count + 1)`, where `claimant_dispute_count` is a REAL
observed quantity tracked the same way as `incident_count` above (a
plain integer attr on the resident's `Resident` node, incremented once
per `run_rule_dispute` call, regardless of domain — audience habituation
is about being watched in disputes generally, not one specific domain).
`DisputeContext.audience_gain` was ALREADY a caller-supplied data field
(`RULE_DISPUTE_ESCALATION_PREREG.md`'s own original design) — this rung
only changes HOW the caller computes the value it supplies, not the
field's meaning or the seed's own formula.

## 3. Predictions

1. **A domain's first incident uses the full personality-trait alpha** —
   `effective_alpha` at `incident_count=0` equals `belief_plasticity`
   exactly, byte-identical to pre-audit behavior for a resident's first
   incident in a domain.
2. **Later incidents in the SAME domain move belief less per incident,
   but sustained evidence still eventually flips it** — checked via the
   probe above, registered as a standing regression.
3. **A claimant's first dispute uses the full base `audience_gain`** —
   identical to pre-audit behavior for a resident's first-ever dispute.
4. **A claimant's Nth dispute (any domain) feels LESS audience pressure
   for the SAME witness count** — `effective_audience_gain` strictly
   decreasing with `claimant_dispute_count`, checked by comparing
   `DisputeContext.audience_gain` across repeated `run_rule_dispute` calls
   for the same claimant.
5. **`claimant_dispute_count` accumulates across DIFFERENT domains** — a
   resident who has been through disputes about `monopoly_rules` is
   already somewhat habituated when their first `chess` dispute happens —
   a genuine, checked consequence of scoping the counter to the resident,
   not the domain (distinct from `belief_plasticity`'s own domain-scoped
   counter, a deliberate difference between the two mechanisms: WHAT you
   believe is domain-specific; HOW MUCH an audience unsettles you
   generalizes across domains).

## 4. Scope boundaries

- `seeds/rule_dispute_escalation.json` is NOT edited — confirmed by the
  same git-status-gated test pattern as every prior rung.
- `belief_plasticity`'s own VALUE (the personality trait itself, e.g.
  `0.3`/`0.05`/`0.5` in existing demos/tests) is NOT re-derived from a
  population distribution in this rung — it stays caller-supplied data,
  same honesty class as `prior_self_worth`. Only its APPLICATION is now
  weighted by accumulated evidence, not its own sourcing.
- Does not model per-witness heterogeneity in the habituation effect (a
  familiar witness vs. a total stranger both count identically toward
  `claimant_dispute_count`) — a real, separate, named follow-on.
