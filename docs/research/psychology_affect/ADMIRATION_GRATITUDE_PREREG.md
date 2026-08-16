# Admiration + gratitude — PREREG

**Task**: Phase C of the expanded emotional+preference system build plan
(`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`) —
generalizing `hate_attribution.py`'s crystallization ladder to the
positive sign (OCC's own Attribution branch: praiseworthy, not just
blameworthy).

## 0. A real bug found before designing, not assumed away

Verified directly before writing this PREREG: `crystallize_hate`'s gate
(`Gte(confirm_streak, effective_threshold)` + `crystallized==0.0`) never
checks the SIGN of the crystallizing pattern. A resident who receives
REPEATED POSITIVE incidents (consistently kind, praiseworthy behavior)
currently crystallizes into a `Hate` node with `consequence_route:
"removal"` — the exact opposite of the correct reading. Confirmed this
was never exercised by any existing test: every prior `negative=False`
call in the test suite is a single isolated exception incident (testing
the reset/resentment mechanism), never a repeated run reaching
crystallization. This rung fixes it as part of building admiration —
you cannot correctly add "positive patterns crystallize into admiration"
without also correcting "positive patterns wrongly crystallize into
hate," so the two are one change, not two.

## 1. Theoretical grounding

- **Weiner's OWN original context (1979, "A Theory of Motivation for
  Some Classroom Experiences"; the achievement-attribution work Weiner
  1985 — already this arc's citation for stability — generalizes)**:
  the controllability dimension originates in ACHIEVEMENT attribution,
  not blame attribution — a success attributed to a CONTROLLABLE cause
  (skill, effort) earns credit/admiration; a success attributed to an
  UNCONTROLLABLE cause (luck) does not, regardless of how good the
  outcome was. This is the exact positive mirror of hate's own
  controllability gate (`controllability_for`, already built) — reused
  verbatim, not re-derived.
- **OCC (Ortony, Clore & Collins 1988)** — Admiration is the Attribution
  branch's positive cell (approving of another's praiseworthy action);
  Gratitude is Admiration COMPOUNDED with a well-being appraisal
  (approving of the act AND being pleased about its benefit to oneself)
  — a lighter-weight, per-incident compound, not a stability-gated
  pattern judgment.
- **McCullough, Emmons & Tsang (2002), "The Grateful Disposition: A
  Conceptual and Empirical Topography," *Journal of Personality and
  Social Psychology*** — the companion paper to the unforgiveness
  citation `resentment_debt` already used: a debt of gratitude, like
  unresolved resentment, does not simply evaporate — it persists and
  motivates future reciprocity. `gratitude_debt` mirrors `resentment_
  debt`'s own accumulate-without-decay design for exactly this reason.

## 2. Design

**Fix**: `crystallize_hate`'s `where` gains a guard requiring the
tracked `regard_for` Concept's `external_field` to be NEGATIVE (reusing
the SAME `_held_regard_term`/sign-read pattern `derive_hate_attribution`
already uses for locus).

**New rule, `crystallize_admiration`**: mirrors `crystallize_hate`
exactly (SAME `confirm_streak`/`effective_threshold` ladder, SAME
`crystallized==0.0`-style guard on its own `admiration_crystallized`
flag) but gated on a POSITIVE `regard_for.external_field`. Mints an
`Admiration` node carrying `consequence_route` computed via the SAME
`controllability_for` sign check `crystallize_hate` already uses:
`controllable (>=0) -> "admiration"`; `uncontrollable (<0) -> "none"`
(Weiner's own achievement asymmetry: a lucky, uncontrollable success
does not earn the person admiration).

```
admiration_route = IfThenElse(controllability_for.external_field >= 0.0, Lit("admiration"), Lit("none"))
```

`record_hate_incident` reads whichever crystallization (Hate OR
Admiration) fired this call and dispatches evidence to the matching
Concept — `removal_desire_for`/`pity_for` (existing) or `admiration_for`
(new) — using the SAME `base_alpha * (1+arousal) * (1+debt)` formula,
swapping `resentment_debt` for the new `gratitude_debt` on the positive
side.

**`gratitude_debt`** (new `TargetPattern` attr, mirrors `resentment_
debt`'s shape but with a simpler trigger): every POSITIVE incident
(`signal > 0`, regardless of locus — gratitude, per OCC, does not
require pattern-stability OR pattern-violation, just a beneficial act)
increments `gratitude_debt` by a fixed unit (`1.0`, documented,
un-fitted — same honesty class as this arc's other fixed contribution
units), never decaying.

Zero new Rust — `Gt`/`Gte`/`Attr`/`Neighbours`/`PickUnique`/`IfThenElse`/
`Plus` all pre-exist; the whole design reuses `hate_attribution.py`'s
already-built machinery (`TargetPattern`, `confirm_streak`,
`TargetArousal`, `controllability_for`) end to end.

## 3. Predictions

1. **The bug fix**: repeated POSITIVE incidents no longer crystallize
   into `Hate` — `crystallized_this_call` never fires the `Hate` branch
   for a positive pattern.
2. **Repeated positive incidents crystallize into `Admiration` instead**,
   using the SAME threshold ladder (confirmed via the SAME arousal/
   increment coupling already measured for hate — no new pace claim
   needed, the ladder is reused verbatim).
3. **Controllability gates admiration's routing** — a positive pattern
   attributed to an UNCONTROLLABLE cause (e.g. luck) crystallizes but
   routes to `"none"`, not `"admiration"` — `admiration_for` receives no
   evidence in that case.
4. **`gratitude_debt` accumulates on EVERY positive incident**,
   independent of locus or whether admiration ever crystallizes — a
   single isolated kind act (never repeating into a stable pattern)
   still raises `gratitude_debt`.
5. **`gratitude_debt` amplifies `admiration_for`'s crystallizing alpha**
   the same way `resentment_debt` amplifies `removal_desire_for`'s —
   holding arousal fixed, a history with accumulated `gratitude_debt`
   produces a strictly higher `effective_admiration_alpha` than an
   identical history with none.
6. **Per-target isolation holds** for both `Admiration` crystallization
   and `gratitude_debt` accumulation.

## 4. Scope boundaries

- Does not give admiration its own "reset/resentment"-style discounted
  forgiveness mechanism — Sternberg's positive-triangle symmetry
  (passion + decision/commitment) is reused via the SAME arousal/
  threshold ladder; a positive-pattern analogue of the resentment RESET
  specifically (a disconfirming negative act discounted under arousal)
  is a real, separate, named follow-on, not built here.
- `gratitude_debt`'s fixed `+1.0` per-incident contribution (rather than
  a magnitude scaled to the incident's own significance) is a documented
  simplification — a real, named refinement (e.g. scaling by how much
  the act contradicted an existing negative pattern) is deferred.
- Does not model any DOWNSTREAM reciprocity behavior (an actual returned
  favor) — scoped to the motivational Concept and ledger existing,
  matching every other consequence-Concept-not-enacted-behavior
  convention in this arc.
