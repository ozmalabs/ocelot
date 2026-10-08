# PREREG — the decode-through-ToM text arm as REUSE (or a generalization win)

**Committed BEFORE any number.** Per the repo's PREREG-then-measure discipline
and CLAUDE.md's architecture rule (the agent is a graph in Rust; Python is only
the world adapter; NO Python decisions). Successor to the Phase-3 rules-only cue
typer (`phase3_derisk/`), which scored 0.83 on FOMC house-style and **0.0** on
ECB rhetoric / 8-Ks / COT because it matched surface WORDS, not the utterance's
PURPOSE.

## Thesis (the user's reframe, verified against the substrate)

An utterance is a **manifold deformation with purpose**. For a rate/FX forecast
the signal is not the hawkish/dovish surface words — it is the SPEAKER'S INTENT:
a central bank emits a statement to MOVE a target audience's expectation. So the
typer must (a) DECODE the utterance against the FORECAST FRAME's symbols (policy
path, balance sheet, credibility, tenors/crosses), and (b) recover the PURPOSE
behind the deformation through the ToM layer, and (c) shift the forecast band by
an amount WEIGHTED BY HOW WELL THE UTTERANCE GROUNDED — grounding IS the
confidence.

## What the investigation established (do not re-derive; cite, build on)

The substrate ALREADY contains every structural piece. This arm is REUSE, not a
new representation:

- **2nd-order ToM (a belief ABOUT another mind)** = a per-(holder,target) CAN
  Concept `<aspect>_for:<target>` (`domains/bigville_theory_of_mind.py`,
  `domains/shared_arousal.mint_target_concept`). No bespoke ToM node type exists
  or should (`TOM_SYSTEM_UNIFICATION_RESULTS.md`). Graded by the CAN marginal
  ⟨σ⟩ — which per `seeds/causal_attitude_networks.json`
  (`marginal_expectation_is_grounding`) IS the grounding vector.
- **Evidence MOVES a target-scoped belief** = `inner.concept_apply_evidence`
  (Rust `can_ops.rs::apply_evidence_h`, `h += alpha*evidence`), the belief-update
  primitive every bigville arc drives (`hate_attribution`, `resident_trust`,
  `shared_arousal`, `can_self_worth_bridge`). This IS "induce a belief," seen
  from the receiver: an utterance is evidence applied to a target-scoped Concept.
- **A read/derived FACT → belief-update on a CAN Concept** = the GENERAL bridge
  `domains/reasoning_can_bridge.py` (`apply_derived_fact_as_can_evidence` /
  `apply_inference_hits_as_can_evidence`): `is_a(entity, attr)` becomes a
  `concept_apply_evidence` on the Concept named `attr` in the Microtheory the
  entity DENOTES — described in its own docstring as "the general resolution
  mechanism."
- **Surface-purpose vs actual-purpose divergence** = `domains/actor_goals.py`
  layer 3 (conflicting-meta-goal) + layer 5
  (`run_epistemic_signal_detectors` / `assess_epistemic_lean`: structural
  deception-vs-introspection-gap, NOT a cue lexicon).
- **Decode against a frame codebook** = `ShapeDecode` (`shape_decode.rs`,
  `seeds/shape_decode_loop.json`), already applied to narrative role/boundary
  recovery in `domains/story_tree.py` / `narrative_structure` /
  `reading_collapse.read_clause`.
- **Frame-symbol grounding of `about_concept`** = `seeds/intent.json`
  rules 990/991 (lexical exact `text==name`); Concept vocabulary is open/teachable
  via `domains/teach.py`.
- **Transitive grounding + confidence + overconfidence guard** =
  `ReachableFrom(node,'grounded_in')` (installed Rust Term, BFS-to-fixpoint),
  `domains/grounding_reach.grounding_reach` → `{reached, anchors, hops}` over the
  `seeds/grounding_anchors.json` anchors (Reality/Teacher/Consequence/Sensor), and
  `flag_ungrounded_confident` → `GroundingGap` for low-residual+high-confidence+
  UNgrounded nodes. Grounding is a VECTOR, per-frame (Mt), by `grounding_theory`.

## The ONE unverified seam (the reuse-vs-generalize boundary)

`reasoning_can_bridge` is fed today by the DEDUCTION/inference layer and
`worlds/bigville_can_beliefs.apply_scenario_evidence` by structured scenarios.
**Unverified:** does a TEXT-READ clause (`reading_collapse.read_clause` /
`media_analysis`/`actor_goals` annotate path, the corpus route) already flow into
that bridge, so a corpus utterance updates a target-scoped CAN belief?

Governing directive (user): **if it is not strict reuse, the machinery must be
made GENERIC — a net win regardless.** So this seam resolves two ways, both
acceptable, and the build MUST take whichever holds:

- **REUSE**: a text-read grounded predication already reaches
  `apply_derived_fact_as_can_evidence`. Then the arm is pure wiring: teach the
  frame-symbol Concepts + a central-bank speech-act codebook, and let existing
  rules apply evidence and read the marginal.
- **GENERALIZE**: the bridge is coupled to the deduction/scenario SOURCE. Then
  the fix is to make its INPUT source-agnostic — accept ANY grounded predication
  (deduction, bigville scenario, OR corpus clause) as CAN evidence. This unifies
  text-evidence and inference-evidence into one belief-update path and is a net
  win beyond this arm. NO new parallel text-only mechanism may be authored: the
  test of a correct fix is that bigville's existing callers are byte-unchanged.

## The mapping under test

A central-bank statement is, structurally, a bigville resident's ACTION that
applies evidence to a target-scoped CAN belief:

    utterance (corpus Message, tick=asof-bounded)
      -> read_clause grounds a predication over frame symbols   [ii, teach + 990/991]
      -> the actor's stance is evidence on `<stance>_for:market` CAN Concept
         (e.g. `hawkish_stance_for:rates_market`)               [reuse concept_apply_evidence
                                                                  via reasoning_can_bridge, general]
      -> purpose recovered: is the stance stated-sincerely or divergent?
         (actor_goals layers 3/5, structural)                   [i, reuse]
      -> the CAN marginal ⟨σ⟩ of that Concept, per-frame, IS the graded signal;
         its transitive grounding (ReachableFrom 'grounded_in' -> anchor) IS the
         confidence; a chain reaching no anchor mints GroundingGap and shifts ~0  [iii, reuse]
      -> shift the forecast band by direction(⟨σ⟩) x grounding-weight            [iii readout, media_analysis-shaped]

## Hypotheses (falsifiable, pre-declared decision rules)

- **H0 (the seam):** classify the corpus-clause → CAN-evidence path as REUSE or
  GENERALIZE by tracing `reasoning_can_bridge` inputs. Deliverable states which,
  with file:line. If GENERALIZE, the generalization is made source-agnostic and
  **bigville's existing callers must still pass their tests byte-unchanged**
  (the net-win gate). PROVEN iff the generalized bridge accepts a corpus-read
  predication AND the bigville CAN tests are green.

- **H1 (generalization — the headline):** the decode-through-ToM arm recovers
  forecast-relevant DIRECTION on the exact non-FOMC snippets the Phase-3 cue
  lexicon scored ~0.0 on (ECB rhetoric, 8-Ks, COT). Measure directional accuracy
  on the frozen `phase3_derisk/study_set.json` labels, split by doc_type.
  CONFIRMED iff non-FOMC directional accuracy > the cue lexicon's (≈0.0–0.43)
  by a margin outside per-class noise. A NULL (still ~0 on non-FOMC) is a finding:
  the ToM decode did not buy generalization on this study set, reported as
  headline.

- **H2 (grounding-weighted shift calibrates):** shifting the band by
  `base_shift × grounding_weight` (the transitive grounding read, NOT a flat
  weight) keeps magnitude calibrated vs the Phase-5 flat 0.1σ shift. Measure
  randomised-PIT KS and the scorer's tail penalty on the adapted forecaster over
  the F3-shaped units, grounding-weighted arm vs flat arm, hand-made realized
  proxy (sealed outcomes unavailable → RAW_UNRANKABLE, stated). NEUTRAL-OR-BETTER
  iff KS not worse AND tail within the Phase-5 5% tolerance. A regression is a
  finding.

- **H3 (the overconfidence guard fires):** on an ungrounded-but-confident read
  (a snippet the typer scores confidently but whose chain reaches no anchor),
  `flag_ungrounded_confident` mints a `GroundingGap` and the shift attenuates to
  ~0 — the structural version of Phase-3's "silence, not error" safety. PROVEN
  iff a constructed ungrounded-confident case mints GroundingGap and shifts <10%
  of a grounded case's shift.

## What a null means (pre-committed)

- H1 null with grounding OK → the ToM decode does not generalize past FOMC on
  real prose either; the ceiling is genuinely extraction, and the honest arm is
  rules-only-on-FOMC + silence elsewhere (Phase-3's safe floor stands).
- H0 = GENERALIZE but bigville tests break → the generalization was done wrong
  (a text-only fork, not a source-agnostic input); reject and redo. The net-win
  gate is bigville staying byte-green.

## Architecture discipline (CLAUDE.md — non-negotiable)

- NO Python decision over graph state. Every DECISION (which stance, which
  direction, commit vs abstain) is a seed RULE (Eq-join + guard) or the CAN
  marginal; Python only marshals graph in / ticks / reads out (the
  `media_analysis` annotate→codebook→rule→held_ template).
- NO new parallel text-only ToM/belief mechanism. Reuse `mint_target_concept` +
  `concept_apply_evidence` + `reasoning_can_bridge` + `actor_goals` + the
  grounding-reach read. If a seam blocks reuse, GENERALIZE the existing machinery
  (source-agnostic input), proven by bigville tests staying green.
- Frame symbols + central-bank speech-act codebook are TAUGHT data
  (`domains/teach.py`), not hand-authored rule logic.
- PREREG-then-measure; nulls are findings; proven vs assumed reported explicitly;
  no fabricated score (no ranked/normalized number is obtainable locally).

## Deliverables

- `INDUCED_BELIEF_RESULTS.md` — H0 verdict (reuse/generalize + evidence), H1
  per-doc_type directional accuracy vs the cue lexicon, H2 calibration
  before/after, H3 guard firing, proven-vs-assumed ledger.
- code under `drafts/seldon_t2_text/induced_belief/` (the arm) + any
  generalization edit to `reasoning_can_bridge` (with bigville tests re-run green).
- the arm wired into the text-arm path behind a flag, output still admissible g0–g3.

---
MEASUREMENT GATE — nothing above this line is edited once numbers exist.
