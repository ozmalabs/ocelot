# Hate → pity via a Theory-of-Mind understanding of the other — PREREG

**Task**: user, following "now, can we model hate to pity with
understanding?" (answered conceptually first, per this arc's own
discipline for proposing new mechanisms — Weiner's controllability
dimension, the piece of his attribution model not yet built here) —
*"yes - this should be based on their tom model of the other."* This
document registers exactly that: a resident's Theory-of-Mind
representation of WHY a target behaves as they do gates whether a
crystallizing hate routes its motivational consequence to
`removal_desire_for` (already built) or a new `pity_for` Concept.

## 0. Reuse audit — why a new Concept, not an existing ToM module

Investigated before designing (not assumed): this codebase has THREE
ToM-adjacent systems, and none model one bigville resident's belief about
a SPECIFIC other resident's circumstances:

- `domains/character_tom.py` — false-belief tracking (Sally-Anne style)
  for NARRATIVE TEXT CHARACTERS, reading comprehension, not bigville
  residents.
- `domains/psychology.py` — installs ToM VOCABULARY (`mental_state`,
  `theory_of_mind`, Premack & Woodruff 1978, Wimmer & Perner 1983,
  Baron-Cohen 1995) as Concepts the agent can introspect over — no
  resident-specific data.
- `domains/interlocutor_model.py` — the agent's own conversational-
  partner identity tracker, unrelated to bigville.
- `worlds/bigville_can_beliefs.py`'s `build_resident_can_mt` mints ONE
  resident's beliefs about the world/generic others — no node holds
  resident A's belief about resident B's circumstances specifically.

**So this rung is the first resident-of-resident ToM CONTENT in
bigville** — not a reuse of prior ToM work (wrong domain in every case)
but the SAME per-target Concept SHAPE this whole arc already established
(`shared_arousal.mint_target_concept`, reused verbatim once again): a
CAN Concept scoped to `(resident, target)`, exactly like `regard_for` and
`removal_desire_for` already are. The resident's ToM of the target IS a
CAN belief about the target, same as every other belief in this arc — no
new node type, no new primitive.

## 1. Theoretical grounding

- **Weiner (1980), "A Cognitive (Attribution)-Emotion-Action Model of
  Motivated Behavior: An Analysis of Judgments of Help-Giving," *Journal
  of Personality and Social Psychology*** — the founding empirical
  result: the SAME negative outcome attributed to a CONTROLLABLE cause
  produces anger and reduced helping; attributed to an UNCONTROLLABLE
  cause (illness, circumstance, lack of ability) produces sympathy/pity
  and increased helping. This is the third dimension of Weiner's
  attribution model — locus and stability are already built in this arc
  (`ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md`,
  `HATE_STABILITY_AROUSAL_COUPLING_PREREG.md`); controllability is the
  piece this rung adds.
- **Weiner (1985)**, already this arc's own citation for stability,
  formalizes all three dimensions together — controllability is
  orthogonal to locus/stability, not a replacement for either: a pattern
  can be global AND stable AND (newly) understood as uncontrollable,
  without ceasing to be recognized as a real, stable pattern. Hate's
  STABILITY (Sternberg's decision/commitment, `confirm_streak`
  crystallizing) is UNCHANGED by this rung; only which motivational
  Concept receives the resulting evidence changes.
- **Ross (1977), "The Intuitive Psychologist and His Shortcomings:
  Distortions in the Attribution Process," *Advances in Experimental
  Social Psychology*** — the Fundamental Attribution Error: absent
  specific information otherwise, people DEFAULT to dispositional
  (controllable) attributions for another's negative behavior. This
  grounds the DEFAULT direction this rung registers: with no ToM
  understanding at all, crystallization routes to `removal_desire_for`
  exactly as it already does (backward compatible) — understanding is
  what's required to shift away from the default, not the other way
  around.

## 2. Design

**`controllability_for:<target>`** — a new target-scoped CAN Concept
(minted via the EXISTING `shared_arousal.mint_target_concept`, tracked
from `TargetPattern` via a new `tracks_controllability` edge, exactly
mirroring `tracks_concept`/`tracks_removal_desire`/`tracks_arousal`).
This Concept's `external_field` IS the resident's ToM representation of
the target: positive/zero = believed controllable (the FAE default, or
explicit evidence of deliberate malice), negative = believed
uncontrollable (understood circumstances: illness, trauma, coercion,
lack of capacity).

**`record_understanding_incident(inner, pattern, *, exculpatory: bool,
alpha=0.3)`** — mechanical evidence application (reuses
`concept_apply_evidence` directly, the same primitive every belief update
in this arc uses): `evidence = -1.0 if exculpatory else +1.0`. No locus/
stability layer — unlike `regard_for`, there is no "confirms an existing
pattern" structure to a SINGLE piece of understanding; it is a flat,
accumulating CAN belief, the same shape `self_worth`'s original design
used before any of the locus/stability/arousal couplings existed.

**`crystallize_hate`'s existing effects gain ONE more Term-computed
attribute**, read at the SAME moment crystallization itself fires (no new
timing point, no new rule):

```
consequence_route = IfThenElse(controllability_for.external_field >= 0.0, Lit("removal"), Lit("pity"))   [Ross 1977's default: >=0 (no understanding, or believed controllable) -> removal]
```

written onto the minted `Hate` node. Python (`record_hate_incident`)
reads `Hate.consequence_route` — the SAME rules-decide/Python-dispatches
division of labor `attribution_locus` already established — and applies
the crystallizing incident's evidence to `removal_desire_for` (existing,
unchanged) OR the newly-minted `pity_for:<target>` Concept (mutually
exclusive; `pity_for` receives ZERO evidence when routed to `removal`,
and vice versa).

**`pity_for`'s evidence is NOT amplified by arousal or resentment_debt**
— a deliberate scope decision: Sternberg's passion component and
McCullough et al.'s resentment ledger are specifically models of
VENGEFUL motivation intensifying; pity is a structurally different
affective category (Weiner's own model pairs uncontrollable attribution
with REDUCED anger, not a parallel passion channel), so `pity_for`
receives flat `base_alpha` evidence, unamplified.

## 3. Predictions

1. **With no understanding at all, crystallization routes to `removal`**
   — byte-identical to this arc's existing (pre-this-rung) behavior;
   `pity_for` receives no evidence. Backward compatible, and the Ross
   1977 default.
2. **With sufficient exculpatory understanding accumulated BEFORE
   crystallization, the SAME crystallizing incident instead routes to
   `pity`** — `removal_desire_for` receives ZERO evidence in this case;
   `pity_for` receives it instead.
3. **The routing matches the sign test exactly**, including the boundary
   (`controllability_for.external_field == 0.0` routes to `removal`, the
   registered default direction).
4. **Per-target isolation holds** — target A's accumulated understanding
   does not affect target B's own routing.

## 4. Scope boundaries

- Understanding arriving AFTER crystallization does not retroactively
  re-route an already-crystallized `Hate`'s consequence — `consequence_
  route` is decided once, at the SAME moment `crystallized` itself is
  set, matching `Hate`'s own "fires exactly once" semantics. Post-
  crystallization re-routing (a real, plausible extension — "I used to
  want to remove them, now I understand and just pity them instead") is
  a named, deferred follow-on, not built here.
- Does not couple pity to arousal or resentment_debt (Sec2, deliberate).
- Does not model a stability/pattern layer for `controllability_for`
  itself (no locus/streak/threshold analogue) — a single flat CAN belief,
  the simplest form that supports this rung's own claim.
- Does not build any DOWNSTREAM consequence of holding `pity_for`
  evidence (e.g., helping behavior, as Weiner's own original study
  measured) — scoped exactly to the routing decision itself, per the
  user's own framing ("model hate to pity").
