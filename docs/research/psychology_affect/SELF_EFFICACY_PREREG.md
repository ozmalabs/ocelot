# Self-efficacy — PREREG

**Task**: Phase E of the expanded emotional+preference system build plan
(`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`) —
belief in one's OWN capability, distinct from `self_worth`, wired into
`AffectiveState.competence` (confirmed, before this rung, a live schema
field that was never meaningfully written — only a default-zero init in
`domains/doom_dual_process_ingest.py`, never a real evidence-driven
value).

**Naming note, to avoid confusion with Phase D**: this rung's
`self_efficacy_for:<domain>` is a resident's belief about their OWN
capability in a domain. Phase D's `competence_for:<target>` is a
resident's ToM belief about ANOTHER resident's capability. Same word,
different holder — no technical or conceptual collision (different
Concept names, different purpose), named explicitly here so the
distinction is on the record.

## 1. Theoretical grounding

- **Bandura (1977), "Self-Efficacy: Toward a Unifying Theory of
  Behavioral Change," *Psychological Review*; Bandura (1997),
  *Self-Efficacy: The Exercise of Control*** — self-efficacy is belief
  in one's capability to EXECUTE a course of action, distinct from
  self-esteem/self-worth (a global self-evaluation). Critically,
  Bandura's own repeated emphasis: self-efficacy is TASK-SPECIFIC by
  design — believing oneself skilled at chess does not generalize into
  believing oneself skilled at everything, unlike self-worth's own
  generalized-expectancy structure (Rotter 1954, already this arc's own
  citation for `self_worth`'s domain-projection design). This is why
  `self_efficacy_for:<domain>` is built FRESH and UNCOUPLED per domain
  (mirroring `reparative_desire_for`/`withdrawal_desire_for`'s own
  fresh-accumulator shape), NOT `self_worth`'s projected-then-decoupling
  one.
- **Bandura's own central behavioral claim**: self-efficacy predicts
  PERSISTENCE versus AVOIDANCE in the face of difficulty — high
  self-efficacy sustains effort; low self-efficacy predicts giving up or
  avoiding the task altogether. This is a genuinely different behavioral
  axis from `self_worth`'s own consequences (mood, shame/guilt) —
  self-efficacy drives WHETHER YOU KEEP TRYING, not how you feel about
  yourself.

## 2. Design

**`self_efficacy_for:<domain>`** — a domain-scoped CAN Concept, minted
via the SAME `mint_target_concept`-family idiom every other rung in this
arc uses, but WITHOUT `self_worth`'s coupling-then-decoupling causal
edges — a fresh accumulator starting at `0.0`, per Bandura's own
task-specificity claim.

```
record_self_efficacy_incident(inner, concept, success, alpha=0.3)
    evidence = 1.0 if success else -1.0
    concept_apply_evidence(concept, evidence, alpha)
```

**`read_persistence_disposition(efficacy_value)`** — Bandura's own
behavioral claim, made concrete: `efficacy_value >= 0.0 -> "persist"`,
`< 0.0 -> "avoid"`. A genuine behavioral classification, not an affect
label — this is what self-efficacy is FOR, distinct from every
mood/appraisal Concept elsewhere in this arc.

**`sync_competence_to_affective_state(inner, affective_state_node,
efficacy_concept)`** — writes the efficacy Concept's CURRENT
`external_field` directly onto `AffectiveState.competence` (the SAME
schema field `seeds/affective_state_core.json`'s own
`psi_project_canonical_affect` rule already writes to from
`ModulatorState.competence`, confirmed live and dead before this rung).
Mechanical write, no new schema, no PSI drive-competition machinery
required — this rung wires an ALREADY-DEFINED field with real data, it
does not build a new one or attempt to model PSI's own leading-drive
selection (a separate, larger, out-of-scope integration).

## 3. Predictions

1. **Repeated success incidents raise `self_efficacy_for:<domain>`.**
2. **Repeated failure incidents lower it** — same Concept, opposite
   sign, symmetric magnitude.
3. **Persistence/avoidance flips with the sign** — enough failures drive
   `read_persistence_disposition` from `"persist"` to `"avoid"`; enough
   subsequent successes flip it back.
4. **No cross-domain generalization** — a resident's heavily-evidenced
   self-efficacy in one domain leaves a DIFFERENT domain's self-efficacy
   at its fresh `0.0` default, confirming the task-specificity design
   (no coupling edge exists to leak through, unlike `self_worth`'s own
   domain projection).
5. **`sync_competence_to_affective_state` correctly wires the confirmed-
   dead field** — a real `AffectiveState.competence` value after sync
   matches the efficacy Concept's own current value exactly.

## 4. Scope boundaries

- Does not model PSI's own `ModulatorState`/leading-drive competition
  (`psi_select_initial_leading_drive`/`psi_switch_leading_drive`) — the
  sync writes `AffectiveState.competence` directly, a mechanical bridge,
  not an attempt to make self-efficacy drive PSI's own drive-selection
  process. A real, deferred, larger integration.
- Does not couple `self_efficacy_for` to `resentment_debt`/`gratitude_
  debt`-style ledgers or arousal amplification — Bandura's own theory
  gives no basis for a passion-style amplification of self-efficacy
  evidence; flat `alpha`, by design.
- `read_persistence_disposition`'s `>=0.0` boundary is a documented,
  un-fitted threshold, same honesty class as every other boundary choice
  in this arc.
