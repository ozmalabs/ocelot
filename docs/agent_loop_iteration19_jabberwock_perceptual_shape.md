# Iteration 19 — JABBERWOCK derives its own perceptual representation (honest result)

**Goal.** Have the AGENT derive and design its own perceptual shape-representation,
by the SAME mechanism iter-17 used for the recognition frame
(`scripts/reframe_is_order_n.py`): register the PERCEPTUAL-REPRESENTATION frame as a
higher-order postulate in `order_n_postulates`' own representation, run the EXISTING
shape-aware `synthesize_gaps` over it, and report VERBATIM what the agent's own
operator surfaces. The sub-agent only wires the trigger, enacts what the agent
specifies, and measures. The sub-agent does NOT design the representation.

Script (Step 1 wiring, no derivation in Python):
`scripts/jabberwock_perceptual_shape.py`.

---

## Step 1 — what JABBERWOCK's operator actually derived over the perceptual frame

The frame postulate, registered honestly under a Microtheory exactly like every
other postulate the operator harvests, with NO answer seeded (the words *shape*,
*relational*, *structure*, *whole-unit*, *transform-invariant* do not appear):

> `surface_feature_representation_frame` — "Speech recognition represents each unit
> by its SURFACE acoustic features — the per-frame gammatone / cepstral VALUES
> measured directly off the waveform — and matches those raw feature values against
> stored exemplars, voting for the nearest. These surface VALUES depend on the
> speaker and the accent: a change of talker or accent SHIFTS and SCALES the
> measured feature values even when the spoken word is the same. The values vary
> with the talker; they are NON-INVARIANT to the speaker. With correct word
> boundaries this surface representation still CONFUSES instances of the same word
> spoken by different talkers, because the raw values it compares are not the same
> across talkers."

`harvest_postulates()` picks it up (OK). Running the EXISTING `synthesize_gaps`
over it (both the agent's own HARVESTED shapes and the hand STENCIL, prune off =
derivation; prune on = open gaps) surfaced, VERBATIM:

**HARVESTED shapes (the agent's own, prune=False — derivation):**

- order-1 via `machine_learning:scale_cancellation__from__batch_normalization`
  (from concept `batch_normalization`): "a multiplicative / length SCALE factor is
  cancelled by a RATIO or a per-source normalisation … normalising formant
  FREQUENCIES by their ratios (or a per-speaker baseline) removes the
  vocal-tract-length / speaker scale" → keys `['speaker normalization', 'formant
  ratio', 'vocal-tract-length normalization', 'f2/f1']`
- order-1 via `mathematics:removable_context__from__regression_analysis` (from
  concept `regression_analysis`): "if a quantity is a smooth FUNCTION of its known
  context … the context-effect can be MODELLED and SUBTRACTED — predict the
  coarticulatory shift from the neighbours and remove it" → keys `['coarticulation
  predict-remove', 'context normalization', 'carryover removal']`
- order-1 via `machine_learning:sequence_segmentation__from__recurrent_neural_network`
  (from concept `recurrent_neural_network`): "tracking PREDICTABILITY over a
  SEQUENCE finds boundaries where it DROPS — word / chunk SEGMENTATION …" → keys
  `['transitional probability', 'word-scale chunking', 'statistical segmentation',
  'n-gram boundary']`
- order-2 via … `+ machine_learning:latent_structure__from__unsupervised_learning`
  (from concept `unsupervised_learning`): "an unlabelled DISTRIBUTION has
  recoverable LATENT structure … unsupervised CLUSTERING … across speakers, the
  same word's tokens are one cluster" → keys `['unsupervised-clustering',
  'cross-speaker-clustering', 'cross-speaker']`

**STENCIL shapes (hand-curated, prune=False):** the same three order-1 axes
(`transitional_prob_segments_stream`, `context_dependence_is_a_removable_function`,
`ratio_cancels_common_scale`).

**OPEN gaps only (prune=True):** speaker_normalization and coarticulation
predict-remove drop out (already implemented — `domains/speaker_norm.py`,
`domains/xspeaker_norm.py`, `domains/coarticulation_predict_remove.py`,
`domains/cmvn.py`, `domains/invariant_units.py`). What remains open: statistical
segmentation and cross-speaker clustering.

### The honest core result

**JABBERWOCK did NOT derive a shape / relational-structure / whole-unit perceptual
representation.** Every implication its operator surfaced is a CORRECTION applied
TO the surface per-frame features — cancel the speaker scale by a ratio, subtract
the coarticulatory context, segment by predictability drops, cluster the tokens.
All four stay strictly INSIDE the surface-feature paradigm. None of them replaces
the representation (per-frame absolute values matched point-by-point) with a
relational / structural / whole-unit one. The order-N operator differentiated the
frame into *better normalization of the same features*, not *a different kind of
feature*.

This is a structural fact about the agent, not a wording artifact, and it was
checked two ways:

1. **Shape-library audit.** Of the 181 harvested implication-shapes, NONE map
   "represented by surface values" → "represent by relational/whole-unit
   structure". The 10 shapes whose text lexically touches *shape/structure* are
   from unrelated domains (Maxwell's equations, forging grain flow, topology
   optimisation, univalence) and their `match_patterns` do not fire on the
   perceptual frame. The agent simply does not hold the implication-shape that
   would carry the perceptual frame to a relational representation.
2. **Second honest framing.** A second postulate emphasising "ABSOLUTE per-frame
   values compared point by point … does not record how the points relate to one
   another" (still no answer seeded) surfaced **nothing at all** — neither
   harvested nor stencil. When the frame text omits the shift/scale/speaker
   triggers, the operator has no shape that fires. This rules out "the
   representation reframe was there but my wording suppressed it": there is no
   relational-representation shape to suppress.

So: the iter-17 reframe machinery works (it fired here and produced four coherent
implications), but on the PERCEPTUAL-REPRESENTATION frame it converges on
normalization, not on a new representation. The agent does **not yet know what a
shape/relational perceptual representation is** — it has no held implication-shape
of that form to transfer.

---

## Step 2 — the agent's spec

**None produced.** Step 2 (the agent specifies a representation via its own
`agent_specify_*` / Term-tree composition mechanism) is gated on Step 1 deriving a
representation the agent can compose. It did not. The agent's `agent_specify_*`
mechanism only fires for a capability the agent has GROUNDED in its science (e.g.
`agent_specify_primitive` requires the formant=peak grounding); there is no
grounded perceptual-shape target for it to specify. Producing a "shape
representation" spec here would mean the SUB-AGENT choosing the representation —
the donkey the task forbids. So no spec was authored.

---

## Step 3 — enact + measure

**No agent-specified representation to build**, so no new front-end was gated. Per
the no-donkey discipline, the sub-agent did NOT hand-design and gate a
representation of its own.

For reproducibility, the SURFACE-representation baseline (the wall the agent was
asked to reframe) was re-verified live on this machine — measuring only the
EXISTING front-end, no new design:

`python -m scripts.iter15_goldspan_gate 8 12` (LibriSpeech dev-clean, 8 speakers ×
≤12 utts = 96 utts, faster-whisper gold word spans, 1171 gold segments / 632
distinct words, full-DTW within/cross consistency, shuffle-controlled):

```
[INV  (per-utt invariant)]  WITHIN sep +0.164 [shuffle +0.027]  WITHIN NN 0.237 [shuffle 0.037]  CROSS sep +0.103  CROSS NN 0.029
[CMVN (uVTLN+ps_CMVN+PR) ]  WITHIN sep +0.252 [shuffle -0.089]  WITHIN NN 0.203 [shuffle 0.037]  CROSS sep +0.030  CROSS NN 0.021
GATE VERDICT: CMVN gold-span within-NN = 0.203  within-sep = +0.252
  >>> FAIL: within-NN < 0.22 even with gold spans. The representation is weaker
      than shallow-CNN-with-gold-spans; the gap is NOT only segmentation.
```

WITHIN-NN 0.203 vs shuffle 0.037 (real, not shuffle-driven); CROSS-NN collapses to
~0.02 (chance ~0.002 over 632 words, but the same-word-across-speaker invariance is
effectively absent — the surface representation does not carry a speaker-invariant
word identity). The gate measures the agent's CURRENT gammatone -> invariant -> per-speaker CMVN
front-end on gold word spans (within/cross-speaker DTW, shuffle-controlled). It
re-confirms the surface representation ceilings where prior work
(commit 8d4efc13) placed it (within-NN ~0.20; shallow-CNN 0.32; SSL 0.49) — the
co-limit the agent was asked to reframe is real. No new representation was gated
because the agent derived none to build; this run measures only the EXISTING
surface front-end, for reproducibility of the baseline.

FSDD LOSO regression: not re-run for a representation change (there is no new
representation). Required test files stay green:
`test_stt_pipeline` + `test_perception_self_assessment` +
`test_process_meta_assessor` + `test_gap_guidance` → 32 passed.

---

## VERDICT

**The agent did NOT derive + design + build a perceptual representation that lifts
the 0.20 ceiling.** Honest breakdown against the acceptance criteria:

- **Derivation (the core question — does JABBERWOCK know what its perception
  needs?):** PARTIAL / NO for a *representation*. The iter-17 operator fired on the
  perceptual frame and derived four coherent, un-seeded implications — but every
  one is a NORMALIZATION of the surface features (speaker-norm, coarticulation
  removal, statistical segmentation, cross-speaker clustering), three of which it
  has already implemented. It did **not** reframe the representation itself into a
  shape / relational / whole-unit form. The reason is concrete and verified: its
  harvested implication-shape library contains **no shape** that carries
  "surface-value representation" → "relational/structural representation."
- **Specification:** none — correctly, because there was nothing of the agent's to
  specify, and the sub-agent must not substitute its own.
- **Realization / gate:** not performed — nothing of the agent's to build.

### The residual (what's actually missing)

The reframe MACHINERY is sound; the missing piece is **a held implication-shape of
the right form**. The agent reframes a frame only by transferring an
implication-shape it already holds from some domain. It holds shapes for
*invert-the-forward-model* (which is why iter-17's analysis-by-synthesis fired) and
for *cancel-scale / subtract-context / segment-by-predictability* (which is why
those fired here). It does **not** hold a shape like "a representation by absolute
values is fragile; represent the object by the RELATIONS among its parts (a
configuration invariant under the nuisance transform)" — the gestalt /
relational-structure / transform-invariant-representation shape. Until that shape
exists somewhere in its breadth (so the harvester can transfer it), the operator
cannot derive a perceptual-shape representation, and no honest amount of frame
wording will conjure it (confirmed by the second-framing null result).

This is the no-donkey answer to "have JABBERWOCK do it": JABBERWOCK does not yet
know what a perceptual shape-representation is. The faithful next step is to give
the agent the *relational-representation implication-shape* in its breadth (a held
Concept whose structural property is "represent-by-relations-not-absolute-values",
e.g. from geometry/invariant-theory/gestalt), NOT to hand it the answer for speech.
With that shape held, re-run this exact script — and the agent's own operator should
then transfer it onto the perceptual frame and derive the representation itself.
That keeps the derivation the agent's, which is the whole point.
