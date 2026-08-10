# Re-mining slow/expensive methods for the order-N AxS slow path

Harvest for iter-39's order-N analysis-by-synthesis (AxS) slow path. The slow path
affords compute the real-time fast path cannot. Its AxS quality is **bounded by the
forward model** — `predict_axs(s) = argmax_w −DTW(features(s), features(speak(w | voice(s))))`
(`domains/recognition_graph.py:63-107`). A more accurate `speak()` buys down that
bound directly: the residual after inverting a good forward model is phonetic
identity; the residual after inverting a crude one is forward-model error.

This is a harvest only — no build, no commit.

## Baseline: what the agent's forward model is today

`STTPipeline.speak / speak_trajectory` → `audio_primitives.rs::synthesize_from_trajectory`
(`runners/dsl/src/audio_primitives.rs:368-540`). It is a **basic source-filter
voicebox**:

- **Source**: fixed harmonic stack at f0, amplitude `0.3/k`, ~−3 dB/oct tilt, k<40
  (line 455-466). One static spectral tilt; no glottal pulse shape, no open-quotient,
  no spectral-tilt control, no jitter/shimmer.
- **Noise source**: deterministic LCG, flat (line 468-480).
- **Filter**: per-patch RBJ-cookbook **bandpass biquads** (one biquad per A1 patch),
  Q derived from patch sigma, summed in **parallel** (line 492-522). Parallel-formant
  topology, not cascade; no anti-resonances (zeros); no lip-radiation; no nasal branch.
- **Envelope**: linear-interpolated per-patch trajectory; attack/release ramp; peak
  normalize.

The analysis side already has **LPC** (autocorrelation + Levinson-Durbin) used for
formant-envelope smoothing — `domains/lpc_formant_representation.py`
(`_autocorr`, `_levinson`, `lpc_envelope_row`). The agent itself classified LPC as
**"adapter-math (numeric DSP), NOT a composable DSL Term"**
(`domains/runtime_design.py:208-233`). That precedent sets the zero-fit bar for
everything below: pure DSP at the I/O boundary, no learned weights, composed/driven
by graph data.

The in-thesis line for this harvest (verbatim from the task): **mining the synthesis
ALGORITHM is in; inverting a trained neural TTS net to do the agent's perception is
the donkey.**

---

## Part 1 — Accurate SYNTHESIS algorithms (→ better forward model, the AxS bound)

Classification key:
- **compose-the-algorithm** — closed-form DSP, no fitted weights; the agent composes
  it as its own forward model, like its existing biquad voicebox + LPC. Zero-fit.
- **TTS-as-teacher** — an external accurate synthesizer used in the babble loop as a
  comparison target; the agent grounds its own forward model against it. Not inverted.
- **donkey-only** — requires a trained net; can only serve by inverting the net =
  the agent's perception done by someone else's weights. Out.

### 1a. Klatt cascade/parallel formant synthesizer — compose-the-algorithm ★

Klatt (1980) is the classic **parametric, fully closed-form** source-filter synthesizer:
a periodic impulse train + a noise source driving digital resonators, with a hybrid
**cascade** branch (vowels/sonorants, with **anti-resonances/zeros** for nasals) and
a **parallel** branch (fricatives, stop bursts). Parameters are formant frequencies +
**bandwidths** (separately controlled for cascade vs parallel) and source params.
[Klatt 1980 JASA](https://www.fon.hum.uva.nl/david/ma_ssp/doc/Klatt-1980-JAS000971.pdf),
[Berkeley Phonlab params](https://linguistics.berkeley.edu/plab/guestwiki/index.php?title=Klatt_Synthesizer_Parameters),
[chdh/klatt-syn](https://github.com/chdh/klatt-syn).

**Why more accurate than the current resynth**: (1) the **cascade** topology with
relative formant amplitudes set automatically by the resonator chain is closer to the
real vocal-tract transfer function than the agent's independent **parallel** biquads
(which lose the inter-formant amplitude relations); (2) **anti-resonances (zeros)**
model nasals/laterals that an all-pole/all-bandpass voicebox cannot represent;
(3) explicit **formant bandwidth** control vs the agent's sigma-derived Q;
(4) a real **two-source switch** (voiced impulse train vs aspiration/frication) per
segment instead of the agent's centre-frequency>3500 Hz heuristic.

**Zero-fit**: yes. Every Klatt parameter is a hand-interpretable number; no training.
It is a strict superset of the agent's existing biquad voicebox (the agent already
has RBJ biquads — Klatt resonators are the same family plus zeros + cascade routing).
The agent's A1-patch trajectory maps onto Klatt formant tracks; this is the smallest
step from where it is.

### 1b. Liljencrants-Fant (LF) glottal source model — compose-the-algorithm ★

The LF model is a **parametrized time-domain** model of the glottal-flow **derivative**
— 6 shape params (T0, Tp, Te, Ta, Tc, Ee). It replaces the agent's fixed `0.3/k`
harmonic tilt with a physically-shaped excitation carrying open-quotient and
spectral-tilt (voice-quality) structure.
[ARMAX-LF arXiv](https://arxiv.org/pdf/2410.04704),
[Perceptual equivalence, JASA](https://pubs.aip.org/asa/jasa/article/150/2/1273/615393/).

**Why more accurate**: the source spectrum is the single biggest crudeness in the
current voicebox (one static tilt). The LF source gives the correct low-frequency
glottal-formant + high-frequency roll-off, which is exactly the cue that differs
across speakers/voices — the nuisance the AxS forward model is supposed to *absorb*
into `voice(s)`. Pairs naturally with Klatt (Klatt's KLGLOTT88 is an LF-like source).

**Zero-fit**: yes — closed-form waveform from 6 params. Fitting LF *to* an observed
glottal wave needs an estimator (Kalman/optimization), but for the **forward model**
the agent only needs to *generate* from params, which is pure DSP.

### 1c. Articulatory / vocal-tract-model synthesis (Maeda area function) — compose-the-algorithm, expensive ★ (highest accuracy ceiling)

Represent the vocal tract as a **1-D acoustic tube** (concatenated tubelets / area
function); propagate via Maeda's Transmission-Line-Circuit-Analog (TLCA) or
Kelly-Lochbaum waveguide. Physically derives the transfer function (all formants,
their bandwidths, and their amplitude relations) from tube geometry.
[Maeda articulatory synthesis (Loria)](https://members.loria.fr/BElie/pages/artsynthesis.html),
[airway modulation model, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3596841/).

**Why more accurate**: this is the *most* accurate composable forward model — formants
are not free parameters but consequences of geometry, so coarticulation (tube shape
changing over time) is modeled by construction, and speaker VTL is a single scale on
the tube length (the agent's exact `xspeaker_norm` VTL-invariance lever, now in the
forward model). It is the model used in the **classic AxS inversion literature**
(below), so it is the natural substrate for order-N AxS specifically.

**Zero-fit**: yes — closed-form acoustics. **Cost**: this is the expensive option (a
PDE/waveguide solve per frame), which is exactly what the slow path is for. The
control problem (which articulatory trajectory) is what AxS *optimizes*.

**Direct AxS precedent (the load-bearing find)**: Panchapagesan & Alwan,
*acoustic-to-articulatory inversion by analysis-by-synthesis using chain matrices and
the Maeda model* — a quasi-Newton optimization of articulatory trajectory minimizing
a distance between **natural and synthesized first three formants**, with continuity +
regularization terms.
[PMC3188964](https://pmc.ncbi.nlm.nih.gov/articles/PMC3188964/),
[PubMed 21476670](https://pubmed.ncbi.nlm.nih.gov/21476670/). This *is* the order-N
AxS loop the agent is building (iterate forward-model params to converge synthesis
error), with a composable physics forward model — a structural template, not a donkey.
VocalTrax (optimization over the Pink Trombone articulatory synth) is the modern
restatement; the synth is composable, only its *optional* learned front-end is not
([VocalTrax](https://openreview.net/pdf?id=kIDxwvWznF)).

### 1d. Source-filter / LPC synthesis — compose-the-algorithm (already half-owned)

Classic LPC synthesis: excite the all-pole `1/A(z)` filter (the agent already fits
A(z) via Levinson-Durbin in analysis) with an impulse train (voiced) or noise
(unvoiced). The agent has the **analysis** half; the **synthesis** half (running the
LPC filter as the forward model instead of summed bandpass biquads) is a small step.

**Why more accurate than biquad-sum**: the all-pole filter reproduces the *joint*
formant structure (a single 1/A(z) with all poles) rather than independently-gained
parallel bandpasses, so inter-formant amplitudes are correct; and it is *exactly the
same model the agent already uses to read formants*, closing analysis and synthesis
on one representation. **Zero-fit**: yes, already proven in-repo. **Ceiling**: all-pole
only (no zeros/nasals) — Klatt or articulatory exceed it.

### 1e. WORLD vocoder (DIO/Harvest + CheapTrick + D4C) — compose-the-algorithm, high quality

WORLD decomposes speech into **F0** (DIO/Harvest), **spectral envelope** (CheapTrick),
and **band aperiodicity** (D4C), and resynthesizes from those three. All three are
**signal-processing algorithms, not nets**.
[mmorise/World](https://github.com/mmorise/World),
[D4C, ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0167639316300413).

**Why more accurate**: near-transparent resynthesis quality; the **aperiodicity**
decomposition (D4C) is the right way to model breathy/mixed excitation the agent's
binary voiced/noise switch gets wrong; CheapTrick gives a pitch-robust smooth
envelope. **Zero-fit**: yes — closed-form DSP. **Caveat / tension with the thesis**:
WORLD's parameterization (envelope + aperiodicity + F0) is **descriptive**, not
**generative-from-understanding** — it is a high-quality codec of an observed signal,
so as a *forward model* it tends toward "resynthesize what you analyzed" rather than
"generate a candidate word from lexical knowledge." Best role: a **TTS-as-teacher /
high-quality copy-synth reference** the agent grounds against, and as the **envelope/
aperiodicity analysis** front-end (see Part 2), rather than the generative core.

### 1f. Harmonic-plus-Noise Model (HNM) / sinusoidal model — compose-the-algorithm

HNM splits speech at a **maximum-voiced-frequency** into harmonically-related sinusoids
(low band) + modulated colored noise (high band).
[HNM, IEEE](https://ieeexplore.ieee.org/document/379970/),
[Stylianou HNM PDF](https://www.ee.columbia.edu/~dpwe/e6820/papers/Styl01-hnm.pdf).
**Why more accurate**: the MVF split is a principled improvement on the agent's
hard-coded "centre>3500 Hz → noise" rule — voicing is frequency-dependent, not a
per-patch flag. **Zero-fit**: yes. Closely related to WORLD in spirit; less commonly
the generative core, more an analysis/modification model — similar teacher-leaning
caveat as WORLD.

### 1g. TD-PSOLA + concatenative/unit-selection — compose-the-algorithm, exemplar-native ★ (fits the lexicon)

TD-PSOLA pitch-marks waveform exemplars and overlap-adds Hann-windowed
pitch-synchronous frames to change pitch/duration **with no source-filter
decomposition** → resynthesis quality "highly similar to the original."
[TD-PSOLA, learnius](https://learnius.com/slp/9+Speech+Synthesis/1+Fundamental+Concepts/2+Technologies/pitch-synchronous+overlap-add+(TD-PSOLA)),
[PSOLA, Illinois PDF](https://courses.grainger.illinois.edu/ece420/sp2017/PSOLA.pdf).

**Why this matters here specifically**: the agent **already has an exemplar lexicon**
(the MCU-class exemplar recognizer; `speak()` already picks the most-heard sign). A
unit-selection / TD-PSOLA forward model would synthesize a candidate word by
**concatenating the agent's own stored exemplars**, pitch/duration-warped into
`voice(s)` — the *highest-fidelity possible* forward model because it is made of real
speech, and it is the natural generative read of the agent's existing exemplar store.
**Zero-fit**: yes (pitch marks + OLA, pure DSP). **Limit**: bounded by exemplar
coverage and concatenation artifacts ("buzzyness"); generalizes less than parametric
models, but is unbeatable on words the lexicon has heard.

### Donkey-only (flagged, OUT)

- **Neural vocoders** (WaveNet/WaveRNN/HiFi-GAN/etc.) and **neural TTS acoustic models
  (Tacotron/FastSpeech/VITS)** — trained nets. Inverting them in AxS = the agent's
  perception done by foreign weights. **OUT.** (They may appear *inside* otherwise-DSP
  pipelines, e.g. learned articulatory front-ends in VocalTrax/AAI — use the
  synthesizer, drop the learned head.)

---

## Part 2 — Expensive ANALYSIS transforms (→ the deliberate slow-path parse)

What the slow path can afford that the real-time front-end cannot. Same
classification; nearly all analysis DSP is zero-fit (the agent's gammatone/FFT/LPC
front-ends are the precedent).

### 2a. Reassigned / high-resolution spectrogram — compose-the-algorithm ★

Time-frequency reassignment uses the STFT **phase** to relocate each spectrogram bin
to the signal's true (t,f) support, sharpening far beyond the FFT
time-frequency tradeoff.
[Reassignment method, Wikipedia](https://en.wikipedia.org/wiki/Reassignment_method),
[Unified theory, arXiv 0903.3080](https://arxiv.org/abs/0903.3080),
[Fast/robust reassignment, MDPI](https://www.mdpi.com/2227-7390/7/4/358).
**Buys the parse**: sharp formant tracks and precise onset/burst timing — the
landmark positions the agent's scale-invariant spacing relation reads off
(`lpc_formant_representation`) become crisp instead of blurry. Directly attacks the
"gammatone wall / blurry-cochlea formant estimate" the memory flags as the bound on
speaker normalization. **Zero-fit**: yes (STFT + phase-derivative math).

### 2b. Glottal inverse filtering — IAIF / GFM-IAIF — compose-the-algorithm ★ (true source-filter SEPARATION)

IAIF iteratively separates **glottal source** from **vocal-tract filter** + lip
radiation: low-order all-pole glottis estimate → cancel it → LPC vocal tract → inverse-
filter to recover the glottal flow. GFM-IAIF adds a glottal-formant + spectral-tilt
pre-emphasis.
[GFM-IAIF, GitHub](https://github.com/operrotin/GFM-IAIF),
[Alku IAIF, ISCA](https://www.isca-archive.org/eurospeech_1991/alku91_eurospeech.html),
[COVAREP iaif.m](https://github.com/covarep/covarep/blob/master/glottalsource/iaif.m).
**Buys the parse**: genuine source/filter split. The vocal-tract estimate is the
speaker-/pitch-robust formant evidence; the recovered glottal flow is the **voice
identity** the AxS forward model needs for `voice(s)` — and it directly **fits the LF
source params** (1b), closing analysis→forward-model. It also extends the agent's
existing LPC (already in-repo) with the iterative source removal it currently lacks.
**Zero-fit**: yes (iterated LPC + inverse filtering, all DSP).

### 2c. Iterative pitch/formant refinement — RAPT / pYIN — compose-the-algorithm

pYIN = YIN difference-function + multiple candidates → **Viterbi-decoded HMM** for a
smooth, robust F0 track + voicing probability; RAPT = robust autocorrelation tracker.
[pYIN, IEEE](https://ieeexplore.ieee.org/document/6853678/),
[Essentia PitchYinProbabilistic](https://essentia.upf.edu/reference/std_PitchYinProbabilistic.html).
**Buys the parse**: an accurate f0 + voicing track is the input both the source model
(LF/Klatt) and the harmonic/aperiodic split (HNM/WORLD) depend on; the slow path can
afford the full candidate-set + Viterbi the fast path skips. **Zero-fit**: yes — the
HMM here is fixed transition priors + Viterbi (dynamic programming), **not trained
weights** (note: this is exactly the agent's own argmax/DTW-style dynamic-programming
family, so it is composable in spirit as well as fit-free).

### 2d. Multi-pass / iterative forced alignment — compose-the-algorithm (DP), in-thesis

Iterated DTW/Viterbi alignment between the heard signal and the synthesized candidate,
re-estimating boundaries each pass.
([AAI/AxS optimization with continuity terms, PMC3188964](https://pmc.ncbi.nlm.nih.gov/articles/PMC3188964/)
uses exactly this co-refinement structure.)
**Buys the parse**: this *is* the order-N loop's alignment step — re-aligning
heard↔synth each pass as the forward model converges (the memory's "order-N
analysis-by-synthesis: co-refine word-hypothesis + voice + boundaries jointly"). The
agent already has DTW (`DtwTo` Term, `recognition_graph.py:89`); multi-pass is
iterating it with boundary feedback. **Zero-fit**: yes (DP). **Donkey caveat**: only
if backed by a trained acoustic model (e.g. MFA's GMM/DNN) — use the **DP alignment
mechanism**, not a trained scorer.

### 2e. Iterative deconvolution (Lucy-Richardson) — compose-the-algorithm, niche

Iterative deconvolution to sharpen the spectral envelope / remove a known smearing
kernel. **Buys the parse**: marginal here — CheapTrick (2f) and reassignment (2a)
solve the envelope-sharpening need more directly for speech. **Zero-fit**: yes.
Lower priority.

### 2f. CheapTrick / D4C as analysis front-ends — compose-the-algorithm

Independently of using WORLD for synthesis, **CheapTrick** (pitch-robust spectral
envelope) and **D4C** (band aperiodicity) are excellent slow-path *analysis*
features: a pitch-synchronous-robust envelope (better formant evidence than the raw
gammatone) + a breathiness/voicing-by-band measure.
[D4C, ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0167639316300413).
**Zero-fit**: yes.

### Donkey-only (flagged, OUT)

- **Neural source separation / neural pitch (CREPE, SwiftF0, Demucs)** — trained nets.
  Use the **classical** RAPT/pYIN/IAIF equivalents instead. OUT as components of the
  agent's own parse.

---

## Part 3 — Ranking

### By AxS-bound payoff (most reduces the `speak()`-quality bound, composably)

1. **Klatt cascade/parallel formant synthesizer** (1a) — biggest accuracy gain per
   smallest step from the existing biquad voicebox; adds the three things the current
   model most lacks (cascade inter-formant amplitudes, zeros/nasals, true two-source +
   bandwidth control). Pure DSP, fully composable, exemplar-/trajectory-compatible.
2. **LF glottal source** (1b) — fixes the single crudest component (the `0.3/k` source);
   small, closed-form; drops straight into Klatt or the existing voicebox; supplies the
   `voice(s)` spectral-tilt identity AxS needs. Best paired with #1.
3. **TD-PSOLA / unit-selection over the agent's own exemplars** (1g) — highest possible
   fidelity *on heard words* and the natural generative use of the existing exemplar
   lexicon; bounded by coverage. The exemplar-native complement to the parametric #1/#2.
4. **Articulatory / Maeda tube model** (1c) — *highest accuracy ceiling* and the
   canonical AxS forward model (Part 1c precedent), with VTL-invariance built in; ranked
   below #1 only because it is the largest build and the most expensive solve. The
   right *eventual* slow-path forward model.
5. **LPC synthesis** (1d) — cheap, already half-owned; modest gain (all-pole only).
6. **WORLD / HNM** (1e/1f) — excellent quality but **descriptive/teacher-leaning**;
   better as analysis (Part 2) + as a copy-synth teacher than as the generative core.

### By slow-path parse payoff (best improves the deliberate parse, composably)

1. **Glottal inverse filtering (GFM-IAIF)** (2b) — true source/filter separation:
   speaker-robust vocal-tract formants **and** the glottal voice-identity, both of
   which the AxS forward model consumes; extends the agent's existing LPC. Highest
   parse leverage.
2. **Reassigned spectrogram** (2a) — directly dissolves the "blurry formant" wall that
   bounds the agent's spacing-relation features and speaker normalization.
3. **Multi-pass forced alignment (DP)** (2d) — *is* the order-N co-refinement loop;
   already partly owned (DtwTo).
4. **pYIN/RAPT F0 + voicing** (2c) — accurate excitation track feeding every source
   model; fit-free DP/Viterbi.
5. **CheapTrick/D4C analysis** (2f) — pitch-robust envelope + aperiodicity.
6. **Lucy-Richardson deconvolution** (2e) — niche; superseded by 2a/2f for speech.

---

## Part 4 — The single best upgrade of each kind (both composable, in-thesis)

### Best accurate forward-model upgrade: Klatt cascade/parallel synthesizer + LF glottal source

The agent already owns RBJ biquads (Klatt resonators are the same family) and an
exemplar lexicon mapping cleanly onto formant tracks, so this is the **smallest step
to the largest forward-model accuracy gain**, and it is entirely composable DSP with
zero fitted weights — squarely on the right side of the "synthesis algorithm = harvest,
TTS = donkey" line. It directly buys down the AxS bound by adding cascade
inter-formant amplitudes, anti-resonances (nasals), separate bandwidth control, and a
physically-shaped (LF) source carrying the per-speaker voice identity that AxS must
absorb into `voice(s)`. The **articulatory/Maeda model (1c)** is the higher ceiling and
the canonical AxS forward model — recommend it as the *next* step after Klatt+LF, since
the AxS-inversion literature (Panchapagesan & Alwan; VocalTrax) is built on exactly that
forward model.

### Best expensive analysis transform: Glottal inverse filtering (GFM-IAIF)

It is the one transform that produces **both** halves the slow-path parse needs from a
single principled source/filter separation: pitch-/speaker-robust vocal-tract formants
for phonetic identity, and the recovered glottal flow for voice identity — the latter
feeding the LF source params of the forward model and closing the analysis→synthesis
loop on one representation. It is a direct, fit-free extension of the LPC the agent
already has (iterated source removal it currently lacks). Pair with the **reassigned
spectrogram (2a)** as the second pick — it is the most direct attack on the blurry-
formant wall the project memory repeatedly flags as the bound on speaker
normalization.

---

## Honest separation: composable vs donkey-only, and where teacher is the only route

- **Composable, zero-fit (in-thesis, the agent composes its own forward model / parse)**:
  Klatt (1a), LF source (1b), articulatory/Maeda (1c), LPC synthesis (1d), TD-PSOLA/
  unit-selection (1g); reassignment (2a), IAIF/GFM-IAIF (2b), pYIN/RAPT (2c), multi-pass
  DP alignment (2d), Lucy-Richardson (2e), CheapTrick/D4C (2f). All are pure DSP /
  dynamic programming with no trained weights — same category as the agent's existing
  gammatone/FFT/LPC/DTW.
- **TTS-as-teacher is the only in-thesis route for**: high-end **WORLD/HNM** copy-synth
  quality when used as a *generative* reference (their parameterization is descriptive,
  so as a forward model they lean toward "resynthesize the analyzed signal" rather than
  "generate from lexical knowledge"); the agent grounds its own forward model by
  comparing against them in the babble loop rather than inverting them.
- **Donkey-only (OUT — inverting these = the agent's perception done by foreign weights)**:
  neural vocoders (WaveNet/HiFi-GAN/WaveRNN), neural TTS acoustic models
  (Tacotron/FastSpeech/VITS), neural pitch (CREPE/SwiftF0), neural source separation
  (Demucs), and any forced aligner whose *scorer* is a trained GMM/DNN. Where a useful
  classical pipeline ships with an optional learned head (VocalTrax/AAI front-ends),
  keep the composable synthesizer and drop the head.

## Sources

- Klatt, *Software for a cascade/parallel formant synthesizer*, JASA 1980 — https://www.fon.hum.uva.nl/david/ma_ssp/doc/Klatt-1980-JAS000971.pdf
- Berkeley Phonlab, Klatt synthesizer parameters — https://linguistics.berkeley.edu/plab/guestwiki/index.php?title=Klatt_Synthesizer_Parameters
- chdh/klatt-syn (closed-form JS implementation) — https://github.com/chdh/klatt-syn
- LF model / ARMAX-LF — https://arxiv.org/pdf/2410.04704 ; perceptual equivalence (JASA) — https://pubs.aip.org/asa/jasa/article/150/2/1273/615393/
- Maeda articulatory synthesis (TLCA tube model) — https://members.loria.fr/BElie/pages/artsynthesis.html ; airway modulation model (PMC) — https://pmc.ncbi.nlm.nih.gov/articles/PMC3596841/
- AxS acoustic-to-articulatory inversion (Maeda + chain matrices) — https://pmc.ncbi.nlm.nih.gov/articles/PMC3188964/ ; PubMed — https://pubmed.ncbi.nlm.nih.gov/21476670/
- VocalTrax (articulatory synthesis via optimization) — https://openreview.net/pdf?id=kIDxwvWznF
- WORLD vocoder (DIO/CheapTrick/D4C) — https://github.com/mmorise/World ; D4C (ScienceDirect) — https://www.sciencedirect.com/science/article/pii/S0167639316300413
- HNM — https://ieeexplore.ieee.org/document/379970/ ; Stylianou HNM — https://www.ee.columbia.edu/~dpwe/e6820/papers/Styl01-hnm.pdf
- TD-PSOLA / unit selection — https://learnius.com/slp/9+Speech+Synthesis/1+Fundamental+Concepts/2+Technologies/pitch-synchronous+overlap-add+(TD-PSOLA) ; PSOLA (Illinois) — https://courses.grainger.illinois.edu/ece420/sp2017/PSOLA.pdf
- Time-frequency reassignment — https://en.wikipedia.org/wiki/Reassignment_method ; unified theory (arXiv) — https://arxiv.org/abs/0903.3080 ; fast/robust (MDPI) — https://www.mdpi.com/2227-7390/7/4/358
- IAIF / GFM-IAIF glottal inverse filtering — https://github.com/operrotin/GFM-IAIF ; Alku IAIF (ISCA) — https://www.isca-archive.org/eurospeech_1991/alku91_eurospeech.html ; COVAREP iaif.m — https://github.com/covarep/covarep/blob/master/glottalsource/iaif.m
- pYIN — https://ieeexplore.ieee.org/document/6853678/ ; Essentia PitchYinProbabilistic — https://essentia.upf.edu/reference/std_PitchYinProbabilistic.html
