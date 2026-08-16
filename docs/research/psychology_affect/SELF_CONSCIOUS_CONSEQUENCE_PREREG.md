# Self-conscious emotion consequences — PREREG

**Task**: Phase A of the expanded emotional+preference system build plan
(`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`). Shame
and guilt were confirmed, before this rung, to terminate as bare
categorical labels (`SelfConsciousSignal.emotion`) with no differentiated
downstream consequence — `record_incident_outcome` moves `self_worth`
gated only on `attribution_locus`, never branching on WHICH of the four
self-conscious emotions actually fired. This closes exactly the
asymmetry `hate_attribution.py` already closed for other-directed
appraisal (hate → `removal_desire_for`, pity → `pity_for`).

## 1. Theoretical grounding

- **Tangney & Dearing (2002), *Shame and Guilt*** — already cited in
  `self_conscious_emotions.json`'s own docstrings for the appraisal
  structure itself; this rung uses their OTHER central claim: shame and
  guilt are NOT interchangeable "feeling bad" states — they carry
  DIFFERENT, well-documented motivational consequences. Guilt (an
  attribution to a SPECIFIC ACT — "I did a bad thing") motivates
  REPARATIVE action toward whoever was affected: confession, apology,
  amends. Shame (an attribution to the GLOBAL SELF — "I am bad") motivates
  WITHDRAWAL: hiding, avoidance, escape from the exposing situation.
- **This is the exact mechanism already encoded in `attribution_locus`**
  (`ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md`, reused unchanged by
  `self_conscious_emotions.json`'s own `sc_decide_emotion`: `global_self`
  attribution + violated standard → shame; `specific_act` attribution +
  violated standard → guilt) — so the consequence this rung adds is not a
  new judgment, it is reading a decision the substrate already made and
  routing evidence accordingly, the same rules-decide/Python-dispatches
  division of labor `HATE_PITY_TOM_UNDERSTANDING_PREREG.md`'s
  `consequence_route` already established.

## 2. Design

**Two new domain-scoped Concepts** (`domains/can_self_worth_bridge.py`,
minted via the SAME idiom `mint_domain_self_worth` already uses — a
fresh, uncoupled Concept, NOT causally coupled to global `self_worth` the
way domain self-worth is, since a reparative/withdrawal urge is not a
generalized expectancy, it is a fresh per-domain accumulator):

```
mint_domain_reparative_desire(inner, resident_can, domain) -> Concept  # "reparative_desire_for:<domain>"
mint_domain_withdrawal_desire(inner, resident_can, domain) -> Concept  # "withdrawal_desire_for:<domain>"
```

**One new dispatch function**, called with the ALREADY-DECIDED `emotion`
string `rule_dispute_full_pipeline.py` already reads off
`SelfConsciousSignal.emotion` (line ~151):

```
record_self_conscious_consequence(inner, resident_can, domain, *, emotion, alpha=0.3)
    emotion == "guilt" -> mint + concept_apply_evidence(reparative_desire, +1.0, alpha)
    emotion == "shame" -> mint + concept_apply_evidence(withdrawal_desire, +1.0, alpha)
    otherwise (hubristic_pride/authentic_pride/embarrassment/none) -> no evidence applied to either
```

Wired into `run_rule_dispute` (`domains/rule_dispute_full_pipeline.py`)
immediately after `emotion` is read (line ~151), alongside the existing
`record_incident_outcome` call — no seed edit (`self_conscious_emotions.
json` stays untouched, exactly as `ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.
md`'s own precedent argued for building in the bridge layer rather than
touching a foundational, independently-tested seed).

## 3. Predictions

1. **A guilt-classified incident applies evidence to `reparative_desire_
   for:<domain>`**, leaving `withdrawal_desire_for:<domain>` untouched
   (zero evidence, stays at its minted default).
2. **A shame-classified incident applies evidence to `withdrawal_desire_
   for:<domain>`**, leaving `reparative_desire_for` untouched.
3. **Every other classification (hubristic_pride/authentic_pride/
   embarrassment/none) applies evidence to NEITHER** — a genuine,
   specific gate, not a catch-all default.
4. **Repeated guilt incidents in the SAME domain accumulate** on the SAME
   `reparative_desire_for:<domain>` Concept (idempotent minting, matching
   `mint_domain_self_worth`'s own re-use-not-reset discipline) — a
   resident who repeatedly falls short in one domain shows a stronger,
   not merely repeated, reparative urge.
5. **Domain isolation holds** — a guilt incident in one domain does not
   move `reparative_desire_for`/`withdrawal_desire_for` in a DIFFERENT
   domain for the same resident.

## 4. Scope boundaries

- `alpha` is flat (no arousal/resentment-debt-style amplification) —
  this rung is scoped to closing the missing consequence entirely, not
  to building a passion/resentment analogue for self-conscious emotions;
  that composition is a real, separate, named follow-on if warranted.
- Does not couple `reparative_desire_for`/`withdrawal_desire_for` back
  into `self_worth`'s own belief — the consequence is a separate
  observable, not a feedback loop, matching hate's own `removal_desire_
  for`/`pity_for` design (motivational output, not a belief-revision
  input).
- Does not model the DOWNSTREAM behavioral act (an actual apology, an
  actual withdrawal) — scoped exactly to the motivational Concept
  existing and accumulating evidence, per this whole arc's own
  "consequence Concept, not enacted behavior" convention.
