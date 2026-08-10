# The missing structural component: analysis-by-synthesis recognition

> Step-back-to-first-principles study of how human speech develops, what brain
> structures carry it, and which one our pipeline lacks. The wall is not "trained
> models have a bigger representation"; it is "the brain has an explicit
> structural component our pipeline does not". This document identifies that
> component and proposes what the agent would WRITE. **No build, no commit.**

## The measured wall (restated)

Our continuous large-vocab pipeline is bottom-up end to end:

```
gammatone → invariant_transform → per-speaker CMVN → k-means codebook
          → chunker (TP / landmark / dissimilarity-peak)
          → chunk→word lexicon (DTW / vote)
```

With GOLD word boundaries it still ceilings at within-speaker same-word
nearest-neighbour ~0.20 (`docs/model_mining_chunk_consistency.md`), versus a
trained SSL model at 0.49 (wav2vec2 GOLD layer-7) and a shallow CNN at 0.32, and
cross-speaker matching sits near chance. The gold-span control proved it is *not*
just boundaries — the representation/recognition is co-limiting.

The reframe driving this study: an SSL model's representational advantage is an
**implicit structure** — it was trained by *masked prediction* (HuBERT predicts
the cluster of masked frames; wav2vec2 contrastively predicts the true next
latent), so its representation IS a learned generative/predictive model of speech
([HuBERT](https://arxiv.org/pdf/2106.07447);
[Meta HuBERT](https://ai.meta.com/blog/hubert-self-supervised-representation-learning-for-speech-recognition-generation-and-compression/)).
The brain has that same predictive structure but **explicit and specialized**.
Our pipeline has neither. The question is therefore structural, and answerable.

---

## 1. The developmental / structural account (cited)

How an infant comes to perceive speech, and the brain structures that carry it.
Listed by how sharply each distinguishes the brain from a bottom-up acoustic
matcher (which is what we have).

### 1a. Analysis-by-synthesis / motor theory — recognition by inverting a forward model
Stevens & Halle's **Analysis by Synthesis (AxS)**: perception is a
*hypothesize-and-test* loop — the listener internally **synthesizes** candidate
signals from a generative (articulatory/word→sound) model and accepts the
hypothesis whose synthesis best matches the incoming acoustics; bottom-up
analysis and top-down synthesis jointly constrain the percept. The **motor
theory** (Liberman) is the strong form: perception is mediated by knowledge of
the gestures that *produced* the sound. Infant MEG evidence is direct: 7-month-olds
activate **motor** areas (Broca's, cerebellum) as well as auditory areas in
response to speech, and the motor engagement becomes language-specific by 11–12
months — "auditory analysis of speech is coupled with synthesis of the motor
plans necessary to produce the speech signal"
([Kuhl et al., PNAS 2014](https://www.pnas.org/doi/10.1073/pnas.1410963111);
[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4128155/);
[sensorimotor influences, PNAS 2015](https://www.pnas.org/doi/10.1073/pnas.1508631112)).

### 1b. Dual stream (Hickok–Poeppel) — a dedicated sound↔articulation forward map
The cortex carries **two** speech streams: a **ventral** stream mapping sound→meaning
(the "what" path), and a **dorsal** stream mapping the acoustic signal onto
**articulatory motor commands** (sound↔articulation), bidirectionally. The dorsal
stream is precisely the sensorimotor interface a forward/inverse model needs — it
exists as specialized neural hardware, not as a side-effect
([Hickok & Poeppel, Nat Rev Neurosci 2007](https://www.nature.com/articles/nrn2113);
[feedback-control / predictive-coding framing, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3468690/)).

### 1c. Top-down / predictive coding — lexical priors constrain the acoustics
Higher levels generate **top-down predictions** of lower-level responses;
perception minimizes prediction error. Behaviourally this is the **Ganong effect**
(ambiguous segments are heard as whatever makes a real word) and lexical
restoration; neurally, lexical status is predicted *before* word offset
([Sohoglu et al., J Neurosci 2012](https://www.jneurosci.org/content/32/25/8443);
[lexical influence is a temporoparietal circuit](https://pmc.ncbi.nlm.nih.gov/articles/PMC8286983/);
[causal frontal top-down contributions](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5735133/)).
**TRACE** is the canonical computational form: hierarchical feature→phoneme→word
layers with *bidirectional* connections so lexical knowledge reshapes sub-lexical
categorization.

### 1d. Categorical / phonemic perception + perceptual narrowing
Continuous acoustic variation is discretized into **learned** phoneme categories
(step functions at boundaries; the **perceptual-magnet effect** warps within-category
space toward prototypes). Categories are learned from the **distribution** of
inputs, and between 6–12 months the space **narrows**: native contrasts sharpen,
non-native ones fade
([Kuhl perceptual magnet](https://ilabs.uw.edu/sites/default/files/2000%20Iverson%20_%20Kuhl.pdf);
[perceptual narrowing, theta index](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3795304/)).

### 1e. Motor-auditory babble loop — production calibrates perception
Babbling runs the perception↔production loop: the infant produces a gesture,
*hears its own output*, and the mismatch between intended and perceived calibrates
both the forward model and the categories. This is what *builds* the dorsal-stream
forward model that AxS later inverts.

### 1f. Developmental trajectory as scaffolding
babble → distributional category formation → categorical perception + perceptual
narrowing → vocabulary explosion. The order matters: a stable forward model and
stable categories must exist *before* the lexicon explodes.

**The throughline:** 1a/1b/1c are all the *same structural idea* — a generative
forward model (word/gesture → predicted sound) that perception **inverts**, with
lexical priors steering the search. SSL nets approximate that structure implicitly
by training; the brain wires it explicitly (dorsal stream) and uses it actively
(AxS, predictive coding). **This is the component a bottom-up matcher fundamentally
lacks.**

---

## 2. Inventory — what we HAVE vs each component

| Developmental component | In our pipeline? | Where / gap |
|---|---|---|
| **1a. Analysis-by-synthesis recognition** (invert a forward model to recognize) | **NO** — the decisive gap | We *have* the forward model (`STTPipeline.speak`, `persona_speech_world.speak_as`) but it is used **only for output and self-monitoring**, never to recognize incoming audio. `transcribe`, `transcribe_via_votes`, `lexical_access`, `recognition_graph` are all pure bottom-up signature/vote/DTW matching. No code anywhere compares a *synthesized* candidate to *incoming* audio. |
| **1b. Dual stream / forward (word→sound) model** | **HALF** | The forward map exists and is **bidirectional in node identity** — `speak()` reads the same AcousticSign trajectory + A1-patch metadata the recognizer built, and Rust `synthesize_from_trajectory` voices it. So a generative word→sound path is present; it is simply not in the recognition loop. The "dorsal stream" hardware is there, unused for perception. |
| **1c. Top-down / predictive lexical prior** | **NO** | Recognition is `argmax_w Σ weight_f` (`recognition_graph.predict_term`) and per-sign votes — no lexical/contextual prior reshapes the acoustic decision, no Ganong-style "prefer a real word", no prediction of upcoming material. Bottom-up only. |
| **1d. Categorical perception** | **PARTIAL / weak** | `categorical_perception.py` does online leader-follower clustering of A1 patch vectors (the k-means-ish codebook). It has the *clustering* but not the prototype-warp/perceptual-magnet, and the categories are acoustic, never refined by production or lexical feedback. |
| Perceptual narrowing | PARTIAL (theory only) | Described in `speech_development.py` as a concept + a *future* pruning rule ("NOT YET WIRED"); not enacted. |
| **1e. Babble loop (production calibrates perception)** | **PARTIAL** | `motor_cortex` + `development_cortex` + `phonology` run a babble loop: synthesize a *response* word, re-ingest, and bump `motor_mismatch_count` when self-perception disagrees. But this monitors the agent's **own produced** word; it does not use synthesis to *recognize others' incoming* audio, and the mismatch tunes coherence metrics, not a forward model the recognizer inverts. |
| **1f. Trajectory scaffolding** | YES (as theory) | `speech_development.py` encodes the stages and the DevelopmentCortex self-directs babble rate / invention threshold. Good scaffolding; the thing being scaffolded (the inversion loop) is absent. |
| Speaker invariance (a *prerequisite*, not itself a brain component) | YES, and already mined | `invariant_units.py` (forward VTLN + CMVN), `xspeaker_norm.py` (per-speaker stats), `cmvn.py`, `coarticulation_predict_remove.py`. CMVN already lifted FSDD LOSO 0.417→0.578. |

**Crux of the inventory:** we have *every piece* required for analysis-by-synthesis
— a working forward model (`speak`), speaker-invariant features, a candidate
lexicon, DTW/predict-error machinery — but we have **never connected them into the
inversion loop**. The forward model points outward (talking) instead of being run
in reverse to perceive. That is one missing *wiring/structure*, not a missing
learned representation.

---

## 3. THE missing component(s), ranked

### #1 — Analysis-by-synthesis recognition (the generative-predictive inversion loop) — **build this**
**Mechanism.** Recognize a word not by matching its features to a stored signature,
but by asking, for each candidate word `w`: *if I synthesized `w` (in this
speaker's voice), how close would it be to what I actually heard?* Pick the `w`
whose synthesis minimizes prediction error. This is exactly AxS/motor-theory and
exactly what an SSL net's masked-prediction objective bakes in implicitly — except
here it is an explicit, inspectable loop reusing parts we already own.

**Why it attacks the 0.20 ceiling specifically.** Bottom-up same-word NN compares
two *acoustic instances* directly, so it inherits every nuisance (speaker, pitch,
coarticulation, segmentation jitter) — which is why even gold-span wav2vec2 only
reaches 0.49 and our matcher 0.20. AxS instead compares each instance against a
**canonical generated form**, so the comparison is *instance ↔ model* rather than
*instance ↔ instance*. The speaker-specific nuisances are absorbed into the
**forward model's parameters** (synthesize in the heard speaker's f0/VTL via the
`persona`/`speak_as` voice params we already pass), so the residual error is
dominated by *phonetic identity* — the only thing that should drive the decision.
This is the structural reason the brain can do cross-speaker recognition our
bottom-up matcher cannot: it normalizes by *re-generation*, not by feature
matching. It directly targets both the within-NN 0.20 ceiling and the
cross-speaker-at-chance failure.

### #2 — Top-down predictive lexical prior (Ganong / TRACE bidirectionality)
**Mechanism.** Let the lexicon bias the acoustic decision: `score(w) = acoustic_fit(w) + log prior(w | context)`. Add the prediction-of-upcoming as the
sequence model matures. This is cheap once #1 exists (it is just the prior term in
the same argmax) and is the second half of how the brain beats noisy acoustics.
Ranked below #1 because it *modulates* a decision; #1 *is* the decision and
delivers the bigger structural lift. Best built as a follow-on to #1.

### #3 — Production-calibrated categories (close the babble loop onto the forward model)
**Mechanism.** Use the existing babble loop's mismatch signal to *update the
forward model's per-word trajectory* (and split/merge categories), so synthesis
gets better and AxS error gets sharper over time — the developmental story of 1e.
This is the *learning* that makes #1 improve; it is the right long-run move but
depends on #1 being in place to have an error signal worth minimizing.

All three are the same structure at different time-scales: a forward model,
inverted for perception (#1), steered by priors (#2), and refined by self-production
(#3). None requires learned weights — they require **wiring the generator into the
recognition loop**.

---

## 4. Concrete build proposal for #1 (what the agent writes)

**Claim:** this is a missing *structure*, not a missing representation, because
every primitive it needs already exists and is graph-resident; the agent only
needs to **compose them into the inversion loop** — the same kind of forward-design
move recorded in `recognition_graph.py` and `runtime_design.py`.

**The recognition decision becomes (analysis-by-synthesis):**

```
predict(heard_sign s) =
    argmax over candidate words w  of  -synth_error(s, w)

synth_error(s, w) =
    DTW( features(s) ,  features( speak(w | voice(s)) ) )
```

where:
- `speak(w | voice(s))` = the existing forward model, called with the **incoming
  utterance's own** estimated f0 / VTL (we already estimate f0 in
  `stt_pipeline._estimate_f0`, and pass `f0_hz`/`q_factor`/`vtl_scale` through
  `persona_speech_world.speak_as`). Synthesizing *in the heard voice* is what
  cancels the speaker nuisance.
- `features(·)` = the same speaker-invariant front-end the bottom-up path already
  uses (gammatone → `invariant_units` VTLN+CMVN), so we compare like with like.
- `DTW(·,·)` = the distance machinery the chunk→word lexicon already uses
  (`lexical_access` distance, `mine_*` DTW).

**Primitives it composes (all present):**
- Forward model: `STTPipeline.speak` / `synthesize_from_trajectory` (Rust),
  driven by graph-resident AcousticSign trajectories + A1Patch metadata.
- Candidate set: the word Concepts already marked `is_word`
  (`recognition_graph.mark_words`, `NodesWhere`).
- The argmax-of-score Term-tree skeleton already exists
  (`recognition_graph.predict_term` = `Argmax(NodesWhere(...), w, score)`); the
  build **replaces the `score` sub-term** — from "Σ feature weights" to
  "−synth_error(s, w)". Same shape, new scorer; no new control flow.
- Voice parameters from the incoming utterance: `_estimate_f0` + the VTL/centroid
  estimate already in `invariant_units`/`xspeaker_norm`.
- New DSL Term needed (likely): a `SynthError` / `DtwTo` primitive in Rust
  (`runners/dsl/src/term.rs`) that, given a word node + a target feature buffer,
  synthesizes and returns the DTW distance — the one genuinely new *primitive*,
  because synthesis+DTW is not currently expressible as a Term. Per the
  architecture rule: **primitive in Rust, composition (the AxS argmax) in the
  graph.**

**How it lifts the wall, mechanically.** On the gold-span LibriSpeech benchmark
(`scripts/invariant_units_librispeech_accept.py`, `mine_ssl_goldspan.py`), replace
the within-NN *instance↔instance* metric with the *instance↔synthesis* AxS score
and re-measure same-word within- and cross-speaker accuracy. Expected lift comes
from two structural facts: (a) cross-speaker collapses because every comparison is
re-generated in the *target* voice; (b) within-speaker rises because the canonical
synthesis strips instance-specific coarticulation/segmentation jitter that
instance↔instance comparison cannot. The honest target is to move within-NN off
0.20 toward the 0.32–0.49 band that *correct structure* (not bigger nets)
reaches, and to move cross-speaker off chance — with every step inspectable,
unlike the SSL residue.

**Selector, per project rule (compression, not search).** AxS is selected because
it *compresses*: one forward model + the lexicon explains every heard instance,
versus storing/matching many acoustic exemplars. This is not a parameter sweep —
the forward model already exists; we are composing a structure justified by the
science, and compression is the selector that says it is the right structure.

---

## 5. Honest caveats

1. **The forward model's quality bounds the loop.** AxS can only be as good as
   `speak()`. Today `speak` voices the *most-heard* stored trajectory of a word; if
   that trajectory is poor, synth-error is noisy. This is real, but it is a
   *forward-model-quality* problem (addressed structurally by component #3, the
   babble loop refining trajectories), **not** a "need learned weights" problem —
   and even an imperfect forward model should beat instance↔instance matching on
   cross-speaker, because re-generation in the target voice is the part bottom-up
   matching structurally cannot do.

2. **Cost.** AxS evaluates a synthesis+DTW per candidate word. Fine for the
   digit/small-vocab benches; large-vocab needs the bottom-up path as a *fast
   first pass* that proposes a shortlist, then AxS *re-ranks* — which is in fact
   how predictive coding works (cheap prediction, expensive only on error). Build
   AxS as a re-ranker over the existing recognizer's top-k; that also keeps the
   current pipeline as the regression baseline.

3. **What genuinely cannot be had without learning.** The *distributional category
   formation* of 1d at scale (carving the full native phoneme inventory from raw
   distribution) and the *refinement* of the forward model (#3) are learning
   processes. But they are learning in the project's sense — graph-resident
   category/trajectory updates from the agent's own mismatch signal (the babble
   loop already produces this signal) — **not** gradient-descent weight training.
   The AxS *structure* itself (#1) needs no learned weights; only its long-run
   sharpening does.

4. **#2 and #3 depend on #1.** The lexical prior (#2) is a term in the AxS argmax,
   and the production-calibration (#3) needs the AxS error to have something to
   minimize. Build #1 first; the other two are small follow-ons on the same
   structure.

---

### One-line answer
We are missing **analysis-by-synthesis recognition**: the brain recognizes speech
by *inverting a generative forward model* (dorsal-stream word→sound) under
top-down priors; an SSL net hides that same predictive structure inside trained
weights; **we have the forward model (`speak`) but only ever point it outward**.
Wiring it into the recognition loop — synthesize each candidate in the heard voice
and pick the minimum prediction error — is a missing *structure the agent can
write* from primitives it already owns, and it attacks the 0.20 within-NN ceiling
and cross-speaker-chance failure at their structural root (compare instance↔model,
not instance↔instance).
