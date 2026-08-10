# Re-mining ASR/speech methods as candidate NODES for the recognition graph

> Step-back harvest triggered by the user: "RE-MINE existing ASR/speech software +
> literature for ALL their methods — as candidate NODES for the recognition graph."
> The strategic frame (iter-32→36): the recognition is a **GRAPH** — a variadic
> Argmax-of-product (combinatorial Bayes product) over per-cue likelihood nodes
> (`domains/many_settings_recognizer.predict_many_settings_term`). So we do **NOT
> choose between methods** (that is pipeline thinking) — we **combine them all**.
> Every front-end / feature / transform the field built is a candidate node; in the
> product a node uninformative for a contrast multiplies in near-flat (cannot hurt)
> and a complementary one widens the win + the shuffle margin. iter-34/36 proved the
> richness lever is monotone **only for genuinely ORTHOGONAL cues** — so the harvest's
> value is **orthogonality to what the agent already has**, not raw accuracy.
> **No build, no commit.** Harvest only.

---

## 0. What the agent ALREADY has (the baseline to be orthogonal to)

Read from the code, not the docs, so the orthogonality ranking is exact:

| Agent cue | Module | What acoustic info it captures | Time-freq operating point |
|---|---|---|---|
| **Gammatone cochleagram × 5 settings** | `filter_settings.cochleagram` + `COCHLEAR_SETTINGS` | broadband **energy envelope** per ERB band, log-spaced 80–7500 Hz, at 5 points on the uncertainty tradeoff (sharp-time…sharp-freq) | fine TIME / coarse FREQ (gammatone) → spread |
| **FFT-ear** | `filter_settings.fft_ear` | **fine-frequency** log-magnitude spectrum, 40 log bands 150–3800 Hz × 3 coarse temporal windows | fine FREQ / coarse TIME |
| **Formant-relation** | `lpc_formant_representation.formant_spacings_from_audio` | **LPC pole spacings** (F_i−F_j), VTL-invariant vocal-tract resonance *relations* | spectral-envelope shape (all-pole) |
| **Manner/voicing** | `stacked_representation._manner_voicing_channel` | autocorrelation **periodicity** + voiced/sonorant/sibilant predicates + low/mid/high **band-energy balance** per frame | source + gross spectral balance |
| **Transition** | `filter_settings.transition_multiwindow` | **order-1-over-time** of the patch trajectory at n∈{2,3,4} windows (formant onset/sweep) | temporal derivative |
| **Single-pass AxS** | iter-35 node | **top-down** synthesis-match (invert `speak()`, one pass, no fit) | generative residual |

**The information already covered:** energy envelope (gammatone), fine static
spectrum (FFT-ear), vocal-tract resonance *relations* (formant), voicing/source +
gross manner (manner/voicing), first-order temporal change (transition), top-down
generative match (AxS).

**The information demonstrably MISSING (the gaps the harvest must fill):**
- **F0/pitch CONTOUR as an explicit cue** (the agent has binary voicing via
  periodicity, but not the *pitch track* — and on tonal/prosodic/cross-speaker
  cases this is a separable channel).
- **Modulation / envelope-RHYTHM spectrum** (the 2–8 Hz syllabic temporal-modulation
  axis — Goswami's rise-time axis named in `research_speech_deficits.md` as missing).
- **Spectral SHAPE descriptors that are not envelope/peak** (centroid, slope,
  tilt, contrast peak-vs-valley, rolloff) — the agent reads *peaks* (formants) and
  *band energy*, never the harmonic-vs-noise *contrast* or the global *tilt*.
- **Noise/channel-ROBUST front-ends** (PNCC, RASTA) — the agent has no
  degradation-invariance node (the APD gap).
- **A genuinely DIFFERENT frequency-geometry front-end** (CQT: constant-Q,
  log-frequency, octave-equivariant) — the agent has linear-window FFT + ERB
  gammatone, both fixed-resolution.

---

## 1. The harvested method inventory (front-ends / features / transforms)

Mined from the standard ASR/speech-feature corpus: Kaldi, librosa, openSMILE,
HTK, Praat, the classic robust-ASR line (CMU PNCC, RASTA-PLP), and the SSL line.
For each: what acoustic information it captures, and the citation.

### 1A. Front-ends (whole-signal → time-frequency representation)

| Front-end | What it captures | Cited |
|---|---|---|
| **MFCC** | mel-band log-energy → DCT-decorrelated cepstrum; smooth **spectral envelope**, compact | standard (HTK/Kaldi/librosa) |
| **PLP** | perceptually-warped (Bark) + equal-loudness + intensity-loudness power-law + all-pole (LPC) smoothing → **perceptual spectral envelope** | Hermansky 1990 |
| **RASTA-PLP** | PLP with each log-band **band-pass filtered (1–16 Hz modulation)** → suppresses steady-state / slow channel + convolutional distortion; keeps the **relative spectral change** | [RASTA processing of speech](https://www.researchgate.net/publication/3333372_RASTA_processing_of_speech); modulation 1–16 Hz, high-pass removes convolutional channel offset |
| **GFCC** | **gammatone** filterbank → loudness-compressed (cube-root) → DCT cepstrum; like the agent's cochleagram but cepstral/decorrelated | standard robust-ASR |
| **PNCC** | gammatone + **medium-time power** running average + **asymmetric noise-suppression filter** + temporal masking + **power-law (not log) nonlinearity** → strong **noise robustness** (beats MFCC 55%, RASTA-PLP 47% at 5 dB subway noise) | [PNCC, Kim & Stern](https://www.cs.cmu.edu/~robust/Papers/OnlinePNCC_V25.pdf) |
| **CQT** (constant-Q) | **log-frequency**, constant-Q (octave-equivariant) resolution: fine freq at low f, fine time at high f — a *different* time-freq geometry than linear FFT or ERB gammatone | standard (librosa) |
| **Wavelet / scattering transform** | cascade of wavelet-conv + modulus + low-pass; **locally time-shift invariant + stable to time-warping**; 2nd order recovers **amplitude-modulation / transient** structure lost by mel averaging | [Andén & Mallat, Deep Scattering Spectrum, IEEE TSP 2014](https://www.di.ens.fr/~mallat/papiers/AudioScatSpectrum.pdf) |
| **SSL features (wav2vec2 / HuBERT)** | **learned** contextual latents via masked prediction of quantised units; rich phonetic/contextual representation — but TRAINED (millions of params, gradient-fit) | [HuBERT, arXiv 2106.07447](https://arxiv.org/abs/2106.07447) |

### 1B. Features (descriptors over the time-freq surface)

| Feature | What it captures | Cited / source |
|---|---|---|
| **Formants F1–F3** | vocal-tract resonance frequencies | agent HAS (spacings) |
| **F0 / pitch contour + voicing** | glottal **source** fundamental and its **trajectory** (autocorrelation / YIN / RAPT / SWIPE) | Praat; eGeMAPS frequency params |
| **Energy / loudness** | per-frame intensity, RMS, perceptual loudness | universal |
| **ZCR** (zero-crossing rate) | crude **voiced/unvoiced + spectral-tilt** proxy (high for fricatives) | librosa |
| **Spectral centroid** | "brightness" — energy-weighted **mean frequency** | librosa |
| **Spectral rolloff** | frequency below which X% of energy lies — **high-freq extent** | librosa |
| **Spectral bandwidth / spread** | spread of energy about the centroid | librosa |
| **Spectral flux** | frame-to-frame **spectral change** magnitude (onset/transition energy) | librosa |
| **Spectral contrast (octave-band peak−valley)** | per-octave-band **peak strength − valley strength** → **harmonic vs noise** balance; explicitly **complementary to MFCC** (MFCC averages the band; contrast keeps relative peak/valley) | [Music type classification by spectral contrast](https://www.researchgate.net/publication/3968978_Music_type_classification_by_spectral_contrast_feature) |
| **Spectral slope / tilt / alpha-ratio / Hammarberg index** | global spectral **tilt** (low-vs-high energy ratio) — voice quality, manner | eGeMAPS spectral params |
| **Delta / delta-delta** | 1st/2nd temporal derivative of any feature | agent HAS (transition = order-1) |
| **Modulation spectrum** | the **temporal-modulation** spectrum per sub-band; linguistically dominant **2–8 Hz, peak 4 Hz = syllabic rate**; thought **invariant across speakers/conditions** | [Exploring the role of the modulation spectrum in phoneme recognition, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2663519/); [4 Hz = syllabic rate / robust](https://arxiv.org/pdf/2204.00065) |
| **TRAPs / MRASTA** | **long temporal context** (≈1 s) of a single critical band's energy trajectory → captures slow co-articulatory dynamics one band at a time | Hermansky TRAPs |
| **Jitter / shimmer / HNR** | cycle-to-cycle F0 / amplitude perturbation + harmonics-to-noise — **voice quality / source** | [eGeMAPS](https://mediatum.ub.tum.de/doc/1523509/file.pdf) |
| **eGeMAPS / ComParE sets** | curated **88-param (eGeMAPS) / 6k (ComParE)** affect/voice descriptor banks (F0, formants, jitter/shimmer, loudness, spectral slope, MFCC stats…) | [GeMAPS/eGeMAPS, Eyben et al.](https://mediatum.ub.tum.de/doc/1523509/file.pdf) |

### 1C. Transforms (normalisations on the feature stream)

| Transform | What it does | In agent? |
|---|---|---|
| **CMVN** (cepstral mean/var norm) | subtract per-utterance mean (removes convolutional channel), normalise variance | HAVE |
| **VTLN** (vocal-tract-length norm) | warp frequency axis to a canonical tract | HAVE (cohort warp) |
| **Per-channel energy norm (PCEN)** | adaptive AGC + dynamic-range compression per band — **noise/loudness robustness**, trainable-or-fixed | candidate (fixed form) |
| **RASTA filtering** | per-band 1–16 Hz band-pass (= modulation filter) — removes steady-state, keeps relative change | (subsumed under modulation node) |
| **Mean/var normalisation** | generic standardisation | HAVE |
| **fMLLR / feature-space MLLR** | speaker-adaptive **affine transform** fit per speaker | NOT no-fit (needs adaptation data) |

### 1D. Decoders / combination structures (harvest only portable TRICKS, not as nodes)

These are **alternative combination structures** — ours is the Bayes-product graph,
so HMM/GMM/CTC/attention/WFST are NOT harvested as nodes. Portable algorithmic
tricks only:

| Structure | Portable trick (not a node) |
|---|---|
| **HMM/WFST/lattice** | **context constraints** + **N-best lattices** — keep K candidates per cue and let the product re-rank, instead of 1-NN top-1. A lattice = a soft candidate set the product already consumes; widening the per-node candidate set is a free harvest. |
| **CTC** | **blank / alignment-free** scoring — useful later for the *continuous segmenter*, not the recognition product. |
| **DTW** | HAVE (already the per-node distance). |
| **Attention** | soft alignment — a *learned* combiner; not portable no-fit. |

---

## 2. NODE classification (composable / small-net / not-portable-but-insight)

The hard contract (from iter-33/34): a node is a **per-candidate likelihood** with
its **own median-distance temperature**, entering the variadic product
symmetrically — **no fit, no select-best, no weight**. Classify each harvested
method against that contract.

### 2A. COMPOSABLE NODE — pure DSP, no fit, straight into the product

These are mechanical adapter-math (np.fft / autocorrelation / log-pooling) at the
I/O boundary, the **same category as the existing `fft_ear` / `cochleagram`
nodes**. Each emits a fixed-length per-utterance descriptor → 1-NN exemplar
evidence → softmax by its own median distance → one more item in the `Times`.

| Composable node | What it adds (orthogonality) | Notes |
|---|---|---|
| **F0 / pitch-contour node** | explicit **source pitch trajectory** (resampled to fixed grid). Orthogonal: the agent has *binary* voicing, never the contour. | autocorrelation/YIN — no fit |
| **Modulation-spectrum node** | per-band **2–8 Hz temporal-modulation** energy (syllabic rhythm). Orthogonal: a *temporal-rate* axis, not a spectral or order-1 axis. | envelope → short-FFT of the envelope, fixed mod-bands |
| **Spectral-contrast node** | per-octave **peak−valley** (harmonic-vs-noise balance). Orthogonal: agent reads peaks (formants) + band-energy, never the *contrast within a band*. | librosa-style, fixed octave bands |
| **Spectral-shape node** (centroid / slope / tilt / rolloff / flux, stacked) | global **brightness / tilt / high-freq extent / flux**. Orthogonal: a *coarse-shape* summary the per-band channels do not isolate. | trivially composable; cheap |
| **CQT / constant-Q node** | a **log-frequency, octave-equivariant** time-freq geometry. Orthogonal-in-geometry to both linear-FFT and ERB-gammatone. | librosa CQT, fixed |
| **RASTA-filtered cochleagram node** | the existing cochleagram with each band **1–16 Hz band-passed** (steady-state + channel removed). Partly redundant with the *transition* node (both emphasise change) — flag below. | one-line filter on existing envelope |
| **ZCR / loudness node** | crude tilt + intensity. Mostly redundant (manner/voicing already has band-energy balance). Low value. | flag redundant |

### 2B. SMALL-SPECIFIC-NET NODE — needs a tiny composed/authored transform (in-thesis, like iter-28)

These need a small composed operator (a few authored gadgets, no gradient fit) —
the agent's `code_writing_cortex` CPWL constructor renders them exactly. In-thesis
per `research_polyglot_machinery.md` §1d (a small composed conv hierarchy is what
the cortex *is*).

| Small-net node | What it adds | Why it needs composition (not pure DSP) |
|---|---|---|
| **Scattering / 2nd-order modulation node** | time-shift-invariant + **time-warp-stable** representation; 2nd-order recovers AM/transient structure mel averages away | a *cascade* (wavelet-conv → modulus → low-pass → repeat) — authored as a 2-layer conv gadget, not a single transform |
| **PNCC-style noise-robust node** | gammatone + **asymmetric noise-floor subtraction** + power-law nonlinearity → degradation invariance (the APD gap) | the asymmetric filter + medium-time bias estimate is a small composed operator over the existing envelope; no fit, but more than one np call |
| **TRAP / long-context band node** | ≈1 s single-band temporal trajectory → slow co-articulation | a per-band long-window pooling gadget; composable but a distinct authored layout |
| **PCEN node** | adaptive per-channel gain (AGC) → loudness/noise robustness | fixed-coefficient PCEN is a small composed IIR-AGC gadget (no fit if coefficients are authored, not learned) |

### 2C. NOT-PORTABLE as a node — the big trained net (state the algorithmic insight)

| Method | Why not portable | The portable ALGORITHMIC insight (for a composed analog) |
|---|---|---|
| **wav2vec2 / HuBERT (SSL)** | millions of gradient-fit params; a node would import a trained tensor (out-of-thesis, the donkey) | **masked-prediction objective** + **iterated clustering** (cluster MFCCs → train → re-cluster own latents). The agent's within-thesis analog already named in `research_polyglot_machinery.md` §3.2: grow the representation by **cross-voice prediction-error reduction**, selected by compression — NOT as a node in the product but as the **representation-BUILDER** behind all nodes. Keep it as the builder line, not a product node. |
| **fMLLR / speaker-adaptive transforms** | fit an affine transform per speaker from adaptation data = a fit | the *idea* — per-speaker normalisation — is already the VTLN/CMVN role; the no-fit version is the cross-voice survival selector, not an adapted transform. |
| **Attention / neural combiner** | learned combination weights | our combiner IS the no-fit Bayes product; the insight (soft alignment) belongs to the continuous segmenter, not the product. |

---

## 3. ORTHOGONALITY ranking vs the agent's current cues

The agent's covered axes: **energy-envelope** (gammatone), **fine static spectrum**
(FFT-ear), **resonance-relations** (formant), **voicing/source-binary + gross
manner** (manner/voicing), **first-order temporal change** (transition),
**top-down generative** (AxS). A candidate is orthogonal if it occupies an axis
**none** of these covers (catches a different error kind → widens the win + the
shuffle margin, per the iter-34/36 mechanism).

### Ranked candidate NEW orthogonal nodes (most → least orthogonal)

| Rank | Candidate node | Orthogonal axis (why complementary) | Class | Redundancy risk |
|---|---|---|---|---|
| **1** | **F0 / pitch-contour** | **source-pitch TRAJECTORY** — a wholly separate channel from the vocal-tract *filter* the agent reads everywhere (formant, gammatone, FFT all read the *filter*; F0 is the *source*). The `research_speech_deficits.md` agnosia split (phonagnosia ⊥ word-deafness) says source/voice is an architecturally separate channel; on cross-speaker function words (iter-36's hard venue) the contour disambiguates where the filter is reduced. | composable | LOW — agent has only *binary* voicing, never the contour |
| **2** | **Modulation spectrum (2–8 Hz syllabic rhythm)** | **temporal-RATE / envelope-rhythm** axis — Goswami's rise-time/modulation axis named *missing* in `research_speech_deficits.md`. The transition node is a *point* derivative (order-1 between windows); the modulation spectrum is the *rate distribution* of the envelope. Speaker/condition-invariant by design. | composable (1st-order); small-net (2nd-order scattering) | LOW — distinct from order-1 transition |
| **3** | **Spectral contrast (octave peak−valley)** | **harmonic-vs-noise BALANCE within a band** — the agent reads peaks (formants) and band-*energy*, never the peak-*minus-valley* relief. Explicitly documented as complementary to mel-averaging (which the gammatone/FFT nodes are forms of). Separates sonorant/sibilant/noise structure the manner node only crudely bins. | composable | MEDIUM — partial overlap with manner/voicing's sonorant/sibilant predicate |
| **4** | **PNCC-style noise-robust front-end** | **degradation-INVARIANCE** axis (the APD gap in `research_speech_deficits.md`) — none of the agent's nodes survive added noise; PNCC's asymmetric noise-floor subtraction is a different *kind* of robustness from cross-voice invariance. Most valuable when the venue adds noise (not on clean FSDD/LibriSpeech). | small-net | LOW on noisy data; LOW VALUE on clean data |
| **5** | **CQT / constant-Q** | **log-frequency / octave geometry** — orthogonal-in-geometry to linear-FFT (fft_ear) and ERB-gammatone. A third time-freq operating point in the two-ears spirit. | composable | MEDIUM — another spectral view; could behave like a redundant gammatone setting if its information overlaps the FFT-ear |
| **6** | **Spectral-shape summary (centroid/slope/tilt/rolloff/flux)** | **coarse global SHAPE** — cheap, partly novel (global tilt/brightness not isolated elsewhere), but low-dimensional and correlated with band-energy balance. | composable | MEDIUM-HIGH — flux ≈ transition; centroid/rolloff ≈ formant/peak location |
| **7** | **TRAP / long-context band** | **slow per-band co-articulation** (≈1 s) — a longer temporal scale than transition's windows. Mildly orthogonal (timescale), but reads the same band energy. | small-net | MEDIUM |
| **—** | **Scattering (full)** | time-warp-stability is genuinely novel, but its *information* (AM structure, modulation) **overlaps the modulation-spectrum node (#2)** at much higher cost. Prefer #2 first; revisit scattering only if #2 wins and warp-invariance is the residual. | small-net | OVERLAPS #2 |

### Honestly flagged as likely REDUNDANT with what the agent has

- **GFCC / MFCC / PLP as nodes** — REDUNDANT. These are the *same information*
  (cepstral envelope of an ERB/mel/Bark filterbank) the gammatone cochleagram
  nodes already carry; cepstral decorrelation changes the *coordinates*, not the
  *information*. A GFCC node is a re-parameterised gammatone setting → multiplies
  in near-flat (the iter-33 finding that the 5 flat gammatone channels were partly
  redundant). **Do not add.**
- **RASTA-filtered cochleagram** — PARTLY REDUNDANT with the *transition* node:
  both emphasise spectral *change* over steady-state. RASTA's distinct value
  (convolutional-channel removal) is already the CMVN role. Low marginal value.
- **ZCR / loudness / energy** — REDUNDANT with manner/voicing's band-energy balance
  and periodicity. Crude proxies for cues the agent reads better. **Do not add.**
- **Spectral flux** — REDUNDANT with the transition node (both = frame-to-frame
  spectral change). Skip flux specifically; keep the *other* spectral-shape terms.
- **eGeMAPS/ComParE as a node** — these are **feature SETS, not a node**. Harvest
  the *individual* descriptors that are orthogonal (F0, jitter/shimmer, slope) as
  their own nodes; the bundled set as one node mixes redundant + orthogonal and
  dilutes (the iters-25/26 concatenation-dilution failure mode).

### Where "no fit" is genuinely impossible (stated plainly)

- **SSL (wav2vec2/HuBERT)** — a trained tensor; impossible as a no-fit node. Its
  insight (masked prediction + iterated clustering) belongs to the
  representation-BUILDER (the polyglot-machinery line), not the product. Out of
  scope for this harvest as a node.
- **fMLLR / feature-space MLLR** — per-speaker affine fit; needs adaptation data =
  a fit. Not a node.
- **PCEN with learned coefficients** — out. The **fixed-coefficient** PCEN is in
  (authored, no fit) — but only the fixed form.
- **PNCC's online noise-floor tracking** — the asymmetric filter is *adaptive*
  (tracks the running noise floor) but it adapts **within one utterance from the
  signal itself**, not fit from labels — so it is admissible as a composed
  operator (same status as CMVN's per-utterance mean). The line: signal-derived
  per-utterance adaptation = OK (CMVN/PCEN/PNCC-floor); label-derived fit = NOT.

---

## 4. The single best next node to add

**F0 / pitch-contour node (rank #1).**

Rationale, against the iter-34/36 mechanism (orthogonal-in-information widens the
win + the shuffle margin):

1. **Maximally orthogonal axis.** Every other cue the agent owns reads the
   vocal-tract **filter** (gammatone energy, FFT spectrum, formant resonances,
   manner band-balance) or its temporal derivative. F0 is the **source** — a
   formally separate channel. The `research_speech_deficits.md` agnosia
   dissociation (phonagnosia ⊥ word-deafness) is the lesion-method proof that
   source/voice and filter/word are architecturally distinct — so a source node is
   the *most likely* to catch errors the filter nodes share.

2. **Hits exactly the venue where the graph pays off.** iter-36 showed the cues
   become complementary on **continuous cross-speaker function words**, where the
   bottom-up filter information is reduced/coarticulated. Pitch contour survives
   reduction (a reduced/devoiced segment still carries a recoverable pitch track
   from its neighbours) and is the cue that disambiguates prosodically-distinct
   short words — precisely the iter-36 error population (it caught function-word
   errors at 1.5–2.1× chance with *filter* cues; a *source* cue should catch a
   disjoint error set).

3. **Cleanly composable, no fit.** Autocorrelation/YIN pitch on the existing
   frame grid → resample to a fixed contour → 1-NN exemplar evidence → softmax by
   its own median distance → one more `Times` item. Same node shape as `fft_ear`.
   The agent already computes autocorrelation periodicity in
   `_manner_voicing_channel` — the contour is the *argmax-lag track* of the same
   autocorrelation it already runs (promote the existing periodicity scalar to its
   full lag-trajectory). No new primitive, no fit, no weight.

4. **Testable by the existing decisive controls.** Run it as a drop-it /
   error-overlap diagnostic in `scripts/iter36_continuous_graph.py`: does the F0
   node catch a *different* subset of the bottom-up's errors than the filter cues
   (low error-overlap = genuinely orthogonal), and does adding it widen the
   real−shuffle margin? Combine-all-23→24, no select, no weight — the audit holds
   unchanged.

**Runner-up:** the **modulation-spectrum node (#2)** — equally orthogonal (the
syllabic temporal-rate axis the deficit study named missing), composable, and the
natural second add. Prefer F0 first only because it is the cheaper, more directly
separable (source vs filter) axis and reuses an autocorrelation the agent already
runs; add modulation second to cover the temporal-rate axis F0 does not.

---

## 5. Honest caveats

- **Most of the field's front-ends are NOT orthogonal to the agent.** MFCC, PLP,
  GFCC, PNCC (clean), CQT are all *spectral-envelope* views — they re-parameterise
  information the gammatone + FFT-ear nodes already carry. The combinatorial graph
  tolerates them (they multiply in near-flat) but they **do not widen** — adding
  them is effort without payoff (the meta-monitor pattern). The harvest's real
  yield is the **handful of genuinely different axes**: source pitch, temporal-rate
  modulation, harmonic-vs-noise contrast, degradation-robustness.
- **Redundancy is the default, orthogonality the exception** — consistent with
  iter-33 (5 flat gammatone channels partly redundant) and iter-36 (formant went
  *neutral* on continuous). Expect most harvested nodes to be near-flat; bet on the
  3–4 ranked orthogonal ones.
- **The clean-data ceiling still bounds everything.** On FSDD digits the bottom-up
  already nails arbitrary digits (iter-36 PART B: back-transfer NULL); new
  orthogonal nodes will likely be *redundant on digits and complementary only on
  continuous* — so evaluate any added node on the **continuous** venue, not digits.
- **PNCC/PCEN noise-robustness only pays on noisy input.** On clean FSDD/LibriSpeech
  it is near-flat; it is headroom for a *noisy* venue, not the current one.
- **The SSL line is not a node and should not be smuggled in as one.** Its value is
  the representation-BUILDER algorithm (masked prediction + iterated clustering),
  which is a separate, already-scoped line (`research_polyglot_machinery.md` §3) —
  keep it there, do not import a trained tensor.
- **Do not bundle (eGeMAPS-as-one-node) — split into per-axis nodes.** Bundling
  redundant + orthogonal descriptors into one node re-introduces the iters-25/26
  concatenation-dilution failure; the whole point of the graph is that each
  orthogonal axis is its *own* node.

---

### One-line answer

Re-mining the field yields ~20 candidate front-ends/features/transforms, but the
combinatorial graph already covers the spectral-envelope axis many times over — so
the harvest's value is the **few orthogonal axes the agent lacks**: ranked,
**F0/pitch-contour (source, #1) > modulation-spectrum (syllabic rate, #2) >
spectral-contrast (harmonic-vs-noise, #3) > PNCC noise-robustness (#4) > CQT
geometry (#5)**, with MFCC/PLP/GFCC/CQT-as-envelope, RASTA, ZCR/loudness, and flux
flagged redundant, and SSL/fMLLR genuinely non-portable as no-fit nodes (SSL's
insight belongs to the representation-builder, not the product). **The single best
next node is the F0/pitch-contour node** — maximally orthogonal (the source channel
the agnosia split proves is separable), composable with no fit (the argmax-lag
track of an autocorrelation the agent already computes), and aimed at the
continuous cross-speaker venue where iter-36 showed the cues actually become
complementary.

---

## Sources

- PNCC: [Kim & Stern, Power-Normalized Cepstral Coefficients (CMU)](https://www.cs.cmu.edu/~robust/Papers/OnlinePNCC_V25.pdf) · [PNCC ICA 2012](http://www.cs.cmu.edu/afs/cs/user/robust/www/Papers/KimStern_ica12_PNCC.pdf)
- RASTA-PLP: [RASTA processing of speech (Hermansky & Morgan)](https://www.researchgate.net/publication/3333372_RASTA_processing_of_speech) · [RASTA-PLP reference impl](https://github.com/bingo-todd/RASTA-PLP)
- Modulation spectrum: [Role of the modulation spectrum in phoneme recognition, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2663519/) · [Relative importance of modulation-spectrum components for ASR, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639399000023) · [Importance of different temporal modulations (4 Hz syllabic), arXiv](https://arxiv.org/pdf/2204.00065)
- Scattering transform: [Andén & Mallat, Deep Scattering Spectrum, IEEE TSP 2014](https://www.di.ens.fr/~mallat/papiers/AudioScatSpectrum.pdf) · [arXiv 1304.6763](https://arxiv.org/abs/1304.6763)
- Spectral contrast: [Music type classification by spectral contrast feature (Jiang et al.)](https://www.researchgate.net/publication/3968978_Music_type_classification_by_spectral_contrast_feature)
- eGeMAPS / voice-quality descriptors: [Eyben et al., GeMAPS/eGeMAPS (TUM)](https://mediatum.ub.tum.de/doc/1523509/file.pdf)
- SSL / masked prediction: [HuBERT, arXiv 2106.07447](https://arxiv.org/abs/2106.07447)
- (Cross-referenced internal): `docs/research_polyglot_machinery.md` (representation-builder / SSL-as-builder), `docs/research_speech_deficits.md` (the source⊥filter agnosia split, the modulation/rise-time gap, the APD noise-robustness gap), `docs/agent_loop_iteration34_enriched_graph.md` + `36_continuous_and_transfer.md` (the orthogonality-widens-the-win mechanism).
</content>
</invoke>
