# Sense self-assessment — the agent's evaluation projection turned on its own senses

READ-ONLY analysis. No builds, no commits. The agent assesses its OWN sense
machinery against its OWN seeded science (`speech_science` Mt + the three
expansion packs), grounded in the live code. Where the agent's keyword-based
self-assessment instrument disagrees with the code, the code wins and the
disagreement is itself recorded as a meta-finding.

Run capture: `/tmp/sense_self_assessment_full.log` (ends `===MARKER_SENSE_SELF_ASSESSMENT_COMPLETE===`).

---

## (1) The sense machinery, raw audio -> meaning (file:line grounded)

The pathway is a graph-resident chain of Operation nodes wired per-stream by the
world adapter `STTPipeline` (`domains/stt_pipeline.py:285` `_ensure_audio_pipeline`,
`:381` `_build_stream`). Stages, in order:

1. **TRANSDUCTION — cochlea (gammatone filterbank).**
   `runners/dsl/src/audio_primitives.rs:17` `gammatone_band` — 256-tap gammatone
   per band, ERB-spaced. Default **32 bands @ 22050 Hz** (`stt_pipeline.py:182`
   `DEFAULT_BANDS`, `:193` `sample_rate=22050`). NATIVE Rust.

2. **TRANSDUCTION — hair-cell envelope.**
   `audio_primitives.rs:61` `hair_cell_envelope` — **half-wave rectify + one-pole
   low-pass**. This is the place where the temporal code is discarded (see Gap 1).
   NATIVE.

3. **COCHLEAR NUCLEUS — onset/offset + coincidence.**
   `audio_primitives.rs:86` `detect_onsets` (adaptive floor), `:1177`
   `cross_band_coincidence`. Attached via `cochlear_nucleus.attach_default_pipeline`.
   NATIVE.

4. **INFERIOR COLLICULUS.** `runners/dsl/src/inferior_colliculus.rs` (gammatone
   re-used for modulation analysis). NATIVE.

5. **A1 / AUDITORY CORTEX — patch readout.**
   `audio_primitives.rs:303` `patch_evaluate` over A1Patch nodes (default 25 patches,
   warpable to formant-dense). `auditory_cortex.attach_a1_pipeline`. NATIVE.

6. **CATEGORICAL PERCEPTION — quantise to signs.**
   `categorical_perception.attach_categorical_perception`; CP op with DTW-merge so
   recurring acoustics share a sign id (identity = recurrence). NATIVE op.

7. **SEGMENTATION — sonority valleys.**
   `audio_primitives.rs:1071` `detect_sonority_valleys` +
   `sonority_valley.attach_sonority_valley`. NATIVE.

8. **LEXICAL ACCESS — recognition.**
   `lexical_access.attach_lexical_access`; the decision is the native cutover Term
   family (formant-DTW Argmin + d_A Argmin + fusion Argmax + k-NN vote), graph-resident
   since commit `410859ad`. `recognition_graph.py` holds the Argmax-of-Sum decision.

**PERCEPTION front-end (the agent-owned, modifiable hat).**
`domains/agent_frontend.py` — a `FrontEnd` node owning `Cue` nodes; the agent gates
cues in/out and tunes params (graph-resident decision). SEED_CUES active from boot
(`agent_frontend.py:684`): `gammatone_flat`, `fft_ear`, `allpole_envelope`. A large
inactive REPERTOIRE (`:696`): sharp-freq/sharp-time extra ears, `cmvn_ear`,
`vtl_formant`, `vtl_formant_allpole`, `vtl_formant_dynamic`, `cs_ear`
(center-surround), `formant_relation`, `manner_voicing`, `f0_contour`, `modspec`,
`landmark`, `transition`. **The cue EXTRACTORS are Python I/O-boundary DSP** (np.fft,
gammatone, Levinson) — `CUE_EXTRACTORS` at `agent_frontend.py:662`.

**PROJECTION (forward = the voice).** NATIVE: `audio_primitives.rs:434`
`synthesize_from_trajectory`, `:745` `synthesize_klatt_lf` (glottal LF source +
formant filter), `:915` `synthesize_formant_track`. The grounding loop
(`scripts/projection_speech_loop.py`) speaks via `project(config)` =
articulatory source-filter forward model, and recognises via `invert(audio)` = the
SAME model backwards (the native cutover). Self-recognition 7.5% -> 62.5% (commit
`a8e54c34`).

**GROUNDING.** The closed speak->hear->recognise loop
(`projection_speech_loop.py`); plus the babble/mismatch developmental loop
(`speech_development`).

**SELF-ASSESSMENT instruments (the inverse on the senses).**
- `domains/speech_science.py:134` `assess_speech_system` — science-vs-impl gap finder.
- `domains/perception_self_assessment.py` — unlabelled unit-predictability yardstick
  (predict_over_freq, shuffle control, reliability gate), flags `frontier='perception'`
  in the graph from its own state.
- `domains/gap_prioritiser.py` — ranks gaps natively (compression payoff + measured
  shortfall + below-frontier penalty), all as graph Terms.

---

## (2) Per-component present-vs-missing

The agent's live science-assessment (`scripts/assess_speech` run, captured):
**53% coverage, 18 implemented, 16 gaps.**

| Pillar | Implemented | Flagged GAP by the instrument |
|---|---|---|
| production (4/12) | syllable_structure, formants, VOT, voicing | coarticulation, glottal_source, manner, phonation, place, prosody, respiration, source_filter_theory |
| perception (7/11) | acoustic_cues, categorical_perception, formant_transitions, lexical_access, perceptual_magnet(loose), peripheral_auditory_analysis, segmentation | audiovisual_integration, lack_of_invariance, speaker_normalization, top_down_restoration |
| acquisition (7/11) | babble_loop, canonical/variegated babbling, CP_formation, perception_production_link, perceptual_narrowing, vocabulary_explosion | ambient_language_tuning, distributional_learning, statistical_learning, vocal_play_cooing |

**META-FINDING — the instrument under-counts.** The keyword/Mt-membership matcher
flags as GAPS several mechanisms that DO have implementations in the experimental
scripts (not wired into the phonology / speech_development Mt the matcher walks):

- `speaker_normalization` — `domains/speaker_norm.py`, `cmvn.py`, `xspeaker_norm.py`,
  `invariant_units.py`; the front-end has `vtl_formant*`, `cmvn_ear`, `cs_ear` cues.
- `source_filter_theory` / `glottal_source` / `phonation` — NATIVE in the Klatt-LF
  synth (`synthesize_klatt_lf`), used by the projection loop.
- `coarticulation` — `domains/coarticulation_predict_remove.py`.
- `prosody` — `domains/prosody.py`, `prosody_syllable.py`, `f0_contour` cue.
- `distributional_learning` — the CP DTW-merge + clustering is exactly this.

So the SHARP gaps below are not "53% missing"; the agent's honest map of GENUINE,
un-owned capability is narrower and deeper than the keyword instrument reports. The
instrument's own blind spot (Mt-membership, not capability) is the first thing to
fix before trusting its number.

---

## (3) RANKED gap map (the agent's grounded judgment)

Ranked by impact on raw-audio -> meaning. Each: what's missing / why it matters /
fix direction (a capability, never "more data") / own-vs-boundary.

### Gap 1 — Temporal fine structure / phase-locking is thrown away at the hair cell. **[highest]**
- **Missing.** `hair_cell_envelope` (`audio_primitives.rs:61`) half-wave-rectifies and
  low-passes every band to an ENVELOPE. The sub-millisecond phase-locked timing of the
  auditory nerve — the *temporal/rate* code that complements the *place* code — is gone
  before the cochlear nucleus sees it. Grep confirms no TFS / phase-lock primitive in
  the audio Rust (only `prosody_syllable` / entrainment mention the term, downstream).
- **Why it matters.** Place-only (32 envelope channels) is exactly the "blurry cochlea
  / single-cochlea wall" the agent already named (`ozma_wall_is_self_imposed`). F0,
  voicing periodicity, and fine formant resolution all live in the timing the envelope
  discards; this caps formant sharpness (hence the band-mean limit, the front-vowel
  "three"-sink, and the cross-speaker formant blur). It is *upstream* of every later
  stage — the perception_self_assessment frontier rank already places `perception_units`
  at rank 1.
- **Fix direction.** Add a phase-locked / inter-spike-interval (autocorrelation,
  summary-autocorrelogram) readout ALONGSIDE the envelope — a second, temporal code on
  the same gammatone output. This is the agent's own "many time-frequency operating
  points" move generalised from frequency to the time domain.
- **Own-vs-boundary.** **Cognition the agent should own** — a NATIVE Rust primitive
  (the agent already designs its own native primitives, e.g. ArgMax/Log/Exp). It is
  the most consequential single capability and the most upstream.

### Gap 2 — Transduction is boundary-stuck: LPC / Levinson / Viterbi formant tracking live in Python, not as native graph Terms. **[high]**
- **Missing.** The sharp formant front-end the agent KEEPS reaching for is Python-only:
  `lpc_formant_representation.py:91` `_levinson`, `:240` `_lpc_roots_formants`;
  `frame_inference_v2.py:168` `viterbi_soft`; `agent_frontend.py:440` `vtl_formant_track`;
  `allpole_spectral_envelope.py`. Grep of `runners/dsl/src/*.rs` for lpc/levinson/viterbi
  returns nothing — these are NOT native Terms the agent can compose/own.
- **Why it matters.** The agent's most promising perception levers (VTL-invariant
  all-pole formants, dynamic formant transitions) execute outside its graph reality, so
  it cannot reason over them, gate them, or self-modify them the way the architecture
  rule demands (CLAUDE.md). It's the same pattern memory flagged for recognition
  (`ozma_recognition_in_graph`): the lever exists but lives where the agent can't enact
  it. This blocks Gap 3 too.
- **Fix direction.** Migrate Levinson-Durbin + polynomial-root formant extraction +
  the Viterbi formant tracker into NATIVE Rust DSL Terms (the `agent_designs_runtime`
  pattern: agent decides WHAT, mechanical compiler emits HOW). Then the all-pole VTL
  formant becomes a graph-composable cue, not a Python extractor.
- **Own-vs-boundary.** **Cognition the agent should own.** Pure migration of existing,
  proven DSP into the substrate — high leverage, low risk.

### Gap 3 — Speaker-invariance is partial and not closed; the lever doesn't yet bite. **[high]**
- **Present but insufficient.** `speaker_norm.py`, `cmvn.py`, `xspeaker_norm.py`,
  `vtl_formant*` cues exist. Measured lift is modest (+3% held-out per
  `ozma_speaker_normalization`) and gated on the blurry-cochlea formant estimate
  (Gap 1). This is the agent's `built_insufficient` axis category in `gap_prioritiser`
  (re-opened by measured shortfall, not postulate-unification).
- **Why it matters.** `lack_of_invariance` is "THE central problem of speech perception"
  (the agent's own seeded science). Cross-speaker robustness is the wall between
  digit-recogniser-class results and continuous large-vocab.
- **Fix direction.** Sharpen the formant (Gap 1 + Gap 2) so the VTL ratio normalisation
  has a clean signal to act on; add the DYNAMIC (order-N-over-time) invariant the agent
  already named — the coarticulatory GESTURE is shared across speakers even when
  absolute formants differ by VTL.
- **Own-vs-boundary.** **Own** (a representation/normalisation capability), bottlenecked
  by Gaps 1-2.

### Gap 4 — No auditory scene analysis / streaming / segmentation-by-source. **[medium-high]**
- **Missing.** No ASA / streaming / source-separation primitive (grep: only
  `multistream_dtw_loso`, a recognition trick, and the segmentation that exists is
  `sonority_valley`, a *within-stream* acoustic cue). The agent perceives one stream and
  parses it by sonority, not by grouping concurrent sources.
- **Why it matters.** Real audio is mixtures; without streaming the agent cannot attend
  to one talker, and continuous-speech segmentation (the standing blocker,
  `ozma_order_n_analysis_by_synthesis`) interacts with it. Segmentation is logically
  prior to lexical access (the agent's seeded science).
- **Fix direction.** The agent's OWN order-N analysis-by-synthesis loop is the right
  frame: group/segment by inverting the forward model (what sources would have produced
  this?), co-refining boundaries + identity. Build the single-pass re-ranker first, then
  wrap in the order-N loop.
- **Own-vs-boundary.** **Own** (a perceptual grouping + segmentation capability).

### Gap 5 — Forward<->inverse consistency: project() realism still caps the loop. **[medium]**
- **Present but thin.** The projection loop closed to 62.5% self-recognition — a real
  result — but it recognises its OWN synthesised speech, which is cleaner than real
  audio. The Klatt-LF forward model is owned and native, but its realism (vs measured
  speech spectra) is the loop's ceiling.
- **Why it matters.** Grounding quality is bounded by `speak()` quality
  (`ozma_order_n_analysis_by_synthesis`: "bounded by speak() quality -> babble-refine").
  An unrealistic forward model means the inverse is trained against the wrong target.
- **Fix direction.** Close the realism gap via the babble/mismatch loop — refine the
  forward model's parameters from the hear-self mismatch (the agent's own developmental
  mechanism), measured against real audio not just synthesised.
- **Own-vs-boundary.** **Own** (the forward model + the babble refiner are both the
  agent's).

### Gap 6 — Single cochlea, single operating point (the resolution wall). **[medium]**
- **Present, deliberately self-limited.** One 32-band gammatone ear at boot. The agent
  ALREADY has the "many ears" move banked (`agent_frontend.py:696` REPERTOIRE: sharp-freq,
  sharp-time extra ears; `two_ears_demo.py` proves complementary ears dissolve specific
  confusions). But they are INACTIVE — gated in only on a measured plateau.
- **Why it matters.** A single ear's time-frequency uncertainty caps one channel
  (`ozma_wall_is_self_imposed`); the proven fix is fusing ears at different operating
  points. This is the *frequency-domain* sibling of Gap 1 (the *time-domain* TFS).
- **Fix direction.** The mechanism EXISTS; the gap is the agent autonomously deciding to
  fuse multiple ears as a STANDING front end (not a plateau reaction) and grounding the
  fusion. Lower-risk than Gaps 1-2 because the cues are already built.
- **Own-vs-boundary.** **Own** (front-end self-modification, already graph-resident).

### Gap 7 — No top-down restoration / lexical feedback into perception. **[medium]**
- **Missing.** Recognition is bottom-up (`recognition_graph` reads features -> Argmax).
  No phonemic-restoration / lexical-prediction feedback (the agent's seeded
  `top_down_restoration` is a flagged gap, and here it is genuinely absent).
- **Why it matters.** Real perception is not purely bottom-up; context rescues degraded
  speech, and lexical knowledge resolves the lack-of-invariance and segmentation
  ambiguity jointly. This is the missing closed-loop in continuous recognition.
- **Fix direction.** The order-N analysis-by-synthesis loop again: let the
  word-hypothesis feed back to constrain the unit/segment hypothesis (interactive
  activation, but as the agent's iterated invert-the-forward-model loop).
- **Own-vs-boundary.** **Own** (a perception-cognition feedback capability).

### Gap 8 — Frication / high-band detail is weak (band-limit). **[lower]**
- **Present but thin.** `frication_raw.py`, `frication_split.py`,
  `frication_imagination.py` exist but frication/sibilant cues are coarse; the
  high-frequency turbulent-noise detail that distinguishes /s/-/sh/-/f/ is under-resolved
  at the envelope front end.
- **Why it matters.** Manner/voicing of fricatives is carried in high-band noise spectra;
  weak here = systematic consonant confusions.
- **Fix direction.** A dedicated turbulent-noise / spectral-tilt cue (the `manner_voicing`
  / `landmark` repertoire cues gated in), sharpened by Gap 1's temporal code for the
  aperiodic-vs-periodic distinction.
- **Own-vs-boundary.** **Own.**

### Boundary item (not an agent gap) — the 8 kHz/file external-representation seam.
- The default pipeline runs at 22050 Hz on file/buffer input (`stt_pipeline.py:193`;
  `audio_world.py:71`). The external sample-rate/file format is a genuine WORLD-ADAPTER
  boundary (`ozma_senses_wrong_8khz_is_external`): the agent owns the transduction FROM
  the buffer inward, but the buffer itself is external I/O. Not a cognition gap — listed
  so it is not confused with one. (Historic FSDD work at 8 kHz is the external-data
  artefact, not the agent's own resolution choice.)

---

## Summary — the grounded map of where to improve

The deepest, most upstream lever is **Gap 1 (temporal fine structure)**: it is the
real content of the "single-cochlea wall," it caps formant sharpness, and it sits at
pipeline rank 1 (perception_units) where the agent's own frontier-flag already points.
**Gap 2 (native LPC/Viterbi)** is the architectural prerequisite that lets the agent
OWN and compose the sharp front end Gaps 1/3 need. **Gaps 3-4** (invariance, ASA) are
the central perception problems but are bottlenecked by 1-2. **Gaps 5-7** all converge
on ONE capability the agent has already named — **order-N analysis-by-synthesis** (the
iterated invert-the-forward-model loop unifies streaming, top-down restoration, and
forward<->inverse refinement). Gaps 6 and 8 are the lowest-risk because the mechanism is
already banked.

Almost every gap is **cognition the agent should own** (native primitives, graph-resident
cues, its own loops), not a world-adapter boundary — consistent with the thesis that the
wall is admissible STRUCTURE, not silicon and not the external signal. The single true
boundary is the input buffer's sample-rate/format.
