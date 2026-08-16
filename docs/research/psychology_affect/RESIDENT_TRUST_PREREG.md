# Resident trust — PREREG

**Task**: Phase D of the expanded emotional+preference system build plan
(`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`) —
generalizing `trust_mayor` (confirmed, before this rung, to be a real,
evidence-driven CAN node with structural `causal_influence` edges, but
fixed to "the mayor specifically") to ANY target, decomposed per
Castelfranchi's cognitive trust theory.

## 1. Theoretical grounding

- **Castelfranchi & Falcone (2010), *Trust Theory: A Socio-Cognitive and
  Computational Model*; earlier Castelfranchi & Falcone (1998), "Principles
  of Trust for MAS"** — the standard COMPUTATIONAL trust model for
  agent systems (as opposed to Mayer-Davis-Schoorman's organizational-
  psychology one): trust decomposes into independent belief components —
  COMPETENCE (can they do it) and WILLINGNESS (will they choose to). A
  target competent but unwilling is not trusted; a target eager but
  incompetent is not trusted either — trust requires BOTH, not their
  average.
- **The "weakest link" combination rule**: the standard, simple
  operationalization of Castelfranchi's AND-like requirement in
  computational trust models — trust is capped by whichever dimension is
  WORSE, not smoothed by averaging a strength in one against a weakness
  in the other.

## 2. Design

**Two independent target-scoped ToM beliefs** (reusing `bigville_
theory_of_mind.mint_resident_tom_belief` — the SAME named entry point
`controllability_for` already established, since competence and
willingness ARE beliefs about the target's own properties, not the
resident's affect toward them):

```
competence_for:<target>    -- can the target do what's asked
willingness_for:<target>   -- will the target choose to
```

**Trust is a COMPUTED READ, not a third accumulating Concept**: `min`
of the two Concepts' `external_field`s, evaluated at query time. This is
a deliberate design choice, not a missing piece — trust is a pure
function of two already-tracked beliefs; a third evidence-accumulating
ledger would duplicate state rather than deriving from it.

```
read_trust(competence, willingness) = min(competence.external_field, willingness.external_field)
```

`record_trust_incident(inner, competence, willingness, *, dimension, positive, alpha=0.3)`
applies evidence to WHICHEVER Concept the incident is actually about —
a competence-relevant incident (succeeded/failed at a task) or a
willingness-relevant incident (chose to help/chose to betray) — the
SAME `concept_apply_evidence` primitive every belief update in this arc
uses, dispatched by caller-supplied `dimension` (data, not a decision).

`trust_mayor` (`worlds/bigville_can_beliefs.py`) is UNCHANGED — this is
a new, separate, target-GENERIC primitive alongside it, not a
replacement; `trust_mayor`'s own structural `causal_influence` coupling
into the resident's broader CAN network is a different, richer
integration this rung does not attempt to generalize.

## 3. Predictions

1. **Competence evidence alone does not raise trust** — with
   `willingness` still at its minted default (`0.0`), a positive
   competence incident leaves `read_trust` at `0.0` (`min(positive, 0.0)
   == 0.0`) — the weakest-link property, not a partial-credit average.
2. **Trust rises only once BOTH dimensions are positively evidenced** —
   after a positive incident in each dimension, `read_trust` matches the
   (equal, in this case) positive value.
3. **A single betrayal caps trust even with high competence** — a
   negative `willingness` incident drops `read_trust` to the new
   (negative) willingness value, REGARDLESS of how strongly competence
   is evidenced — trust cannot exceed its worst dimension.
4. **Per-target isolation** — a target's trust beliefs never affect a
   different target's own `competence_for`/`willingness_for`.
5. **Reuses the SAME ToM entry point** — `competence_for`/`willingness_
   for` are minted via `mint_resident_tom_belief`, confirming they are
   genuine ToM-belief instances, not a forked parallel representation.

## 4. Scope boundaries

- Does not implement Castelfranchi's third dimension, DEPENDENCE (how
  much the truster actually relies on the target) — a real, named,
  deferred refinement; this rung builds competence × willingness only.
- Does not couple `read_trust` to `shape_fit_preference`'s own signal as
  a cold-start prior (named in the plan as optional, not required) — a
  real, deferred integration point.
- Does not touch or generalize `trust_mayor`'s own structural
  `causal_influence` coupling into the resident's broader CAN network —
  a separate, richer integration, out of scope here.
- `min()` as the combination rule is a documented, standard
  simplification of Castelfranchi's AND-like requirement, not
  independently validated against a richer multiplicative or weighted
  model.
