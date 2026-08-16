# Hate attribution — PREREG

**Task**: user, following the "can an agent hate another agent" discussion
(answered, not built, in this arc's prior turn): *"build the hate
attribution mechanism next."* That discussion named the shape without
building it: hate maps onto the ALREADY-BUILT self-directed
attribution-locus residual (`ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md`),
generalized from a pattern about ONESELF to a pattern about ANOTHER
agent — "hate = the same global+stable negative-attribution pattern
directed outward that shame is directed inward." This document registers
that generalization plus the two pieces the prior discussion said would
be missing: a stability/essentialism gate (hate is a disposition, not a
single angry appraisal) and a motivational "desire for removal"
consequence.

## 1. Theoretical grounding

- **Sternberg (2003), "A Duplex Theory of Hate: Development and
  Application to Terrorism, Massacres, and Genocide," *Review of General
  Psychology*** — hate has three components: negation of intimacy
  (distancing/repulsion, replacing any positive regard), passion (intense
  arousal — this rung does not re-derive that piece, `SHARED_AROUSAL_
  EXCITATION_TRANSFER_PREREG.md`'s `TargetArousal` already exists for it,
  named as an un-wired optional coupling below), and **decision/commitment
  — a STABLE, over-TIME commitment to the negative view, not a single
  outburst**. This third component is what a single-incident appraisal
  cannot supply and what this rung's stability gate is FOR.
- **Fischer, Halperin, Canetti & Jasini (2018), "Why We Hate," *Emotion
  Review*** — hate requires perceiving the target's negative quality as
  STABLE and CENTRAL to their identity (an essentialist attribution — "they
  ARE bad," not "they DID a bad thing"), and it uniquely motivates a goal
  of **ELIMINATING or REMOVING** the target from one's life or environment
  — distinct from anger's goal of correcting the target's behavior. This is
  the direct grounding for gating "desire for removal" behind the
  stability gate, not behind any single negative appraisal.
- **Beck's cognitive theory of stable, global, negative attribution**
  (cited in the prior turn's "can an agent hate" answer) — the same
  attribution ERROR structure (stable + global + negative) that produces
  depressive self-attribution when directed inward produces hate when
  directed outward. This rung is the outward-directed instance of the
  identical structural claim `ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md`
  already built inward.
- **Direct reuse, not reinvention**: `ATTRIBUTION_LOCUS_AS_RESIDUAL_
  PREREG.md`'s residual — an incident's own implied signal compared
  against a HELD pattern, signs agreeing → global/stable, signs
  disagreeing → an exception — is reused VERBATIM, with the held pattern
  now LIVE-WIRED to a `regard_for:<target>` CAN Concept's own `state`
  (an improvement on that PREREG's own deferred scope note: *"wiring
  [the held pattern] to a LIVE CAN belief network... is a separate, larger
  integration, named but not attempted"* — attempted here, since both
  pieces — the residual rule and a real target-scoped Concept
  (`shared_arousal.mint_target_concept`) — already exist independently).

## 2. Design

**Nodes** (`seeds/hate_attribution.json`, `depends_on:
["can_native_reimplementation"]`):

- `TargetPattern{target, incident_count, confirm_streak, crystallized}` —
  one per (Microtheory, target), minted once, `tracks_concept` → the
  target's `regard_for:<target>` Concept (LIVE regard, read fresh each
  incident, not a duplicated stored field) and `tracks_removal_desire` →
  the target's `removal_desire_for:<target>` Concept — both minted via
  the EXISTING `shared_arousal.mint_target_concept` (reused, not
  reimplemented — same Concept shape as `regard_for`/`desire_for`
  already established there).
- `IncidentReport{target, signal, status}` — one per recorded incident,
  Python-added mechanically (`signal = -1.0` for a negative act, `+1.0`
  for a positive one — the same literal-recoding shape as
  `record_incident_outcome`'s existing `evidence = 1.0 if standard_met
  else -1.0`), linked `about_pattern` → the target's `TargetPattern`.
- `HateAppraisal{attribution_locus}` — minted per incident by a RULE
  (graph-native decision, CLAUDE.md's own standing requirement — the
  branch is NOT Python `if`/`else`), one of `{first_encounter,
  global_other, specific_act}`.
- `Hate{target}` — minted ONCE, only when the stability gate crosses.

**The residual** (mirrors `ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md`
Sec2 exactly, `held_regard` now the LIVE `regard_for` Concept's `state`
instead of supplied data):

```
held_regard = TargetPattern.tracks_concept.state   (live CAN belief, pre-this-incident)
incident_count == 0                                -> first_encounter (no pattern yet -- cannot hate on a first impression)
incident_count > 0, signs of held_regard & signal AGREE (confirms)    -> global_other
incident_count > 0, signs DISAGREE (an exception)                     -> specific_act
```

**The stability gate** (Sternberg's decision/commitment component, made
concrete and falsifiable):

```
confirm_streak <- confirm_streak + 1   if this incident's locus == global_other
confirm_streak <- 0                    otherwise (a SINGLE exception breaks the pattern)
crystallized   <- true, ONCE, when confirm_streak >= HATE_STABILITY_THRESHOLD (= 3, documented, un-fitted -- same honesty class as this arc's other fixed constants)
```

**The motivational consequence** (Fischer et al.'s unique-to-hate
elimination goal — gated behind stability, NOT fired by an isolated
angry appraisal, which is ordinary anger, not hate):

```
regard_for:<target>          <- concept_apply_evidence(evidence=this incident's signal, alpha)     [EVERY incident]
removal_desire_for:<target>  <- concept_apply_evidence(evidence=+1.0, alpha)   [ONLY the incident that crystallizes hate]
```

Both evidence applications are Python calling the pre-existing
`concept_apply_evidence` PyO3 op (the only call site for it anywhere in
this codebase — it is not a Rule effect), driven by values a RULE already
decided (`attribution_locus`, `crystallized`) — the same division of labor
`record_incident_outcome`/`record_targeted_incident` already established:
rules decide, Python reads the decision and calls the primitive.
`force_all_dirty()`+`run_rules()` bracket every evidence application, per
this arc's own standing gotcha.

## 3. Predictions

1. **A negative incident confirming an already-negative held regard →
   `global_other`.** Mirrors `ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md`
   prediction 1, generalized outward.
2. **The identical incident, but current regard is positive →
   `specific_act`**, forgiven as an exception, NOT counted toward
   crystallization.
3. **A first encounter (no prior incidents) → `first_encounter`, never
   `global_other`** — hate cannot form from a single first impression
   (Fischer et al.'s stability requirement, made structural).
4. **One `specific_act` resets `confirm_streak` to 0**, even after prior
   `global_other` confirmations had accumulated — a genuine exception
   breaks the "always like this" narrative (mirrors Miller & Ross's
   self-serving-bias asymmetry, now applied to a THIRD party's pattern
   rather than the agent's own).
5. **Crystallization requires the THRESHOLD, not the first
   `global_other` confirmation** — a single hostile incident, even one
   that reads as `global_other`, does not yet crystallize hate.
6. **`removal_desire_for` receives evidence ONLY on the incident that
   crystallizes hate**, not on ordinary `global_other` appraisals below
   threshold — the elimination motive is specific to the STABLE
   disposition, not to any one angry appraisal.
7. **Per-target isolation** — hate crystallizing toward target A does not
   touch target B's `TargetPattern`, `regard_for`, or `removal_desire_for`
   (mirrors `SHARED_AROUSAL_EXCITATION_TRANSFER_RESULTS.md` prediction 4's
   already-confirmed isolation property, expected to hold here by the
   same per-(microtheory,target) node-minting structure).

## 4. Scope boundaries

- Passion (Sternberg's second component) is NOT re-derived here —
  `SHARED_AROUSAL_EXCITATION_TRANSFER_PREREG.md`'s `TargetArousal` already
  models shared, valence-blind arousal per target; coupling
  `HATE_STABILITY_THRESHOLD` or `effective_alpha` to it (an aroused
  incident should count more) is a real, named follow-on, not attempted
  here, to keep this rung's own claim (the residual + stability gate +
  gated consequence) independently falsifiable first.
- `HATE_STABILITY_THRESHOLD=3` is a documented, un-fitted constant (same
  honesty class as `base_coupling=0.6`, `decay=0.7`) — not independently
  validated against real longitudinal intergroup-hostility data.
- Produces no narrative or depictive content anywhere — every artifact is
  a scalar, a Concept name, or a Term formula, the same abstraction level
  as every prior rung in this arc.
- Does NOT model in-group/out-group essentialism (hate directed at a
  CATEGORY rather than an individual target) — Fischer et al.'s own
  broader claim covers group-level hate; this rung is scoped to a single
  (resident, target) pair, matching `shared_arousal`'s own individual-pair
  scope.
- Sits under the SAME ethics framing already established for this
  project's sensitive relational/psychological territory (the abusive-
  relationship line, `shared_arousal`'s own framing): mechanism, not
  depiction; measured, not narrated. A crystallized `Hate` marker and a
  `removal_desire_for` scalar are the full observable surface — no
  violent action is modeled or enabled by this rung (the still-unbuilt
  `BIGVILLE_ADMISSIBILITY_GRAMMAR.md` violence design remains the
  separate, named gate for anything actionable).
