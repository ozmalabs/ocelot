# Domain-scoped self-worth as projection-then-decoupling — PREREG

**Task**: three-part research arc (this session) on whether CAN/PSI's
single global `self_worth` scalar is sufficient. User's own synthesis of
the causal structure: *"in a new domain, you project into it. your core
self worth affects that projection, rather than vice versa."* This
document registers and builds exactly that mechanism.

## 1. Theoretical grounding

**Rotter (1954, *Social Learning and Clinical Psychology*)**: Social
Learning Theory's distinction between GENERALIZED expectancy (a broad,
cross-situational belief) and SPECIFIC expectancy (belief about one
particular task/situation). Rotter's own finding, precisely matching the
user's framing: in a novel or unfamiliar situation with little or no
direct experience, behavior potential is driven mostly by the generalized
expectancy; as specific experience accumulates in that situation, the
specific expectancy increasingly displaces the generalized one's
influence. This is the formal version of "you project your core self-worth
into a new domain, and only your own real history there displaces it" —
found and confirmed as the correct citation for the user's own structural
claim, not fitted to it after the fact.

## 2. The mechanism — confirmed live, before registering, needs ZERO new
   code beyond correct graph wiring

`domains/can_self_worth_bridge.py`'s existing pieces already implement
Rotter's mechanism once the graph is wired correctly — no new Rust, no new
rule, no new formula:

- A domain Concept minted with `identity_field=0.0` (no independent
  personality prior — a domain a resident has never faced has none) and
  `causal_influence` coupling (both directions, mirroring
  `STRUCTURAL_EDGES`' own convention and the `CAN_CONSUMER_MIGRATION` fix)
  to the resident's global `self_worth` Concept.
- The FIRST relaxation (`can_native_update_3state`'s own weighted-sum
  threshold formula, unchanged) has nothing else to go on but the coupling
  term, so the domain Concept's `state` settles to whatever the global
  Concept's CURRENT state is — projection, mechanically, not a
  special-cased Python blend.
- `record_incident_outcome` applied to the DOMAIN Concept specifically
  (not the global one) accumulates `external_field` there; once that
  outweighs the coupling term, the domain Concept's own state decouples
  from the global one and reflects its own track record instead —
  Rotter's specific expectancy displacing the generalized one.

Confirmed empirically (`scripts/domain_self_worth_projection_demo.py`
below), a `Confident` resident (global `self_worth=1`):

```
brand-new domain, no track record:          domain=1  (projected from global)
after 3 negative domain-specific incidents: domain=0  global=1  (still unmoved)
after 4-5 negative domain-specific incidents: domain=-1 global=1 (decoupled)
```

## 3. Design

`mint_domain_self_worth(inner, resident_can, domain, *, coupling_weight=0.6)`
in `domains/can_self_worth_bridge.py`:

1. Idempotent lookup: a Concept named `self_worth:<domain>` under the
   resident's own Microtheory, found by name, is reused (mirrors
   `find_or_build_resident_can`'s own idempotency discipline) — a second
   call for the same resident+domain does not re-mint or reset the
   already-drifted belief.
2. If absent: mint `Concept{name: "self_worth:<domain>", state: 0.0,
   external_field: 0.0, identity_field: 0.0}`, add it to the resident's
   Microtheory (`has_concept`), couple it BOTH directions to the global
   `self_worth` Concept via `causal_influence` (weight `0.6`, the same
   documented, un-fitted structural weight `STRUCTURAL_EDGES` already
   uses elsewhere in this exact file), `force_all_dirty()`, relax.
3. Returns the domain Concept, ready for `record_incident_outcome` to
   target directly (that function already accepts any `concepts` dict
   with a `"self_worth"` key — a caller passes `{"self_worth": domain_
   concept}` to apply evidence to the DOMAIN belief instead of the global
   one, no new function needed there).

**No seed is edited** — this is entirely graph wiring inside the existing
CAN productions/rules, mirroring `dispute_severity_from_beliefs.json`'s
own "strictly additive, reuse the existing production" discipline, here
done in Python since minting a domain Concept per resident-domain pair is
itself mechanical world-adapter data, not a new decision (the DECISION —
what the settled state becomes — is still entirely the engine's own
Hopfield relaxation).

## 4. Predictions

1. **A brand-new domain projects the current global `self_worth` state**,
   confirmed by the empirical probe above, registered as a standing test.
2. **Domain-specific evidence eventually decouples the domain belief from
   the global one** — repeated same-sign evidence in one domain does NOT
   move the global `self_worth` Concept at all (it was never the evidence
   target), confirming true independence once decoupled, not merely a
   temporary local deviation that snaps back.
3. **Two DIFFERENT domains for the SAME resident can hold opposite
   beliefs simultaneously** — e.g. `self_worth:public_speaking=-1` after
   repeated failures there, `self_worth:chess=1` after repeated successes,
   while global `self_worth` stays at its own value throughout — this is
   the direct, falsifiable test of the user's original question
   ("low self-worth generally but very confident on a topic").
4. **Idempotent minting**: a second `mint_domain_self_worth` call for the
   same resident+domain returns the EXISTING, possibly-drifted Concept,
   not a freshly reset one — mirrors `find_or_build_resident_can`'s own
   discipline exactly.
5. **The coupling weight has a hard THRESHOLD, not a proportional pull**
   — checked, not assumed, and REVISED live after the first run: this is
   a discrete 3-state system (`can_native_update_3state`'s own
   `sum*temperature > 0.549` threshold), so "a smaller pull" is not the
   right mental model. Below `coupling_weight≈0.366` (at `temperature=1.5`,
   the resident's own `beta`), the domain Concept lands in the NEUTRAL `0`
   state, not a weaker projection of the global sign; at/above `≈0.37`, it
   crosses fully into the global belief's sign. There is no partial-credit
   regime — it is a genuine threshold crossing, not a dial.

## 4b. Belief plasticity as a personality trait (registered before
    finalizing, confirmed live)

User, immediately after the projection mechanism: *"that needs to be also
working the other way. Some people DO NOT learn that. This needs to be a
personality based trait."* Correct, and directly grounded: **Dweck's
fixed vs. growth mindset** (see the second research pass in this arc) is
precisely "some people's domain-specific competence belief resists
updating from evidence, others' updates readily" — the same construct,
named. Rotter's own theory doesn't specify a UNIFORM rate at which specific
expectancy displaces generalized expectancy either; individual differences
in that rate are the natural reading of "some people do not learn that."

**The mechanism already has the right knob — it just needed to stop being
a hardcoded default.** `record_incident_outcome`'s `alpha` parameter
(`h_i ← h_i + alpha·evidence`) IS the belief-plasticity axis: it controls
how much each incident's evidence outweighs the coupling-projection term
per PREREG Sec2's own formula. No new parameter, no new Term — `alpha`
is `belief_plasticity`, read from `resident["params"]` (the SAME
convention `prior_self_worth`/`w_supergraph`/`w_spite` already use) by the
CALLER, exactly as every other personality trait in this file already
flows from data to Python to a mechanical PyO3 call.

Confirmed empirically before finalizing:

```
Rigid (alpha=0.05):      global=1 -> [1, 1, 1, 1, 0, 0, 0, 0]   (barely dented after 8 incidents)
Flexible (alpha=0.5):    global=1 -> [0, -1, -1, -1, -1, -1, -1, -1]  (flipped by incident 2)
```

**Prediction 6 (added)**: the SAME number of same-sign domain-specific
incidents produces a strictly SMALLER magnitude of belief drift for a
low-`belief_plasticity` resident than a high-`belief_plasticity` one,
holding everything else (global self_worth, domain, evidence sign)
identical.

## 5. Scope boundaries

- Does not build the self-compassion asymmetry (`alpha` gated by self-vs-
  other appraisal target) or the calibration/Dunning-Kruger gap — both
  named as separate, real follow-on rungs from the same research arc, not
  attempted here (this document is scoped to the projection mechanism
  specifically, per the user's own most recent, precise instruction).
- `coupling_weight=0.6` is a documented, un-fitted constant (same honesty
  class as every other constant this arc has used) — chosen to MATCH the
  existing `STRUCTURAL_EDGES` convention, not independently tuned.
- Does not address WHICH domains get minted or when (a live trigger —
  e.g. minting `self_worth:rules_arguments` the first time a resident is
  ever party to a rule dispute) — named as follow-on, not built; this
  rung provides the mechanism, a caller decides when to invoke it.
