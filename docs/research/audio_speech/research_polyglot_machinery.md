# The polyglot machinery: a language-general representation that builds over time

> Step-back study triggered by the user's redirect. Iters 23–28 hand-composed
> static DSP / CPWL features (scale-invariant relation, LPC-formant relation,
> stacked, weighted-channel, composed poly+predres net) and **none beat the
> baseline**. The diagnosis those iterations point to is not "we need yet another
> fixed representation" — it is that the representation itself is the wrong KIND of
> object. The right model is the machinery of people who learn languages easily:
> **a representation that is built over time from input and stays general across
> languages**, not a single fixed front-end implicitly tuned to one dataset.
> **No build, no commit.** This is the synthesis the user asked for.

This document deliberately does NOT re-derive analysis-by-synthesis recognition —
that is already covered in `speech_development_missing_component.md` (the missing
*recognition* structure). The redirect here is a different and complementary axis:
the missing **representation-building** structure. AxS inverts a forward model to
*recognise*; this is about how the *features the forward model and recogniser both
read* should come into existence developmentally rather than be frozen DSP.

---

## 1. The polyglot / general-acquisition machinery (components + mechanism)

The hyperpolyglot literature is mostly about *efficiency* of an already-acquired
network, but the load-bearing finding for us is the *acquisition* machinery, and it
decomposes cleanly. The throughline: **good language learners keep, or can
re-open, a language-general phonetic space, and they carve new categories from the
distribution of input quickly.** It is a property of the *learning process*, not a
bigger stored representation.

### 1a. A language-GENERAL phonetic space, and perceptual narrowing as the loss of it
Young infants are **"universal listeners"**: they discriminate essentially all
languages' phonetic contrasts via detailed acoustic analysis. Between ~6 and 12
months they **narrow** — native contrasts sharpen, non-native ones fade — as the
brain builds language-specific phonemic maps
([Werker/perceptual narrowing review, J Neurosci 2016](https://www.jneurosci.org/content/36/48/12095);
[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6601985/)).
Narrowing is *adaptive* (efficient native processing) but it is also exactly the
thing that makes a *second* language's contrasts hard later. **The polyglot
property is resisting or re-opening this narrowing** — keeping the space general
enough to admit a new language's sounds.

Mechanistically, "general" means the representation is **not collapsed onto one
language's category boundaries**. The space is kept by *continued exposure to
variability* and by *not committing the lower-level acoustic representation to a
single category partition*. This is the crux for us: narrowing is a property of how
much the representation has *specialised*, and generality is a property of keeping
the lower layers under-committed while category structure lives in a separate,
re-learnable layer.

### 1b. Fast distributional category-formation
New categories are carved from the **statistical distribution** of the input.
Maye, Werker & Gerken (2002): 6–8-month-olds exposed to a **bimodal** VOT
distribution learn two categories; the same continuum presented **unimodally**
yields one. The *shape of the distribution*, not labels, drives category formation
([Maye et al. 2002, PDF](https://linguistics.berkeley.edu/~kjohnson/ling290e/maye_werker_gerken_2002.pdf)).
Kuhl's infant-directed-speech work shows caregivers *stretch* the vowel space so the
modes are further apart, **enhancing** the distributional signal
([IDS & category learning, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3874452/)).
What makes it *fast* in good learners: a shared underlying **"phonetic plasticity"**
capacity — good learners of native phonetic variation are also good learners of
*non-native* contrasts, and the capacity correlates with vocabulary, working
memory, and word-in-noise comprehension
([neurocognitive model of aptitude, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10158630/)).
Domain-general **auditory processing** acuity predicts adult L2 pronunciation
success longitudinally
([Cambridge Core](https://www.cambridge.org/core/journals/applied-psycholinguistics/article/abs/domaingeneral-auditory-processing-determines-success-in-second-language-pronunciation-learning-in-adulthood-a-longitudinal-study/F5F2BB4E9F2AA771EB2DD7184E406E86)).
So the fast carver = a good front-end acuity + a distribution-fitting category
former, kept plastic.

### 1c. The representation is BUILT OVER TIME from input (the developmental analog of SSL)
The auditory representation is **shaped by the input statistics over development**,
not innate-and-fixed. The SSL analog is exact and load-bearing: wav2vec2/HuBERT
build their representation by **masked prediction** (predict the quantised
unit/latent of masked frames), so their representation *is* a learned
predictive/generative model of speech, discovered by **iterated clustering**
(HuBERT clusters MFCCs → trains → re-clusters its own learned latents → re-trains)
([HuBERT, arXiv 2106.07447](https://arxiv.org/abs/2106.07447)).
The brain does the same thing developmentally and explicitly: predictive coding +
the babble loop build the representation from input over time. **The representation
is a product of a process, not a designed artifact.** This is precisely the
property iters 23–28 lacked — they designed the artifact directly.

### 1d. Convolution / hierarchical cortical processing (biologically grounded, within the thesis)
The cochlea and auditory cortex are **convolutional and hierarchical**. Cortical
responses are characterised by **spectrotemporal receptive fields (STRFs)** — local
filters convolved across the time–frequency surface — and they are **hierarchically
organised**: early areas encode fine acoustic detail, later areas encode abstracted,
intelligibility-relevant patterns, with distinct regions tuned to phoneme/syllable
vs word/phrase timescales
([Hierarchy of speech-driven STRFs, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6338500/)).
A **hierarchical sparse-coding model** trained on cochleagrams reproduces this:
lower-layer STRFs resemble inferior colliculus, upper layers resemble cortex
([hierarchical sparse coding, PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6386396/)).
**This is the licence for a small composed conv net**: convolution is what the
biology *is*, so an authored convolutional hierarchy is within the thesis, not an
imported ML trick. (The agent already half-believes this — its A1 patch library is
a 5×5 spectrotemporal modulation bank per Schädler & Kollmeier, i.e. a hand-placed
convolutional layer; see `auditory_cortex.py`.)

### 1e. Variability is the fuel (HVPT) — the engineering proof of 1a–1c
The adult-trainability result that ties it all together:
**High-Variability Phonetic Training**. Adults learn non-native contrasts (the
classic Japanese /r/–/l/) and **generalise to new talkers and contexts** only when
trained on **multiple talkers**; single-talker training improves the trained talker
but **does not generalise** (Logan/Lively/Pisoni 1991–1993; meta-analysed
effective)
([HVPT meta-analysis, Cambridge](https://www.cambridge.org/core/journals/studies-in-second-language-acquisition/article/high-variability-phonetic-training-hvpt-a-metaanalysis-of-l2-perceptual-training-studies/6ABB8C1F32D88D53EA8D05A4565E76F6);
[Thomson HVPT overview, PDF](https://languagelog.ldc.upenn.edu/myl/2018Thomson_HVPT.pdf)).
This is the single most actionable mechanism: **generalisation requires
across-speaker variability in the input during representation-building.** A
representation tuned on one dataset's speakers is the single-talker failure mode by
construction — which is exactly what the agent's front-end is.

**The machinery, in one paragraph.** A language-general learner has (i) a good,
*under-committed* lower acoustic representation (general; not collapsed onto one
language's boundaries), (ii) a *separate* category layer carved fast from the
*distribution* of input, (iii) the whole thing *built over time by a predictive /
self-production loop*, (iv) realised as a *convolutional hierarchy*, and (v) kept
general by *across-speaker variability* in the input. Polyglots differ from
monolinguals not by storing more, but by keeping (i) plastic and (ii) re-learnable,
with strong (iii).

---

## 2. Have vs missing — the machinery against the agent's pipeline

The agent's speech path (per `stt_pipeline.py`, `invariant_units.py`,
`auditory_cortex.py`):

```
gammatone (32 log bands, fixed) → A1 patch bank (25 fixed STRF patches)
   → invariant_transform (VTLN + CMVN + predict-remove, fixed math)
   → k-means-ish codebook / leader-follower clustering (categorical_perception)
   → lexicon (DTW signatures, refine_lexicon merges post-hoc)
```

| Polyglot component | In the agent? | Where / the gap |
|---|---|---|
| **1a. Language-GENERAL, under-committed lower representation** | **NO** | The front-end (gammatone bands, A1 patch centres/sigmas/slopes, VTLN canonical centroid, CMVN) is a **fixed artifact**. `canonical_log_centroid` is computed from the *cohort* (one dataset) and every utterance is warped *to it* — the representation is **committed to one speaker pool by construction**. There is no notion of "general phonetic space" vs "this language's partition"; there is only one frozen space. |
| **1b. Fast distributional category-formation** | **PARTIAL** | `categorical_perception.py` does online leader-follower clustering (a distribution-sensitive carve), and `speech_development.py` *names* `feature_invention` (split a feature when its distribution goes bimodal). But the carve runs **on the frozen front-end's output**, and the bimodal-split rule is theory ("NOT YET WIRED"). No perceptual-magnet/prototype warp. |
| **1c. Representation BUILT OVER TIME from input** | **NO — the decisive gap for the redirect** | The agent HAS the loop machinery — babble (`motor_cortex` + `development_cortex`), `speech_development` stages, statistical-learning concepts, a forward model (`STTPipeline.speak`), net-composition (`code_writing_cortex` CPWL gadgets) — **but none of it builds the representation.** The babble loop tunes *coherence metrics and recognition predicates*; `refine_lexicon` iterates *clustering on the lexicon* (a HuBERT-flavoured move, but on top of a frozen front-end); the composed nets (iters 26–28) are *authored once with fixed weights*, never grown from input. The developmental loop and the representation are **wired to different things**. |
| **1d. Convolutional / hierarchical representation** | **PARTIAL (one fixed layer)** | The A1 patch bank IS a convolutional STRF layer (`auditory_cortex.py`, 5 centres × 5 modulation variants, biology-cited). But it is **one hand-placed layer, fixed**; there is no *hierarchy* (no second conv layer reading the first), and the patches are not *grown from input*. The CPWL machinery (`code_writing_cortex.construct_broadcast_pattern` / `_render_heteroparallel` / `construct_multiplexer`) can *render* layered ReLU nets exactly, so the *constructor for a hierarchy exists* — it has just never been pointed at building a multi-layer conv representation. |
| **1e. Variability-driven generality (HVPT)** | **NO (and actively countered)** | `persona_speech_world.py` is the right world — the agent controls multiple voices (f0/q/vtl) and re-hears itself, i.e. it can *generate across-speaker variability*. But (a) it is used for self-monitoring, not to build a general representation, and (b) the front-end's per-cohort `canonical_log_centroid` **removes** speaker variability by warping everyone to one tract — the opposite of HVPT. The single-talker failure mode is baked in. |
| Perceptual narrowing as a *controllable* knob | NO | Narrowing is described in `speech_development.py` but un-wired. There is no "keep the lower layer general / only narrow the category layer" distinction — there is only one frozen layer, so narrowing-vs-generality is not even expressible yet. |

**Crux.** The agent owns *all five ingredients separately* — a convolutional first
layer, a distributional category former, a babble/forward-model loop, multi-voice
variability generation, and an exact net constructor — but they are **wired to
recognition and self-monitoring, never to building the representation**, and the
one representation that exists is **frozen and committed to one speaker pool**. The
redirect is exactly right: the missing thing is not a better fixed feature; it is
**the process that grows a general representation from input**, which the agent has
the parts for and has never assembled.

---

## 3. The proposed deeper system: a developmentally-grown, language-general convolutional representation

A representation that (i) **builds over time** via the agent's own developmental
loop, (ii) **composes a convolutional hierarchy** (authored, not gradient-fit), and
(iii) **stays general** (admits any language's sounds; not warped onto one cohort).
Built from machinery the agent already has.

### 3.1 Structure: a two-layer convolutional hierarchy with a SEPARATE category layer
- **Layer 0 (fixed, biological):** the gammatone cochleagram. Keep as-is — it is the
  ear and is *already* the language-general substrate (Whisper-mine showed it is the
  stronger raw representation; the gap was downstream).
- **Layer 1 (convolutional, GROWN):** STRF patches over the cochleagram — the
  current A1 bank, but its patch inventory **grown from the input distribution**
  rather than hand-placed. This is `feature_invention` (split a patch when the
  responses it pools go bimodal) applied to the *representation* layer, finally
  wired. Realised via the existing CPWL constructor: each patch is a leaf gadget;
  `construct_broadcast_pattern` lays them out as a conv layer; adding a patch =
  adding a leaf and re-rendering (exact, no fit).
- **Layer 2 (convolutional, GROWN):** a second STRF layer reading Layer 1 over a
  longer temporal window (phoneme/syllable timescale, per the cortical hierarchy of
  §1d). `_render_heteroparallel` already block-diagonally composes a second layer of
  different gadgets each reading their own slice — the hierarchy constructor exists.
- **Category layer (SEPARATE, re-learnable):** the leader-follower clusterer of
  `categorical_perception.py`, run on Layer 2 — **but kept distinct from the layers
  below it.** This is the §1a move: the lower representation stays general
  (under-committed); only this layer partitions into *a* language's categories, and
  it can be re-partitioned for a new language without disturbing Layers 1–2.

### 3.2 How it builds OVER TIME (the within-thesis analog of SSL masked prediction)
The agent's babble/forward-model loop is the developmental engine; point it at the
**representation** instead of at recognition metrics:

1. **Predict-and-check as the build signal (SSL analog, no gradient).** The agent
   already composed the predictive-residual move (`composed_net_representation.py`:
   `b_t − b̂(b_{t-1})`) and owns a forward model (`speak`). The masked-prediction
   objective becomes: a Layer-1/2 patch is *kept/added* when it **reduces the
   prediction error** of masked frames (predict a held-out frame's Layer-1 response
   from its neighbours; a patch that lowers that residual carries real structure).
   This is HuBERT's "iterate clustering on better features" turned into a
   **graph-resident grow/keep rule selected by compression** — the project's
   selector — not a backprop loss. `refine_lexicon` already does the iterated-cluster
   move on the lexicon; this lifts the *same move* down to the representation.
2. **Variability is the input (HVPT, §1e).** Drive the loop from
   `persona_speech_world` across **all** personas (and, when available, real
   multi-speaker corpora) so the representation is built from across-speaker
   variability. A patch/category survives only if it is **stable across voices** —
   the structural definition of speaker-invariant, and the HVPT generalisation
   condition. This *replaces* the per-cohort `canonical_log_centroid` warp (which
   destroys variability) with **invariance-by-survival-across-variability**.
3. **Grow, don't tune.** Each developmental cycle: present varied input → measure
   per-patch prediction-error reduction and cross-voice stability → `feature_invention`
   adds/splits a patch (re-render via CPWL, exact) → category layer re-clusters.
   The representation **accretes** — the same accretion path as `runtime_design`
   (one authored primitive, then more), but for perceptual features. Capability is
   binary/phase-transition (per the memory thesis), so the metric is *configuration
   advancement* (patches that earn their keep, cross-voice stability rising), not a
   smooth accuracy curve.

### 3.3 How it stays GENERAL (resists narrowing)
The §1a separation is the mechanism: **Layers 1–2 are grown to predict/reconstruct
*all heard speech across all voices*** (a language-general objective — survive
everywhere), while **only the category layer narrows** to the current language's
partition. A new language re-runs distributional clustering on the *same* Layer-1/2
representation (re-opening = re-partition the top layer, not rebuild the front-end)
— the polyglot property, made structural. Narrowing becomes a *controllable knob*
(`speech_development.perceptual_narrowing`, finally wired) that prunes **category**
nodes, never **representation** patches.

### 3.4 Where each piece already lives (nothing exotic is required)
- Conv layer + render: `auditory_cortex.attach_a1_pipeline` (patches) +
  `code_writing_cortex.construct_broadcast_pattern` / `_render_heteroparallel`
  (exact ReLU rendering of a layered conv net, no fit).
- Grow rule: `speech_development.feature_invention` (un-wired) +
  `development_cortex` (already self-directs invention threshold).
- Predictive build signal: `composed_net_representation` (predictive residual) +
  `STTPipeline.speak` (forward model) + `refine_lexicon` (iterated-cluster pattern
  to lift down one level).
- Variability input: `persona_speech_world.speak_as` across `DEFAULT_PERSONAS`.
- Selector: compression / cross-voice survival (project rule), not a sweep.

---

## 4. The single most promising first concrete step

**Wire `feature_invention` to the Layer-1 conv patch bank, driven by cross-voice
prediction-error reduction, and select patches by survival-across-personas — then
measure whether a *grown* patch bank generalises cross-speaker where the *fixed*
one does not.**

Concretely, the smallest honest experiment: take the existing A1 patch bank as the
seed Layer 1; run the babble/persona loop over **all four personas** (and a held-out
fifth voice never seen during growth); use the predictive-residual signal to
add/split patches that lower masked-frame prediction error **and are stable across
the four training voices**; render each via the CPWL constructor; then test
same-word matching on the **held-out voice**. The claim under test is the HVPT
claim: a patch bank grown under across-speaker variability generalises to the unseen
speaker, whereas the cohort-warped fixed front-end does not. This isolates the *one*
new idea (grow-the-representation-under-variability) on the agent's existing
benchmark, keeps the current front-end as the regression baseline, and needs no
gradient training — every patch is rendered exactly by the existing constructor and
*kept* by the compression/survival selector.

This is the right first step because it is the *minimum* that turns a fixed
representation into a built one, it exercises the exact gap (§1c + §1e), and its
result is interpretable as the polyglot property (generalise to a new voice) rather
than as a benchmark delta.

---

## 5. Honest caveats — where it needs the open weight-constructor, where the line is

1. **Growing the patch *inventory* is in-thesis; growing patch *shapes continuously*
   may not be.** Adding/splitting a discrete patch and re-rendering via CPWL is exact
   authoring (write-not-train). But if "grow over time" comes to mean *continuously
   adjusting each STRF's coefficients to reduce prediction error*, that **is**
   gradient descent on weights — the open **autonomous weight-constructor** problem
   (the agent has no architecture-vocabulary to *score* and *adjust* arbitrary
   weight tensors; per memory, from-scratch weight construction is the open
   problem). The honest line: **grow the inventory and the layout by discrete
   accretion (in-thesis); do not slide into continuous weight-fitting (out-of-thesis
   until the constructor exists).** Where a continuous coefficient genuinely helps,
   prefer a *discrete library of authored gadgets* the agent selects among, not a
   fitted filter.

2. **Perceptual-narrowing-vs-generality bites at the category layer.** Keeping
   Layers 1–2 general while the category layer narrows is clean *in principle*, but
   the two are coupled: a patch that earns its keep on one language's distribution
   may be the wrong basis for another. Real generality may require the *lower* layer
   to also grow when a new language arrives — at which point "general" is only
   "general over the languages seen so far," exactly the polyglot's actual limit
   (they re-open plasticity; they are not born omni-lingual). Claim "language-general
   over the exposure set," not "universal."

3. **The forward-model / predictive signal bounds the build, as it bounds AxS.**
   The grow-by-prediction-error signal is only as good as the predictor. With the
   trivial 1-step predictor (`b̂_t = b_{t-1}`) the signal is weak; a richer predictor
   is itself a representation-building problem (circular). The babble loop refining
   the forward model (component #3 of the missing-component doc) is the co-dependent
   partner — representation-building and forward-model-refinement improve together,
   which is correct developmentally but means **neither bootstraps cleanly alone.**

4. **The no-big-net line, precisely.** A *small composed conv hierarchy* (a handful
   of authored STRF patches per layer, two layers, rendered exactly from gadget
   formulas) is in-thesis — it is what the cortex *is* (§1d) and it is *authored*,
   not trained. The line is crossed when (a) the layer count / patch count grows to
   where the inventory can only be set by fitting (you can no longer say *why* each
   patch exists), or (b) the weights are set by an optimiser rather than rendered
   from a formula or selected from a library. **Convolution: yes. Hierarchy: yes,
   shallow. Grown inventory: yes, by discrete accretion. Gradient-fit weights at
   scale: no — that is the other project.**

5. **The selector is everything, and overfitting is the failure mode (per memory).**
   Raw discrimination overfits (spread=1.0 on noise); the right selector is
   compression / cross-voice survival. A patch that lowers prediction error on the
   training voices but does not survive the held-out voice must be *rejected*, or the
   grow loop just memorises the cohort — the very failure the whole redesign is meant
   to escape. The cross-voice held-out test in §4 is not optional polish; it is the
   selector's validity check.

---

### One-line answer
The polyglot machinery is **a language-general lower representation that is built
over time from across-speaker variability by a predictive/self-production loop, with
category structure carved fast and separately on top** — and the agent has every
part (a convolutional first layer, a distributional category former, a babble +
forward-model loop, multi-voice variability, and an exact net constructor) but has
**wired them to recognition instead of to building the representation**, leaving one
frozen front-end committed to a single speaker pool. The deeper system grows the
conv hierarchy by discrete accretion under cross-voice prediction-error/compression
selection (the within-thesis analog of SSL masked prediction), keeps the lower
layers general while only the top layer narrows, and is testable today by the HVPT
claim: a grown-under-variability patch bank should generalise to an unseen voice
where the cohort-warped fixed front-end cannot.

---

## Sources
- Werker / perceptual narrowing: [J Neurosci 2016](https://www.jneurosci.org/content/36/48/12095) · [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6601985/)
- Distributional learning (Maye/Werker/Gerken 2002): [PDF](https://linguistics.berkeley.edu/~kjohnson/ling290e/maye_werker_gerken_2002.pdf) · IDS enhancement: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3874452/)
- Language aptitude / phonetic plasticity: [Neurocognitive model, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10158630/) · [Sensitive periods & plasticity, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3834520/) · [Domain-general auditory processing predicts L2, Cambridge](https://www.cambridge.org/core/journals/applied-psycholinguistics/article/abs/domaingeneral-auditory-processing-determines-success-in-second-language-pronunciation-learning-in-adulthood-a-longitudinal-study/F5F2BB4E9F2AA771EB2DD7184E406E86)
- SSL / masked prediction (HuBERT): [arXiv 2106.07447](https://arxiv.org/abs/2106.07447)
- Convolutional / hierarchical auditory cortex (STRFs): [Hierarchy of speech-driven STRFs, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6338500/) · [Hierarchical sparse coding, PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6386396/)
- High-Variability Phonetic Training (Logan/Lively/Pisoni; meta-analysis): [Cambridge meta-analysis](https://www.cambridge.org/core/journals/studies-in-second-language-acquisition/article/high-variability-phonetic-training-hvpt-a-metaanalysis-of-l2-perceptual-training-studies/6ABB8C1F32D88D53EA8D05A4565E76F6) · [Thomson HVPT overview, PDF](https://languagelog.ldc.upenn.edu/myl/2018Thomson_HVPT.pdf) · [High vs low variability, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5452958/)
- Hyperpolyglot network efficiency: [Small/efficient language network, PubMed](https://pubmed.ncbi.nlm.nih.gov/32820332/) · [bioRxiv precision-fMRI](https://www.biorxiv.org/content/10.1101/2023.01.19.524657.full.pdf)
</content>
</invoke>
