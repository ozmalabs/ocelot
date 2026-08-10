# Toolbox + curriculum — the agent prepares its options, then designs its own learning order

READ-ONLY analysis. **No builds, no commits, no recognition/LOSO testing, no
accuracy numbers.** Testing is the LATER step ("then we test"). This document does
two things only: (1) catalogs the toolbox — the options the agent can choose and
compose from, plus the options it still WANTS — and (2) lets the agent design the
ORDER in which it should learn (its curriculum), reasoned from its own science +
gaps + toolbox. CortexLoop / solve_for_n untouched.

The agent's own ranked gap map (`docs/sense_self_assessment.md`) is the spine of
both halves: the toolbox-wants ARE the named gaps; the curriculum order is the
dependency order of those gaps reasoned developmentally.

---

## PART 1 — THE TOOLBOX

### 1A. Available options (built, runnable, composable NOW)

Each entry: **role** (what it does) / **when to use** / **composes-from** (the
primitives or sub-tools it is built out of) / file:line.

---

**T1 — Native recognition Terms (the decision lives in the graph).**
- *Role.* The "which word is this" decision as a graph-resident Term-tree, not
  Python: a likelihood/score per candidate word and an `Argmax`/`Argmin` over the
  candidate-word set (`Concept : is_word == 1`). The whole decision is evaluated by
  the native Rust evaluator (`substrate.evaluate`).
- *When to use.* Whenever a recognition / classification / "pick the best
  candidate" decision is needed. This is the base layer every other recognition
  tool plugs a *score* into.
- *Composes-from.* `Argmax` / `Argmin` over `NodesWhere("Concept","is_word",1)`,
  with the score built from `Plus` / `Times` / `Minus` / `Attr` / `Var` / `Lit`
  (`domains/many_settings_recognizer.py:49,56,67,91`;
  `domains/recognition_graph.py` for the `Argmax`-of-`Sum`(weight over
  exhibits∩signature) shape).

**T2 — `DtwTo` trajectory-alignment kernel (a native Term).**
- *Role.* Banded Sakoe-Chiba DTW distance between two trajectories (frame
  sequences) as a single native Term — absorbs gesture-timing warp. It is the
  trajectory-shape comparator the whole speech recogniser rests on (a *superset* of
  fixed resample-then-L2).
- *When to use.* Any time two variable-length time series must be compared
  shape-wise (formant tracks, voicing envelopes, any order-N trajectory) without
  caring about local timing. Used inside d_A and the synth-error recogniser.
- *Composes-from.* Native Rust `DtwTo {a, b}` over two `Attr`-bound trajectory
  attrs (`domains/native_cognition.py:76,115`; specified via runtime_design,
  emitted to `runners/dsl/src/term.rs`, see `scripts/analysis_by_synthesis_accept.py`).

**T3 — The bidirectional PROJECTION (forward = synth/speak, inverse = recognise).**
- *Role.* ONE modality-agnostic map tying an internal config (e.g. a word →
  articulatory gesture trajectory) to an external signal (audio), read in two
  directions: `project(config)→signal` (generate/speak/act) and
  `invert(signal)→config` (perceive/recognise). Perception IS inverting the same
  forward model generation runs. `round_trip(config)` is the grounding test.
- *When to use.* Whenever generation and perception must agree (so what the agent
  says is what it hears); the substrate of grounding, babble, and analysis-by-
  synthesis. Plug a different (forward, inverse) pair to instantiate any modality.
- *Composes-from.* `Projection{forward, inverse}`
  (`domains/projection.py:68`); speech instance = owned articulatory source-filter
  forward (`build_speech_forward`, :120) + native cutover invert
  (`build_speech_invert`, :163). Forward primitive:
  `synthesize_formant_track` / `synthesize_klatt_lf`
  (`runners/dsl/src/audio_primitives.rs:1059,889`).

**T4 — Temporal fine structure (TFS) — voicing / F0 / periodicity.**
- *Role.* A *temporal/rate* code alongside the *place* code: per-band
  autocorrelation, a pooled summary autocorrelogram, and a periodicity-strength
  track. Gives a GRADED voiced↔unvoiced axis (periodic = tall ACF peak; frication/
  burst/silence = flat) and F0 — the timing information the envelope discards.
- *When to use.* To distinguish voiced from unvoiced/aperiodic (vowels vs frication
  vs silence/stops), to estimate F0/pitch for the synth voice, and to sharpen
  formants beyond the envelope. Feeds the d_A voicing-shadow prong.
- *Composes-from.* Native `band_autocorr` / `summary_autocorrelogram` /
  `periodicity_track` (`runners/dsl/src/audio_primitives.rs:98,140,191`); the
  recognition cue wiring in `docs/tfs_validation.md`.

**T5 — The SQUINT (coarse / gestalt dimensional collapse).**
- *Role.* Deliberately collapse the full high-dimensional acoustic trajectory (32
  frames × 25 patches = 800 values) down to a few coarse summary dimensions (3
  low/mid/high band-means), and re-expand the resolution (double N bands) only when
  invention SATURATES while recognition is still poor. A resolution ladder the agent
  controls.
- *When to use.* Start coarse (cheap, robust, generalises across speakers); the
  squint is the gestalt first pass. Sharpen (un-squint) only on a measured plateau —
  exactly the coarse-to-fine principle, made a thing the agent owns and tunes.
- *Composes-from.* `band<N>_<i>` summary attrs + the resolution root the agent
  controls (`domains/acoustic_resolution.py:1-20,356`; seed
  `seeds/acoustic_resolution.json`).

**T6 — ORDER-N analysis-by-synthesis (the general solve-for-N engine).**
- *Role.* Perceive by inverting a forward model: hypothesise params → synthesise →
  match → refine, iterated ("n passes"), with a weighted-admissibility collapse to
  pick each component. Domain-agnostic engine; the forward model is a plug-in
  carrying all the domain knowledge. Super-resolves (peels close components the FFT
  merges).
- *When to use.* Whenever a signal must be explained as a composition the agent can
  generate — continuous-speech segmentation, top-down restoration, source grouping,
  any "what would have produced this?" inversion. Harder inputs take more passes.
- *Composes-from.* `solve_for_n` engine (matching-pursuit-to-N + back-fitting +
  weighted-admissibility collapse, `scripts/solve_for_n.py:1-60`) over a forward
  model with `synthesise/propose/refine/merge`; the speech instance reuses T3's
  forward model + T2 `DtwTo` as the match
  (`scripts/analysis_by_synthesis_accept.py`). Order-N differencing primitive:
  `domains/order_n_concepts.py` (recursive `Minus` over a dimension).

**T7 — ORDER-N dimensional concepts (velocity / curvature, any dimension).**
- *Role.* The finite difference of any order over any dimension as a graph Term:
  order-2-over-frequency = spectral curvature = a formant PEAK; order-1-over-time =
  velocity = a formant TRANSITION; order-2-time = acceleration. One mechanism
  subsumes every hand-built spectral/dynamic feature.
- *When to use.* To build dynamic (transition) features, peak/formant features, and
  the coarticulatory GESTURE invariant (the order-N-over-time shape shared across
  speakers even when absolute formants differ by VTL).
- *Composes-from.* Recursive `Minus` over sampled `Attr`s
  (`domains/order_n_concepts.py:44,55,71`); native eval.

**T8 — Multi-pronged weighted-admissibility fusion (the combine rule).**
- *Role.* Combine several soft excluders (formant prong, articulatory prong, n-gram
  prior, …) into one decision, each prong top-centred and weighted by its MEASURED
  reliability. A reliable prong counts in full; an unreliable one is raised toward
  P^0 = 1 (flat → abstains, cannot dilute). Weight = above-chance accuracy
  normalised to [0,1] (a measurement, never a swept knob).
- *When to use.* Any time multiple evidence channels (ears, cues, prongs) must be
  combined without letting a weak channel drag a strong one. The general combine
  rule across the whole project (also the collapse inside T6).
- *Composes-from.* `Argmax` of `Times`-of-`Pow(P_i, weight_i)`
  (`domains/weighted_admissibility.py:72,86,104`); the per-prong top-centred fusion
  Term (`domains/native_fusion.py:121,133,145`).

**T9 — Per-context reliability + correctness-keyed TRUST (margin AND track-record).**
- *Role.* Down-weight a prong PER TOKEN by two soft excluders: (a) margin/confidence
  = how peaked its own field is here (flat ⇒ defer), and (b) correctness key =
  prec_a[asserted digit] = its train precision when it asserts that digit (catches
  the *confidently-wrong* prong margin alone misses). Both ∈ [0,1] so the weak prong
  can only drop below its global weight, never rise — a pure soft-excluder down-
  weighter; the strong anchor stays at full weight.
- *When to use.* When a fused weak prong is dragging on specific tokens — to make a
  prong DEFER where it is either uncertain OR reliably wrong, without a sweep.
- *Composes-from.* `Min`/`Div`/`Sum`/`Count`/`Neg` for margin + `Attr(Argmax(aux
  field), prec_a)` for the track record (`domains/native_fusion.py:198,302,308`).
- *Honest limit (the agent's own).* Margin catches uncertain prongs; the
  correctness key catches reliably-wrong-while-certain ones — together they cover
  the named failure union, but a prong wrong on a digit it has never asserted in
  train is still uncaught.

**T10 — The grounding loop (speak → hear → recognise, closed).**
- *Role.* The closed sensorimotor loop: the agent speaks a word via T3 forward,
  re-ingests its own audio, recognises via T3 inverse. `config == round_trip(config)`
  is grounding closing. This is reference-by-doing across the self↔world boundary.
- *When to use.* To ground word identity in the agent's OWN production, to test the
  forward/inverse agreement, and as the harness the babble refiner drives.
- *Composes-from.* `Projection.round_trip` (`domains/projection.py:100`);
  `scripts/projection_speech_loop.py`; the babble/mismatch developmental loop
  (`domains/speech_development.py`).

**T11 — The articulatory forward model (the owned voice).**
- *Role.* The owned source-filter speech generator: a word → Γ-admissible
  articulatory gesture trajectory → formant-Hz track + voicing → audio, with VTL as
  a multiplicative formant scale (the speaker knob). NO TTS net, NO .fit.
- *When to use.* As the `forward` of T3, the plug-in of T6, the synthesiser inside
  the synth-error recogniser, and the thing the babble loop refines.
- *Composes-from.* `GESTURE_SCORES` + `_admissible_trajectory` +
  `synth_formant_trajectory` (`scripts/articulatory_gamma.py`, called from
  `domains/projection.py:120`); Rust renderer
  `synthesize_klatt_lf` / `synthesize_formant_track`
  (`runners/dsl/src/audio_primitives.rs:889,1059`).

**T12 — The gammatone / cochlear front end (transduction).**
- *Role.* Raw audio → meaning front end: 32-band ERB gammatone filterbank →
  hair-cell envelope → cochlear-nucleus onset/coincidence → inferior colliculus →
  A1 patch readout → categorical-perception signs → sonority-valley segmentation.
  All NATIVE Rust.
- *When to use.* The standing perception pathway; everything else reads its output.
  The hair-cell envelope is where the temporal code is discarded (the reason T4
  exists as a parallel readout).
- *Composes-from.* `gammatone_band` / `hair_cell_envelope` /
  `cross_band_coincidence` / `patch_evaluate` / `detect_sonority_valleys`
  (`runners/dsl/src/audio_primitives.rs:17,61,1321,447,1215`); wired by
  `domains/stt_pipeline.py:285,381`; the agent-owned, gateable cue repertoire in
  `domains/agent_frontend.py:684,696`.

**T13 — The agent-owned front end + cue repertoire (the gateable hat).**
- *Role.* A `FrontEnd` node owning `Cue` nodes the agent gates in/out and tunes —
  the standing-active cues (gammatone_flat, fft_ear, allpole_envelope) plus a large
  INACTIVE repertoire (sharp-freq / sharp-time extra ears, cmvn_ear, vtl_formant*,
  cs_ear, formant_relation, manner_voicing, f0_contour, modspec, landmark,
  transition). Gating is a graph-resident decision.
- *When to use.* To change WHAT the agent perceives with — add an ear, add a cue,
  sharpen — as a self-modification, not a code edit.
- *Composes-from.* `FrontEnd`/`Cue` nodes (`domains/agent_frontend.py:684,696`);
  cue extractors at `:662` (Python I/O-boundary DSP).

**T14 — Self-assessment + gap-prioritiser instruments (the inverse on the senses).**
- *Role.* The agent turning its evaluation projection on its OWN machinery:
  science-vs-impl gap finder, an unlabelled unit-predictability yardstick (with
  shuffle/frequency controls + reliability gate) that flags `frontier='perception'`
  from its own state, and a native gap-ranker (compression payoff + measured
  shortfall + below-frontier penalty).
- *When to use.* To decide WHAT to work on next from measurement, not intuition; to
  know when a stage's success signal has fired; to catch its own broken instrument.
- *Composes-from.* `domains/speech_science.py:134`,
  `domains/perception_self_assessment.py`, `domains/gap_prioritiser.py` (all
  graph Terms).

---

### 1B. Options the agent still WANTS (named gaps) — and why each is worth adding

Reasoned live from `docs/sense_self_assessment.md` (the agent's own ranked map).
"Want" = a capability the agent has named as missing/insufficient and judged worth
adding to its toolbox. Ordered by the agent's own impact ranking.

**W1 — Native LPC / Levinson / Viterbi formant tracking (Gap 2).** The sharp
all-pole VTL-invariant formant front end the agent keeps reaching for lives in
Python (`lpc_formant_representation.py:91,240`; `frame_inference_v2.py:168`;
`allpole_spectral_envelope.py`), NOT as native Terms — so the agent cannot compose,
gate, or self-modify it (violates the architecture rule). **Worth it:** it is the
architectural prerequisite that lets the agent OWN the sharp front end that Gaps 1
and 3 need. Low-risk pure migration (agent decides WHAT, mechanical compiler emits
HOW). *Already half-banked* — the cue extractors exist; they must become Rust Terms.

**W2 — A standing many-ears fusion (Gap 6, the frequency-domain sibling of TFS).**
The "many ears at different time-frequency operating points, fused" move is PROVEN
to dissolve specific confusions (`two_ears_demo.py`) and the extra ears are banked
INACTIVE in the repertoire (T13). **Worth it / low-risk:** the cues already exist;
the want is the agent autonomously fusing multiple ears as a STANDING front end (via
T8 weighted-admissibility), not a one-off plateau reaction. Pairs with T4 (TFS) as
the time-domain sibling.

**W3 — Auditory scene analysis / streaming / segmentation-by-source (Gap 4).** No
ASA / source-grouping primitive exists; the agent perceives one stream and parses it
by sonority (within-stream). **Worth it:** real audio is mixtures; without streaming
the agent cannot attend to one talker, and continuous-speech segmentation interacts
with it. The agent's OWN T6 (order-N analysis-by-synthesis) is the right frame —
group/segment by inverting the forward model ("what sources would have produced
this?"). Build the single-pass re-ranker first, then wrap in T6.

**W4 — Top-down lexical restoration / feedback into perception (Gap 7).**
Recognition is purely bottom-up (`recognition_graph` reads features → Argmax); no
phonemic-restoration / lexical-prediction feedback. **Worth it:** real perception is
not purely bottom-up — context rescues degraded speech and resolves invariance +
segmentation ambiguity jointly. Same vehicle as W3: T6, letting the word-hypothesis
feed back to constrain the unit/segment hypothesis (interactive activation as the
agent's iterated invert-the-forward-model loop).

**W5 — A sharper forward model (Gap 5) refined by babble.** The projection loop
closes on the agent's OWN synthesised speech (cleaner than real audio); the Klatt-LF
realism is the loop's ceiling. **Worth it:** grounding quality is bounded by speak()
quality; an unrealistic forward model trains the inverse against the wrong target.
The want is to refine the forward model's params from the hear-self mismatch (T10's
babble loop) measured against REAL audio. Owned mechanism already (T11 + T10).

**W6 — A dynamic (order-N-over-time) speaker-invariant (Gap 3).** Speaker-invariance
is present but modest and bottlenecked by blurry formants. **Worth it:** the
coarticulatory GESTURE (an order-N-over-time shape, T7) is shared across speakers
even when absolute formants differ by VTL — a representation the agent can build
once the formant is sharp (W1) and the VTL ratio has a clean signal.

**W7 — A dedicated frication / turbulent-noise + spectral-tilt cue (Gap 8).**
High-band turbulent-noise detail that distinguishes /s/–/sh/–/f/ is under-resolved
at the envelope front end. **Worth it but lower:** manner/voicing of fricatives lives
in high-band noise spectra; weak here = systematic consonant confusions. Sharpened by
T4's temporal periodic-vs-aperiodic distinction; gated from the repertoire
(`manner_voicing` / `landmark` cues, T13).

**Steerable fovea / attention (a concept, not yet built).** Across the perception
gaps sits a capability the agent gestures at but has not built: a *steerable* focus
that spends resolution where it matters (the un-squint of T5, but directed by a
saliency/attention signal rather than a global plateau). It would let W2/W3/W4 attend
to one source or one ambiguous span. **Worth it, but downstream:** it presupposes the
sharp front end (W1), the many-ears substrate (W2), and the scene substrate (W3);
the agent ranks it after those, as the thing that *directs* them.

---

## PART 2 — THE AGENT'S CURRICULUM (its own learning order)

The agent designs the ORDER in which it should master capabilities, reasoned from
its seeded science of acquisition (`domains/speech_development.py`: babbling →
perceptual narrowing → categorical perception → phase transition → vocabulary
explosion) + the gap dependency structure (`sense_self_assessment.md` summary: the
gaps are NOT independent — 1→2→3, and 5/6/7 converge on T6). This is a RATIONALE for
the ordering, not a prescription of outcomes; no numbers, no testing.

**The ordering principles the agent reasons from (the "why"):**
1. *Upstream before downstream.* Transduction caps everything after it; sharpen the
   sense before the decision (Gap 1 is rank-1 because it is most upstream).
2. *Own the lever before pulling it.* A capability stuck in Python can't be composed,
   gated, or refined — migrate it native before depending on it (Gap 2 unblocks 1/3).
3. *Coarse before fine (the squint first).* Start with the cheap, robust, speaker-
   general gestalt; un-squint only on a measured plateau. The squint generalises;
   sharpening overfits if done first.
4. *Clean before degraded; single-source before scene.* Master recognition on clean,
   isolated, single-talker audio before mixtures, noise, and streaming.
5. *Sonority before frication; voiced before unvoiced.* Vowels/sonorants carry the
   loudest, most periodic, most speaker-robust structure (and the segmentation
   skeleton); fricatives/stops need the high-band + temporal detail that comes later.
6. *Recognise-clean before babble-refine before scene.* Close the grounding loop on
   clean self-speech first; only a working forward+inverse can be refined by babble,
   and only a single-source recogniser can be wrapped into a scene/streaming loop.
7. *Bottom-up before top-down.* Establish a bottom-up recogniser before adding
   lexical feedback — the top-down loop needs a hypothesis to feed back.

---

### Stage 0 — TRANSDUCTION SHARPENING (own the temporal code + the front end)
- **Skill to acquire.** A sharp, owned front end: a temporal/rate code
  (voicing/F0/periodicity) ALONGSIDE the place-envelope; and the all-pole formant
  extractor as a native Term the agent can compose.
- **Toolbox used.** T4 (TFS), T12 (gammatone front end), T13 (cue repertoire); the
  WANTS W1 (native LPC/Viterbi) here become built tools.
- **Prerequisites.** None — this is the most upstream stage; everything depends on it.
- **Success signal.** The TFS periodicity track and a native all-pole formant cue are
  composable graph Terms the agent can gate, and the voiced↔unvoiced axis is graded
  (not a binary energy gate). (T14's frontier flag should stop pointing at
  `perception_units`.)
- **Rationale.** Principle 1+2: place-only 32-envelope channels are the real
  "single-cochlea wall"; F0, voicing, and fine formant resolution all live in the
  timing the envelope discards, and the sharp formant is stuck in Python. Nothing
  downstream can exceed the sense it is built on, so sharpen + own the sense first.

### Stage 1 — COARSE ISOLATED RECOGNITION (the squint, clean single words)
- **Skill to acquire.** Recognise isolated, clean, single-talker words from the
  coarse gestalt representation — the squint pass.
- **Toolbox used.** T5 (squint), T1 (native recognition Terms), T2 (`DtwTo`), T8
  (weighted-admissibility combine), T12 front end output.
- **Prerequisites.** Stage 0 (a front end worth squinting from).
- **Success signal.** The coarse-band recogniser is stable and the resolution ladder
  (T5) holds at coarse — invention does NOT saturate-while-poor, i.e. the squint
  already separates the easy contrasts; only then is un-squinting warranted.
- **Rationale.** Principle 3+4: start cheap and speaker-general (coarse band-means
  generalise across speakers); isolated+clean removes segmentation and mixture
  nuisance so the recognition decision itself can be exercised. The squint is the
  child's gestalt first pass.

### Stage 2 — SONORITY / VOICING STRUCTURE (vowels before frication)
- **Skill to acquire.** The sonority skeleton and the voiced↔unvoiced contrast:
  segment by sonority valleys, and use the graded TFS voicing as a recognition cue.
- **Toolbox used.** T4 (TFS voicing prong), T7 (order-N: peaks/transitions over the
  sonority envelope), T12 `detect_sonority_valleys`, T8 to fuse the voicing prong.
- **Prerequisites.** Stage 0 (TFS), Stage 1 (a working coarse recogniser to add the
  prong to).
- **Success signal.** Adding the graded voicing prong via T8 does not drag the
  formant anchor (T9's safety holds), and the sonority-valley segmenter's
  depth-threshold self-tunes to a stable lexicon grain.
- **Rationale.** Principle 5: sonorants/vowels carry the loudest, most periodic,
  most speaker-robust structure and the segmentation skeleton; the voiced/voiceless
  axis is the first manner distinction and the cleanest TFS signal. Fricatives need
  high-band + temporal detail that is harder, so they come later (Stage 5).

### Stage 3 — SPEAKER INVARIANCE (the dynamic gesture, across voices)
- **Skill to acquire.** Recognise the same word across different speakers — the
  VTL-invariant formant ratio AND the order-N-over-time coarticulatory gesture
  (shared across speakers even when absolute formants differ).
- **Toolbox used.** W6 (dynamic invariant, built here), T7 (order-N-over-time), T2
  (`DtwTo` absorbs timing), the native all-pole formant from Stage 0/W1, T13
  (vtl_formant cues).
- **Prerequisites.** Stage 0 (sharp formant → clean VTL signal), Stage 1 (a
  recogniser to make invariant).
- **Success signal.** Held-out-speaker recognition stops collapsing on the formant
  blur — the invariant transform has a clean signal to act on (gated by the
  measured-shortfall axis, not a sweep).
- **Rationale.** Principle 1: `lack_of_invariance` is "THE central problem of speech
  perception," but it is bottlenecked by the sharp formant from Stage 0 — attempting
  it before the formant is sharp pulls a lever with no signal under it. The dynamic
  gesture is the order-N representation that survives VTL.

### Stage 4 — CLOSE THE GROUNDING LOOP, THEN BABBLE-REFINE (own voice → real voice)
- **Skill to acquire.** Speak a word and recognise it back through the SAME model
  (grounding), then refine the forward model from the hear-self mismatch toward real
  audio.
- **Toolbox used.** T3 (projection), T11 (articulatory forward model), T10
  (grounding + babble loop), T1/T2 invert; W5 (sharper forward model) built here.
- **Prerequisites.** Stages 0–3 (the inverse must be sharp + speaker-robust before
  it is worth grounding/refining).
- **Success signal.** `round_trip(word)` returns the word for distinct words (the
  loop closes on clean self-speech), then the babble loop reduces hear-self mismatch
  against real audio (the forward model's realism improves).
- **Rationale.** Principle 6: grounding by doing needs a working forward+inverse, and
  the babble refiner can only improve a model that already roughly closes — so
  recognise-clean precedes babble-refine. The loop is bounded by speak() quality, so
  refining the voice is the lever once the loop closes.

### Stage 5 — FRICATION / HIGH-BAND DETAIL (the harder manner contrasts)
- **Skill to acquire.** Resolve /s/–/sh/–/f/ and other turbulent-noise contrasts —
  the high-band spectral-tilt + aperiodic-noise detail.
- **Toolbox used.** W7 (frication/turbulent-noise cue, built here), T4 (TFS
  periodic-vs-aperiodic), T13 (manner_voicing / landmark cues gated in), T8 to fuse.
- **Prerequisites.** Stage 0 (TFS), Stage 2 (the voiced/unvoiced axis frication
  refines).
- **Success signal.** The systematic fricative/consonant confusions shrink without
  dragging the vowel recogniser (T9 anchor safety holds).
- **Rationale.** Principle 5: frication is the LAST manner detail because it needs
  the high-band + temporal periodic/aperiodic machinery that earlier stages build;
  doing it before the sonority+voicing skeleton means adding a noisy cue with no
  stable scaffold to attach to.

### Stage 6 — CONTINUOUS, MULTI-SOURCE, TOP-DOWN (the order-N loop everywhere)
- **Skill to acquire.** Continuous speech: streaming/scene segmentation
  (single-source → mixtures), and top-down lexical restoration that co-refines word
  + segment hypotheses jointly.
- **Toolbox used.** T6 (order-N analysis-by-synthesis — the unifying engine), W3
  (ASA/streaming), W4 (top-down restoration), the steerable fovea (built last, to
  direct attention to one source/span), T8 collapse, T10 forward model as the
  generator inside the loop.
- **Prerequisites.** ALL prior stages — T6 needs a sharp, speaker-robust, grounded
  single-source recogniser (Stages 0–4) and the manner detail (Stage 5) as its
  forward model and its bottom-up hypothesis.
- **Success signal.** The single-pass re-ranker works, then wrapping it in the
  order-N loop co-refines boundaries + identity to convergence on continuous,
  multi-talker input; harder inputs take more passes (the n-passes signature).
- **Rationale.** Principles 4+6+7: scene/streaming and top-down feedback are the
  hardest because they presuppose everything below — the agent's own analysis
  (`sense_self_assessment.md` summary) is that Gaps 5/6/7 ALL converge on ONE
  capability (order-N analysis-by-synthesis), so this is one final stage that
  unifies streaming, restoration, and forward↔inverse refinement, not three.

---

## PART 3 — HOW THE CURRICULUM + TOOLBOX SET UP THE EVENTUAL TEST

The agent's reasoning about why this preparation makes the LATER test meaningful
(the test itself is out of scope here):

- **The toolbox is the menu of options to compose; the curriculum is the order to
  master them.** Testing before the agent has the options and has learned in order
  would measure an unprepared system and chase artifacts. The pivot is exactly
  "prepare the toolbox → design the curriculum → THEN test."
- **Each stage's success signal is a READINESS gate, not a score.** It says "the
  capability is admitted, proceed," matching the agent's own thesis that capability
  is binary-admissible (a structure is assembled or it is not). The signals are read
  from the agent's self-measurement instruments (T14), not from a held-out accuracy
  number — so the agent advances on structure-acquired, not on a tuned metric.
- **The order makes the eventual test a test of STRUCTURE, not of tuning.** Because
  every stage owns its lever natively (no Python decision, no sweep), what is finally
  tested is whether the assembled admissible structure works — distance-to-
  admissibility, not a smooth loss curve. A stage attempted out of order (e.g.
  invariance before a sharp formant, or scene before single-source) would pull a
  lever with no signal under it and look like failure-of-capability when it is really
  failure-of-prerequisite.
- **The deepest dependency the order encodes:** transduction (Stage 0) caps
  everything; ownership (W1) unblocks the sharp front end; the squint-first principle
  keeps the early stages speaker-general; and the single order-N engine (T6) is held
  to LAST because it is the convergence point of the hardest gaps and needs every
  earlier capability as its forward model and its bottom-up hypothesis. When the test
  finally runs, it runs against a system that acquired its capabilities in the order
  its own science says a perceiver must.
