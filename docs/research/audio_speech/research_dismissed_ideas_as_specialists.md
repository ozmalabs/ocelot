# Re-mining the field's DISMISSED "only useful for X" ideas as SPECIALIST nodes

> Step-back harvest triggered by the user: "RE-MINE the DISMISSED 'only useful for
> X' ideas in speech/acoustics — methods the field rejected as too NICHE/narrow."
> Companion to `docs/research_remine_methods_as_nodes.md` (which mined the
> *mainstream* feature corpus). This one mines the field's **rejected pile**.
>
> **The strategic frame.** "Only useful for X" is the field's rejection under
> **PIPELINE thinking**: a pipeline has one front-end stage and must pick the single
> best *general* feature, so a specialist that helps only on X loses the average
> benchmark and is discarded. But the agent's recognition is a **GRAPH** — a variadic
> Argmax-of-product (combinatorial Bayes product) over per-cue likelihood nodes
> (`domains/many_settings_recognizer.predict_many_settings_term`). In a product, a
> specialist that is **sharp on X and near-flat everywhere else CANNOT HURT** (a
> near-flat node multiplies in as ~1; iter-34/36 proved this — `manner_voicing` is
> 0.179 ALONE yet +0.012 drop-it IN the product). This is the binary-admissibility
> thesis turned into a strength: a specialist **admits X cleanly** (binary, brittle
> ALONE) but its "zero elsewhere" is harmless inside the product. **The field's
> rejected pile is our treasure** — each "only good for X" method is a gap-filler the
> field already built, validated, and then discarded for the wrong (pipeline) reason.
>
> **No build, no commit.** Harvest only.

---

## 0. What the agent has + its FAILURE MODES (the ranking axis)

Read from `research_remine_methods_as_nodes.md` §0 and the iter-34/36/37 docs.

**The agent's cues ALL read the vocal-tract FILTER** (spectral-envelope shape or its
time-derivative): gammatone cochleagram ×5 settings, FFT-ear, LPC formant-spacings,
manner/voicing band-balance, order-1 transition, single-pass AxS. **iter-37 is IN
FLIGHT adding two SOURCE/RATE axes: F0/pitch-contour + modulation-spectrum** — so
those two are EXCLUDED from this harvest's recommendation (do not duplicate).

The agent's graph **fails on** (the four failure-X axes this harvest ranks against):

| Failure-X | Why the FILTER cues fail on it | Venue where it bites |
|---|---|---|
| **(A) cross-speaker** | the filter is speaker-shaped (VTL, formant absolutes) | held-out-speaker LOSO; the whole project |
| **(B) coarticulation / continuous** | the steady-state envelope is smeared/reduced in running speech; boundaries are gone | LibriSpeech gold-span words (iter-36) |
| **(C) noise / degradation** | none of the agent's nodes survive added noise (the APD gap, `research_speech_deficits.md` §1b) | any noisy venue (NOT clean FSDD/Libri) |
| **(D) phoneme-CLASS confusions** | the cues bin manner crudely; stop bursts / VOT / fricative noise / nasal murmur are sub-frame, sub-band events the envelope averages away | every venue; the dyslexia rapid-transition axis (`research_speech_deficits.md` §1a-ii) |

The **honest no-fit / no-portability line** (inherited from
`research_remine_methods_as_nodes.md` §2C, §3): a node must be a **per-candidate
likelihood with its OWN median-distance temperature, entering the product
symmetrically — NO fit, NO select-best, NO weight**. Signal-derived per-utterance
adaptation is admissible (CMVN/PCEN/PNCC-floor); **label-derived fit is NOT**. A
trained tensor (SSL, the SVM/RNN detectors below in their *published* form) is NOT
portable — but the **acoustic measurement it detects** usually IS (the detector is
the donkey; the cue it measures is composable DSP).

---

## 1. The harvested DISMISSED-ideas inventory (by category, what X, cited)

For each: the method, **the X it was rejected as "only useful for,"** and the cite.

### 1A. NICHE speech — dismissed as "only for [a specific case]"

| Dismissed method | "Only useful for X" | Cite |
|---|---|---|
| **Glottal-source / phonation-type features** (creaky, breathy, tense, vocal-fry detectors; OQ/NAQ glottal-flow params) | "only for **paralinguistics / voice-quality / pathology**" — mood/attitude/emotion, clinical voice; explicitly found to **beat MFCC/PLP for pathology** but pigeonholed there | [Glottal Source Processing review, arXiv 1912.12604](https://arxiv.org/pdf/1912.12604) · [Phonation types in speech & singing, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639319303358) · [Lost in Phonation, arXiv 2510.25577](https://arxiv.org/html/2510.25577) · [Pathological voice via glottal features, arXiv 2309.14080](https://arxiv.org/pdf/2309.14080) |
| **Tonal pitch-CONTOUR / tone classifier** (F0-contour shape classified into tone categories; integrated tone classifier in a Mandarin recogniser) | "only for **tonal languages**" (Mandarin/Cantonese/Thai) — useless for Germanic/Romance ASR; note tonal-language listeners use the contour to stay robust **under noise/degradation** | [Mandarin tone via F0 contour (cochlear-implant), Frontiers](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.1026116/full) · [Integrated tone classifier patent US5602960](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5602960) · [tone robust under degradation, PMC4048445](https://pmc.ncbi.nlm.nih.gov/articles/PMC4048445/) |
| **Phoneme-CLASS detectors / acoustic LANDMARKS + distinctive features** (Stevens; stop-burst detector, **VOT** detector, fricative detector, **nasal-murmur** detector) | "only for **one manner class / one cue**" — each detector fires only on its class; the *general* deep net beat the landmark pipeline on the average | [Landmark-based ASR, JHU 2004 (PMC2638080)](https://ncbi.nlm.nih.gov/pmc/articles/PMC2638080) · [nasal-manner detection, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639304000573) · [Stevens landmark/distinctive-feature lexical access, PubMed 12002871](https://pubmed.ncbi.nlm.nih.gov/12002871/) · [landmarks carry more phone info, arXiv 1710.09985](https://arxiv.org/pdf/1710.09985) |
| **VOT detectors specifically** (burst-onset vs voicing-onset interval; the stop-voicing cue) | "only for **stop voicing / accent / pronunciation assessment**" | [VOT via random forest, PubMed 21786917](https://pubmed.ncbi.nlm.nih.gov/21786917/) · [VOT via reassignment spectra, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639309000892) · [DeepVOT, Interspeech 2016](https://github.com/adiyoss/DeepVOT) |

### 1B. ABANDONED as "superseded by deep nets"

| Dismissed method | "Only useful for X" / why abandoned | Cite |
|---|---|---|
| **Group-delay & PHASE-spectrum features** (modified group delay, MODGDF, chirp group delay) | "**unstable / too noise-sensitive**" → the field discards phase and keeps only the magnitude spectrum; group delay is **high-resolution for formants + reveals glottal-flow** but rejected as not robust | [Group-delay in speech tech (review), IAS](https://www.ias.ac.in/article/fulltext/sadh/036/05/0745-0782) · [Modified Group Delay Function for phoneme recognition, SRI](https://www.sri.com/wp-content/uploads/2021/12/the_modified_group_delay_function_and_its_application_to_phoneme.pdf) · [formant estimation via group-delay-modified magnitude, ResearchGate](https://www.researchgate.net/publication/349699210) |
| **Teager-Kaiser energy operator / AM-FM modulation** (energy-separation; multiband demodulation; instantaneous freq+envelope of resonances) | "only for **formant tracking / V-UV / noisy-speech detection**" — niche demodulation tool; outperformed LPC for formants but boxed in | [TKEO formant tracking via energy separation, ResearchGate](https://www.researchgate.net/publication/232625318) · [AM-FM modulation model of speech, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639399000126) · [Instantaneous TEO for V-UV, ResearchGate](https://www.researchgate.net/publication/228937266) · [Multiband modulation energy for noisy-speech detection, ResearchGate](https://www.researchgate.net/publication/3457672) |
| **TRAPs / TempoRAl Patterns / MRASTA** (≈0.5–1 s single-band energy trajectory) | "**superseded** by neural acoustic models" — but explicitly found to give **complementary info** and **robustness to additive+convolutive degradation** when fused | [TRAPs in noisy ASR, ResearchGate](https://www.researchgate.net/publication/3793940) · [TRAP-TANDEM, academia.edu](https://www.academia.edu/86741711) · [Speech recognition from spectral dynamics, Sādhanā](https://link.springer.com/article/10.1007/s12046-011-0044-2) |
| **Articulatory-inversion / gestural features** (acoustic→vocal-tract constriction trajectories; Articulatory Phonology gestures) | "**superseded by deep nets**" — but consistently **improves phone/speech recognition when ADDED** to acoustic features (a complement, never the replacement) | [Acoustic-to-articulatory inversion review, arXiv 2504.13308](https://arxiv.org/html/2504.13308v1) · [hybrid CNN articulatory+acoustic ASR, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639316300401) · [speaker-independent inversion, arXiv 2302.06774](https://arxiv.org/pdf/2302.06774) |
| **Sparse / overcomplete EXEMPLAR coding** (sparse representation over a clean-speech exemplar dictionary; sparse imputation / missing-data) | "only for **noise-robust / missing-data ASR**" — strong at low SNR (92% @ −5 dB w/ oracle mask) but eclipsed by end-to-end nets on clean data | [Sparse imputation for noise-robust ASR, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0885230810000653) · [noise-robust digit recognition via sparse rep, academia.edu](https://www.academia.edu/51935662) · [noise-robust exemplar matching, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639315001120) |
| **Reservoir computing / liquid-state / echo-state** (fixed random recurrent reservoir + linear readout) | "**niche**, never beat HMM/DNN at scale" — but trains no recurrent weights and matches nonlinear temporal tasks | [Reservoir-based speech recognition, ResearchGate](https://www.researchgate.net/publication/221531717) · [Extended LSM for speech, PMC9651956](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9651956/) · [Echo state network, Scholarpedia](http://www.scholarpedia.org/article/Echo_state_network) |

### 1C. CROSS-DOMAIN — dismissed as "only for [music / sonar / bioacoustics]"

| Dismissed method | "Only useful for X" | Cite |
|---|---|---|
| **HPSS — harmonic/percussive source separation** (median-filter the spectrogram: horizontal=harmonic, vertical=percussive/transient) | "only for **music** (melody/chord/onset)" — but "percussive sound … stems from **consonants in speech**"; it is a free **transient-vs-sustained split** | [HPSS lab course, AudioLabs Erlangen](https://www.audiolabs-erlangen.de/content/05_fau/professor/00_mueller/02_teaching/2017w_mpa/LabCourse_HPSS.pdf) · [HPSS for MIR tasks, ResearchGate](https://www.researchgate.net/publication/225805350) |
| **Spectral onset-detection function** (MIR onset/novelty curve) | "only for **music note onsets / beat tracking**" — directly a boundary cue for the segmentation gap | (same HPSS/MIR refs) |
| **DEMON** — Detection of Envelope Modulation On Noise (band-pass → envelope → narrowband demod → modulation spectrum) | "only for **passive sonar** (propeller blade-rate from cavitation noise)" — a noise-robust modulation-rate extractor on BROADBAND noise | [DEMON processor for sonar, IEEE Xplore](https://ieeexplore.ieee.org/document/9864381/) · [DEMON-LOFAR passive sonar, IJAIA](https://aircconline.com/ijaia/V15N1/15124ijaia06.pdf) |
| **Time-frequency REASSIGNMENT** (relocate spectrogram energy to instantaneous-freq + group-delay coordinates → sharp ridges) | "**niche** sharpening" for phonation analysis / whale-song / forensic speaker-ID — sharp formant + onset localisation at short windows | [Reassignment method, Wikipedia](https://en.wikipedia.org/wiki/Reassignment_method) · [Unified theory of reassignment, arXiv 0903.3080](https://arxiv.org/pdf/0903.3080) · [VOT via reassignment spectra, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639309000892) |
| **Bioacoustic contour / time-frequency RIDGE features + spectrogram cross-correlation** (extract the F0/formant ridge as a contour; match by template correlation) | "only for **animal calls** (birdsong, mouse USV, anuran)" — a shape-of-the-contour descriptor robust to absolute frequency | [contour features from TF ridge (mouse USV), JASA](https://pubs.aip.org/asa/jasa/article/152/1/266/2838328) · [spectrogram cross-correlation, Methods Ecol Evol](https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210X.13765) |

---

## 2. SPECIALIST-node classification + zero-fit feasibility

Each against the hard contract (per-candidate likelihood, own temperature, no fit,
no weight). **C** = composable pure-DSP node (drop straight into the product, same
category as `fft_ear`); **S** = small composed/authored gadget (in-thesis, the
`code_writing_cortex` CPWL constructor, no gradient fit); **N** = not-portable
as published (a trained detector) — **but** the underlying cue is re-derivable.

| Dismissed method | Class | The ZERO-FIT specialist node (the cue, stripped of the donkey) |
|---|---|---|
| **Group-delay / MODGDF** | **C** | the (modified) group-delay spectrum of the frame = `−d(phase)/dω` from the same FFT the agent already runs; pool to fixed bands → per-utterance descriptor. Pure DSP, no fit. Phase is information the magnitude-only nodes THROW AWAY → orthogonal by construction. |
| **Teager-Kaiser energy / AM-FM** | **C** | `Ψ[x] = x[n]²−x[n−1]x[n+1]` per band (3 multiply-adds), then energy-separation → instantaneous (envelope, freq) per band. No fit. A different *nonlinear* energy than the agent's linear band sums. |
| **HPSS transient/harmonic split** | **C** | median-filter the existing cochleagram horizontally (→harmonic) and vertically (→percussive); the **percussive residual** is a transient/consonant map. Two median filters, no fit. |
| **Onset / novelty curve** | **C** | spectral-flux-style positive-difference novelty over the cochleagram → a 1-D onset strength contour, resampled fixed. (NB: partly overlaps the agent's order-1 transition — flag.) |
| **DEMON modulation node** | **C** | band-pass → Hilbert/abs envelope → FFT-of-envelope → narrowband modulation peaks. **Caveat: this is the iter-37 modulation-spectrum node's sibling** — DEMON's distinct angle is *narrowband* modulation-line extraction on broadband noise. Defer to iter-37's modspec; revisit only the narrowband-line variant. |
| **Time-frequency reassignment** | **C** | reassign STFT energy via the same group-delay + instantaneous-freq estimates (chirp-z / phase-derivative). Pure DSP, no fit. Sharp ridges at short windows = better formant + onset localisation under coarticulation. |
| **Bioacoustic contour / ridge** | **C** | extract the per-frame argmax-ridge (the agent ALREADY computes the autocorrelation argmax-lag for F0 in iter-37 and the formant argmax in `dynamics_features`); the *shape-normalised contour* (mean-removed, range-normalised) is a speaker/absolute-frequency-invariant descriptor. Reuses owned operators. |
| **Tonal pitch-contour shape** | **C** (a *readout* of iter-37's F0) | NOT a new node — it is the **shape-classification readout** of the iter-37 F0 contour (delta-F0, contour curvature = order-1/2 over time of F0). In-thesis via `order_n_concepts`. Useless on non-tonal venues (flag). |
| **VOT / stop-burst / fricative / nasal-murmur landmark** | **N→C** | the *SVM/RNN detector* is the donkey (trained). But the **acoustic cue each measures is composable DSP**: stop burst = abrupt broadband energy rise after silence (onset curve in high bands); VOT = lag between burst-onset and voicing-onset (the agent has autocorrelation voicing + the onset curve — VOT is their *time difference*); fricative = sustained high-band aperiodic energy (the agent's sibilant predicate, sharpened); nasal murmur = low-freq energy concentration + spectral-zero (anti-formant). Each becomes a **per-class landmark-density / landmark-timing descriptor**, no fit. |
| **Glottal-source / phonation** | **S** | glottal inverse-filtering (IAIF) is an authored all-pole cascade (no fit, like LPC); read OQ/NAQ + spectral-tilt of the residual → a source-quality descriptor. The agent already does LPC; this is the *residual* of it. |
| **Articulatory inversion / gestures** | **N (builder, not a node)** | the published inversion is a trained net (donkey). The agent's **AxS node IS the within-thesis analog** (invert `speak()` = invert the articulatory forward model). Keep gestures as the AxS/forward-model line, NOT a new product node. |
| **Sparse exemplar / missing-data** | **N (combiner trick, not a node)** | the agent's product ALREADY does exemplar matching (1-NN per node). Sparse-coding's portable insight is **missing-data masking** — drop unreliable time-freq cells before the per-node distance (a robustness trick for failure-X **C**, not a new node). |
| **Reservoir / echo-state** | **N (out)** | a fixed random recurrent net is still a net with a fitted linear readout = a fit; and its temporal-memory role is the agent's sequence layer (SLI axis, already strong). Not a product node. |
| **TRAPs / MRASTA** | **C** | per-band ≈0.5–1 s energy trajectory, DCT/cosine-pooled to fixed length → one node per critical band (or pooled). Pure DSP, no fit. A *longer timescale* than the agent's transition windows. |

---

## 3. RANKING by the agent's FAILURE MODES (the key output)

A specialist ranks HIGH iff its X is a **real current gap** (A/B/C/D above) the
filter cues fail on, AND it is zero-fit composable, AND it is orthogonal to both the
agent's cues and the in-flight iter-37 nodes. Ranks LOW / "harmless-but-useless" iff
its X **doesn't occur in the continuous clean venue** (it sits near-flat — admissible
but no payoff, the meta-monitor's effort-without-payoff pattern).

| Rank | Specialist node | Failure-X it targets | Class | Why it fills a REAL gap (not covered by agent or iter-37) |
|---|---|---|---|---|
| **1** | **Landmark-density / VOT / burst / fricative / nasal cues** (phoneme-class detectors, re-derived zero-fit) | **(D) phoneme-class confusions + (B) coarticulation** | N→C | The dyslexia rapid-transition lesion (`research_speech_deficits.md` §1a-ii) names exactly this: phoneme identity lives in the **fast stop-burst / VOT / fricative-noise events** the envelope averages away. The agent bins manner CRUDELY (3-way sonorant/sibilant/voiced); a per-class **landmark** cue resolves the within-class confusions (b/d/g, p/t/k, s/f) that survive cross-speaker. **Orthogonal to F0 (source) and modspec (rate)** — this is the FAST-EVENT axis neither covers. This is also the Stevens distinctive-feature program, which the field had working (160 params, 80% manner on TIMIT) and discarded for the average benchmark. |
| **2** | **Group-delay / phase-spectrum** | **(B) coarticulation + (D) class** | C | The agent's nodes are ALL magnitude-spectrum (gammatone, FFT, LPC all discard phase). Group delay is the **single largest truly-orthogonal information source the field threw away** — high-resolution formant + glottal cues from the discarded half of the signal. "Unstable" was a *pipeline* objection (a magnitude-only system can't afford a flaky stage); in the product a flaky-but-sharp node multiplies in near-flat where it's uncertain. Maximally orthogonal because it's literally the complement of what every current node reads. |
| **3** | **HPSS percussive/transient split** + **onset curve** | **(B) coarticulation/segmentation** | C | "Percussive = consonants in speech." A clean **transient-vs-sustained** decomposition gives a consonant-burst map and boundary cues — the segmentation/coarticulation gap that is iter-36's core failure. Partial overlap with the order-1 transition node (flag); distinct in that it SEPARATES the streams rather than differencing them. |
| **4** | **Time-frequency reassignment** | **(B) coarticulation + (A) cross-speaker** | C | Sharp formant ridges at SHORT windows → better-localised formants under the smearing of running speech, where the agent's fixed-resolution front-ends blur. Improves the *quality* of the formant/transition cues precisely in the continuous venue. |
| **5** | **Teager-Kaiser AM-FM energy** | **(D) class + (C) noise** | C | A nonlinear per-band instantaneous (envelope, freq) — outperformed LPC for formants and used for V-UV under noise. Orthogonal *kind* of energy (nonlinear) vs the agent's linear band sums. Moderate overlap with formant/voicing cues (flag). |
| **6** | **TRAPs / MRASTA long-context band** | **(B) coarticulation + (C) noise** | C | A LONGER timescale (≈1 s) than the transition windows → slow co-articulatory context; documented complementary + robust to additive/convolutive degradation. Reads the same band energy (mild orthogonality, by timescale). |
| **7** | **Glottal-source / phonation quality** | **(A) cross-speaker (as nuisance-ID) + paralinguistics** | S | Source quality (OQ/spectral-tilt). Overlaps iter-37's F0 (both source-channel). Genuine *new* info is voice-quality/tilt, but its X (paralinguistics) is **not what FSDD/Libri-digit recognition needs** — modest. |
| **—** | **Tonal pitch-contour shape** | **only tonal-language tone (X absent in venue)** | C | **HARMLESS BUT USELESS on English FSDD/LibriSpeech** — tone is not phonemic in the venue, so it sits near-flat. Keep on the shelf for a tonal-language venue; it is a *readout* of iter-37's F0 anyway, near-free to add later. |
| **—** | **DEMON narrowband modulation** | **(C) noise (sonar venue)** | C | **Subsumed by iter-37's modulation-spectrum** for the speech venue; its distinct narrowband-line value is a sonar/noise specialty. Defer — do not duplicate iter-37. |
| **—** | **Bioacoustic ridge contour** | **(A) cross-speaker (absolute-freq invariance)** | C | Genuinely speaker-robust (shape, not absolute frequency), BUT it is the **same operator** as iter-37's F0-contour + the formant argmax-ridge the agent owns — largely redundant once iter-37 lands. Low marginal value. |
| **—** | **Sparse missing-data masking** | **(C) noise** | trick | A robustness *trick* (mask unreliable cells before the per-node distance), not a node. Useless on clean data; bank for a noisy venue. |
| **—** | **Reservoir / articulatory-net / SSL** | — | N | NOT portable as no-fit nodes (each is a trained net). Articulatory → the AxS line; reservoir's memory → the sequence layer (already strong); SSL → the representation-builder. Keep the *insight*, not a product node. |

### The honest "no-fit / no-payoff" line (kept explicit)

- **The X must occur in the venue.** Tonal-contour, DEMON-narrowband, and sparse-
  masking all target an X (tone, sonar, noise) **absent from clean English digit/
  continuous recognition** → they multiply in near-flat (admissible, the product
  cannot be hurt) but **add nothing here** (effort-without-payoff). They are bankable
  headroom for a *tonal* or *noisy* venue, not the current one. State this, do not
  pad the graph with them.
- **The detector is the donkey; the cue is the harvest.** The published VOT/burst/
  fricative/nasal detectors are SVMs/RNNs (a fit). Importing one violates the no-fit
  contract. What is admissible is **re-deriving the acoustic cue** each detector
  measures as composable DSP / a small authored gadget (rank #1's construction).
  This is the same line as `research_remine_methods_as_nodes.md` §3 (SSL's *insight*
  is portable, its *tensor* is not).
- **Articulatory inversion, reservoir, SSL** are genuinely non-portable as no-fit
  product nodes. Their roles map to lines the agent already has (AxS / sequence /
  representation-builder), not to new nodes.

---

## 4. The single best dismissed-idea specialist to add next

**The phoneme-CLASS LANDMARK node (rank #1) — re-derived zero-fit: a per-utterance
descriptor of stop-burst / VOT / fricative-noise / nasal-murmur landmark presence
and timing.** (Excludes F0 + modspec, which iter-37 is adding.)

Rationale, against the iter-34/36 mechanism (orthogonal-in-information widens the win
+ the shuffle margin) and the failure-mode ranking:

1. **Targets the gap NEITHER the agent NOR iter-37 covers.** The agent reads the
   *filter*; iter-37 adds the *source* (F0) and the *temporal rate* (modspec). The
   one remaining axis is the **fast transient PHONETIC EVENT** — the stop burst, the
   VOT interval, the fricative noise band, the nasal anti-formant. This is failure-X
   (D), and `research_speech_deficits.md` §1a-ii names it as the load-bearing,
   discard-prone cue (the dyslexia rapid-transition lesion). It is the cue that
   separates the *within-manner-class* confusions (b/d/g, p/t/k, s/f/θ) that survive
   every speaker-invariant filter cue.

2. **It is the field's own discarded, VALIDATED program.** Stevens'
   landmark/distinctive-feature recognition WORKED (Juneja & Espy-Wilson: 80% of six
   manner classes on TIMIT with **160 trainable parameters**); the field shelved it
   because the *general* DNN beat it on the *average*. In the product, "only fires on
   its class" is exactly right — a specialist that admits its class cleanly (binary)
   and is near-flat off it (harmless).

3. **Re-derivable ZERO-FIT from owned operators (the detector is the donkey).** Each
   landmark is composable DSP the agent already nearly has: burst = positive onset
   spike in high bands (HPSS-percussive / onset curve from rank #3); VOT = time-lag
   between that burst onset and the autocorrelation-voicing onset
   (`stacked_representation` already computes per-frame voicing); fricative = sustained
   high-band aperiodic energy (the existing sibilant predicate, time-resolved); nasal
   = low-band energy + a spectral zero (anti-formant, an LPC-residual dip the agent
   can read). The node emits a fixed-length **[per-class landmark density, mean
   landmark time, burst-to-voicing lag]** descriptor → the SAME 1-NN exemplar
   evidence → softmax by its OWN median distance → one more `Times` item. No SVM, no
   RNN, no fit, no weight — fully within the contract.

4. **Testable by the existing decisive controls.** Drop-it / error-overlap in the
   iter-36 continuous harness: does the landmark node catch a *different* subset of
   the bottom-up's errors (low overlap = orthogonal), and does it widen the
   real−shuffle margin? Combine-all, no select, no weight — the iter-34 audit holds.

**Runner-up:** the **group-delay / phase-spectrum node (rank #2)** — equally zero-fit
and arguably MORE orthogonal (it reads the *phase* half of the signal that every
current AND iter-37 node discards), but it is a more diffuse cue (a whole spectrum)
where the landmark node targets the named confusion population directly. Prefer the
landmark node first for its precision on failure-X (D); add group-delay second to
recover the discarded phase channel wholesale.

---

## 5. Honest caveats

- **The clean-venue ceiling still bounds everything.** On clean FSDD digits the
  bottom-up already nails arbitrary digits (iter-36 back-transfer NULL); these
  specialists will be **redundant on digits and complementary only on continuous /
  cross-speaker / within-class-confusion** populations. Evaluate every added node on
  the **continuous** venue and on the **confusion** slice, not the digit mean.
- **Redundancy is the default, orthogonality the exception** (iter-33/36). Expect
  most of these to multiply in near-flat; bet on the 2–3 that hit a named failure-X
  (landmark #1, group-delay #2, HPSS/onset #3).
- **Several specialists' X does not occur in the current venue** — explicitly flagged
  near-flat-and-useless-here: tonal pitch-contour (no lexical tone in English),
  DEMON-narrowband (sonar), sparse missing-data + Teager-V-UV-robustness (need
  noise), glottal-phonation (paralinguistics, not digit ID). They are HARMLESS in the
  product but add nothing on the present data — bank them for tonal/noisy venues; do
  not pad the graph to inflate the node count (the iter-33 redundant-channel lesson).
- **The detector is the donkey, the cue is the harvest** — the no-fit line in full:
  every "specialist" here is admitted as the **re-derived composable acoustic
  measurement**, never as the field's trained SVM/RNN detector. Re-deriving the cue
  is in-thesis; importing the detector is not.
- **Group-delay's "unstable" objection is real at the signal level** — phase is
  genuinely noise-sensitive; the product tolerates a flaky-but-sharp node (it
  multiplies in near-flat where uncertain), but the node's own median-distance
  temperature must be honest or a noisy node could mislead. Test the real−shuffle
  margin before trusting it.
- **AxS already IS the articulatory-inversion harvest** — do not add a second
  inversion node; the gestural/articulatory line is the AxS forward-model, kept
  there.

---

### One-line answer

Re-mining the field's REJECTED "only useful for X" pile yields specialist cues that
PIPELINE thinking discarded but the Bayes-product GRAPH welcomes (sharp on X,
near-flat = harmless elsewhere); ranked against the agent's failure modes (cross-
speaker, coarticulation, noise, phoneme-class confusion) and EXCLUDING the in-flight
F0/modspec, the top fillers are **phoneme-class LANDMARK cues (stop-burst / VOT /
fricative / nasal — the dyslexia fast-event axis; #1) > group-delay / PHASE spectrum
(the discarded half of the signal; #2) > HPSS transient split + onset curve
(consonant/segmentation; #3) > time-frequency reassignment (sharp formants under
coarticulation; #4)**, with the published VOT/landmark/articulatory/reservoir
DETECTORS flagged as donkeys (re-derive the cue, never import the trained net) and
tonal-contour / DEMON / sparse-masking / glottal-phonation honestly flagged as
harmless-but-useless on the clean English venue (bank for tonal/noisy venues). **The
single best next specialist is the re-derived zero-fit phoneme-class LANDMARK node** —
it targets the within-manner confusion population neither the filter cues nor iter-37
covers, it is the field's own validated-then-discarded Stevens program, and every
landmark is composable from operators the agent already owns (onset, voicing,
sibilant, LPC-residual) with no fit, no weight.

---

## Sources

- Glottal source / phonation: [Glottal Source Processing review, arXiv 1912.12604](https://arxiv.org/pdf/1912.12604) · [Phonation types, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639319303358) · [Lost in Phonation, arXiv 2510.25577](https://arxiv.org/html/2510.25577) · [Pathological voice, arXiv 2309.14080](https://arxiv.org/pdf/2309.14080)
- Tonal pitch-contour: [Mandarin tone via F0 contour, Frontiers](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.1026116/full) · [integrated tone classifier, US5602960](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5602960) · [tone robust under degradation, PMC4048445](https://pmc.ncbi.nlm.nih.gov/articles/PMC4048445/)
- Landmarks / distinctive features / phoneme-class detectors: [Landmark-based ASR (JHU 2004), PMC2638080](https://ncbi.nlm.nih.gov/pmc/articles/PMC2638080) · [nasal-manner detection, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639304000573) · [Stevens lexical access, PubMed 12002871](https://pubmed.ncbi.nlm.nih.gov/12002871/) · [landmarks carry more phone info, arXiv 1710.09985](https://arxiv.org/pdf/1710.09985)
- VOT: [VOT random forest, PubMed 21786917](https://pubmed.ncbi.nlm.nih.gov/21786917/) · [VOT via reassignment, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639309000892) · [DeepVOT](https://github.com/adiyoss/DeepVOT)
- Group-delay / phase: [Group-delay in speech tech, IAS](https://www.ias.ac.in/article/fulltext/sadh/036/05/0745-0782) · [Modified Group Delay phoneme recognition, SRI](https://www.sri.com/wp-content/uploads/2021/12/the_modified_group_delay_function_and_its_application_to_phoneme.pdf) · [formant estimation via group delay, ResearchGate](https://www.researchgate.net/publication/349699210)
- Teager-Kaiser / AM-FM: [TKEO formant tracking, ResearchGate](https://www.researchgate.net/publication/232625318) · [AM-FM model of speech, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639399000126) · [Instantaneous TEO V-UV, ResearchGate](https://www.researchgate.net/publication/228937266) · [Multiband modulation energy, ResearchGate](https://www.researchgate.net/publication/3457672)
- TRAPs / MRASTA: [TRAPs in noisy ASR, ResearchGate](https://www.researchgate.net/publication/3793940) · [TRAP-TANDEM, academia.edu](https://www.academia.edu/86741711) · [spectral dynamics, Sādhanā](https://link.springer.com/article/10.1007/s12046-011-0044-2)
- Articulatory inversion / gestures: [AAI review, arXiv 2504.13308](https://arxiv.org/html/2504.13308v1) · [hybrid CNN articulatory+acoustic ASR, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639316300401) · [speaker-independent inversion, arXiv 2302.06774](https://arxiv.org/pdf/2302.06774)
- Sparse / exemplar coding: [sparse imputation noise-robust ASR, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0885230810000653) · [noise-robust digit recognition, academia.edu](https://www.academia.edu/51935662) · [noise-robust exemplar matching, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639315001120)
- Reservoir / echo-state / liquid-state: [reservoir-based speech recognition, ResearchGate](https://www.researchgate.net/publication/221531717) · [extended LSM for speech, PMC9651956](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9651956/) · [echo state network, Scholarpedia](http://www.scholarpedia.org/article/Echo_state_network)
- HPSS / onset (MIR): [HPSS lab course, AudioLabs Erlangen](https://www.audiolabs-erlangen.de/content/05_fau/professor/00_mueller/02_teaching/2017w_mpa/LabCourse_HPSS.pdf) · [HPSS for MIR, ResearchGate](https://www.researchgate.net/publication/225805350)
- DEMON (sonar): [DEMON processor, IEEE Xplore](https://ieeexplore.ieee.org/document/9864381/) · [DEMON-LOFAR passive sonar, IJAIA](https://aircconline.com/ijaia/V15N1/15124ijaia06.pdf)
- Time-frequency reassignment: [Reassignment method, Wikipedia](https://en.wikipedia.org/wiki/Reassignment_method) · [Unified theory of reassignment, arXiv 0903.3080](https://arxiv.org/pdf/0903.3080)
- Bioacoustic contour / ridge / spectrogram cross-correlation: [contour features mouse USV, JASA](https://pubs.aip.org/asa/jasa/article/152/1/266/2838328) · [spectrogram cross-correlation, Methods Ecol Evol](https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210X.13765)
- (Cross-referenced internal): `docs/research_remine_methods_as_nodes.md` (mainstream harvest, the no-fit line, the agent's cues), `docs/research_speech_deficits.md` (the dyslexia fast-transition axis = phoneme-class events, the APD noise gap, the source⊥filter split), `docs/agent_loop_iteration34_enriched_graph.md` + `36_continuous_and_transfer.md` (orthogonal-widens-the-win + redundant-multiplies-flat mechanism), `docs/agent_loop_iteration37_source_nodes.md` (F0 + modspec IN FLIGHT — excluded here).
</content>
</invoke>
