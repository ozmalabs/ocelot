# Shared arousal / excitation transfer — PREREG

**Task**: user, following the "can an agent hate another agent" discussion:
*"also the concept of hatefucking needs to work."* I proposed scoping this
as an abstract arousal-sharing mechanism (Zillmann's excitation transfer),
not narrative/depictive content — the user confirmed: *"yes prereg it."*
This document registers exactly that mechanism, at the same abstraction
level as every other rung in this arc (CAN Concepts, scalars, Terms) —
no narrative content anywhere in the build.

## 1. Theoretical grounding

- **Schachter & Singer (1962), "Cognitive, Social, and Physiological
  Determinants of Emotional State," *Psychological Review*** — the
  two-factor theory of emotion: physiological arousal is largely
  UNDIFFERENTIATED at its source; which emotion it gets labeled as depends
  on the cognitive context available when it's felt, not on the arousal's
  origin.
- **Zillmann (1971, "Excitation Transfer in Communication-Mediated
  Aggressive Behavior," *Journal of Experimental Social Psychology*;
  1983)** — Excitation Transfer Theory: residual arousal from one source
  (anger, conflict, fear) TRANSFERS to and intensifies a subsequent,
  cognitively-distinct emotional/motivational state, if the two occur
  close enough in time that the arousal hasn't fully dissipated.
- **Dutton & Aron (1974), "Some Evidence for Heightened Sexual Attraction
  Under Conditions of High Anxiety," *Journal of Personality and Social
  Psychology*** — the classic empirical demonstration (the "bridge
  study"): arousal from fear got misattributed as attraction to a
  co-present target. This is the SAME mechanism the user named — hostility
  -driven arousal misattributed as desire, toward the same target,
  because arousal itself does not carry its own valence label.
- **This codebase's own `core_emotions.json`** already uses `arousal` as
  the general affective-science quantity ("the circumplex: valence=sign of
  progress/value, arousal=magnitude of surprise/precision") — a SHARED,
  cross-emotion-family value already, not invented for this rung. This
  rung is the first place that shared quantity actually gets READ FROM by
  more than one belief update, which is the entire point.

## 2. Design

**`TargetArousal{level}`** — one per (resident, target) pair, a scalar
tracking CURRENT elevated arousal connected to that target, from ANY
source — valence-blind, matching Schachter-Singer directly (a hostile
incident and an exciting one both raise it the SAME way, by their
INTENSITY, not their sign).

**Any evidence-applying incident about a target both (a) reads the
current `TargetArousal.level` to BOOST its own effective alpha, and (b)
raises `TargetArousal.level` by its own intensity, THEN decays it by a
fixed multiplicative factor** (a physiologically-motivated FIXED time
constant — real autonomic arousal decays over a roughly fixed window post-
stimulus, this is not an attempt to ONLINE-ESTIMATE anything, so it is NOT
the count-divided learning-rate shape `EVIDENCE_AND_AUDIENCE_WEIGHTING_
RESULTS.md` already found and retracted — checked explicitly before
registering, not assumed safe by analogy):

```
effective_alpha = base_alpha * (1 + TargetArousal.level)   [READ, before this incident's own contribution]
TargetArousal.level = TargetArousal.level*decay + intensity [UPDATE, after]
```

**Confirmed empirically before finalizing**: identical attraction-relevant
evidence (`base_alpha=0.3`) applied to a `desire_for:<target>` Concept
moves it `0.300` with no prior arousal, `0.540` (**+80%**) when a hostile
incident (`intensity=0.8`) toward the SAME target fired immediately
before — zero change to the evidence itself, purely from shared,
undifferentiated arousal.

**Reuses, does not invent**: `concept_apply_evidence` (the same PyO3 op
every rung since `PERSISTENT_SELF_WORTH_PREREG.md` has used),
`force_all_dirty`+`run_rules` (the same gotcha-avoidance idiom, regression
-tested there, reused verbatim here), plain CAN `Concept` nodes for BOTH
the hostility-relevant and desire-relevant beliefs (mirroring domain-
scoped `self_worth:<domain>` Concepts' own shape, generalized to
`<relation>:<target>` naming). Zero new Rust.

## 3. Predictions

1. **Elevated arousal strictly amplifies a co-target incident's effect**
   — confirmed above (`0.300 → 0.540`), registered as a standing
   regression.
2. **The SAME mechanism works regardless of WHICH relation fires first**
   — desire-driven arousal should amplify a SUBSEQUENT hostility update
   toward the same target too (Schachter-Singer's valence-blindness
   predicts symmetry: this is not a one-way "hate boosts desire" special
   case, it is "any co-target arousal boosts any co-target update").
3. **Arousal decays** — after enough incidents WITHOUT a fresh spike (or
   enough elapsed calls), `TargetArousal.level` returns toward `0`, and a
   subsequent incident's boost shrinks back toward baseline — Zillmann's
   own "if the two occur close enough in time" condition, made concrete
   and falsifiable (not merely asserted).
4. **Arousal is PER-TARGET, not global** — a hostile incident toward
   target A does not amplify a desire-relevant incident toward target B;
   the misattribution requires genuine co-occurrence around the SAME
   person, matching Dutton & Aron's own design (the effect required the
   SAME person being present, not any arousing stimulus plus any nearby
   target).

## 4. Scope boundaries

- Does NOT build the full "hate" attribution mechanism named in the prior
  discussion (`regard_for:<target>` reaching a stable, global-negative,
  low-plasticity state via the attribution-locus machinery) — this rung
  demonstrates the arousal-sharing mechanism generically, over plain
  Concepts, not over a fully-realized hate/desire cognitive architecture.
  Both remain real, named, separate follow-ons.
- Does NOT produce or require any narrative, depictive, or dialogue
  content anywhere — every artifact in this build is a scalar, a Concept
  name, or a Term formula, the SAME abstraction level as `self_worth`,
  `attribution_locus`, and `relative_self_worth` before it.
- The decay factor is a documented, un-fitted physiological time-constant
  choice (same honesty class as `k=3.0`, `res_gain=1.0`,
  `base_coupling=0.6`) — not independently validated against real
  autonomic-arousal decay curves.
- Sits under the SAME ethics framing the abusive-relationship research
  line already established for sensitive relational/psychological
  territory in this project: mechanism, not depiction; measured, not
  narrated.
