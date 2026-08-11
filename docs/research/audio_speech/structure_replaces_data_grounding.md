# Structure replaces data: grounding the analytic-prior frontier for speech

**Research spike** — grounds the one direction in speech representation
learning genuinely *different* from current self-supervised learning (SSL):
the regime where strong **earned/analytic priors (inductive bias)** reduce
the **data** required, rather than buying accuracy with ever more unlabeled
audio.

The thesis under test: *maximise earned analytic structure (strong priors)
so the data-hungry learned part shrinks — "lossy-but-right" = strong priors,
not more data.*

This project's own measured findings frame why this matters:

- A self-supervised predictive representation (APC / "predict-to-recover")
  is **label-efficient** (~8–16× fewer labels) but **unlabeled-hungry exactly
  like SSL** — it keeps improving with more unlabeled audio, no early
  saturation. The learned predictive net is *SSL-shaped*, not a new frontier.
- The **only** lever that beat the unlabeled-data floor was
  **compose-not-train**: an analytic basis (per band `b → [b, b², b³,
  b_t − b̂(b_{t−1})]` = local-polynomial lift + predictive residual) gave
  **+7% per-frame phone accuracy with ZERO unlabeled data.**

That measured +7%-from-zero-data result is exactly the phenomenon the
literature below explains and predicts. This doc establishes (a) the
principle, (b) a ranked list of analytic priors most likely to buy back the
most data — each mapped to a gap the agent (`jabberwock`) has already named,
and (c) honest caveats, including the bitter-lesson counterargument.

---

## (a) The principle — when analytic structure substitutes for data

### Why a prior is *necessary*, not optional

Generalization beyond the training set is impossible without an inductive
bias. Mitchell's foundational result states it plainly: an inductive bias is
"any basis for choosing one generalization over another, other than strict
consistency with the training instances," and **biases are necessary for the
inductive leap** — a structure-free learner cannot generalize beyond its data
at all (Mitchell 1980, *The Need for Biases in Learning Generalizations*,
CMU/Rutgers CBM-TR-117,
https://www.cs.cmu.edu/~tom/pubs/NeedForBias_1980.pdf).

The No-Free-Lunch theorem makes the same point from the other side: averaged
over *all* possible target functions, every learning algorithm has identical
off-training-set error — above-chance generalization is purchased *entirely*
by an inductive bias that matches the target (Wolpert 1996, "The Lack of A
Priori Distinctions Between Learning Algorithms," *Neural Computation* 8(7):
1341–1390,
https://direct.mit.edu/neco/article/8/7/1341/6016/). The defensible reading
is the weaker one: "there is no universal data-only learning algorithm …
every mechanical learning procedure must possess an inductive bias"
(Sterkenburg & Grünwald 2021, "The no-free-lunch theorems of supervised
learning," *Synthese* 199: 9979–10015,
https://link.springer.com/article/10.1007/s11229-021-03233-1).

Crucially, NFL does *not* forbid a *universally useful* low-complexity prior
on **real** data: the uniform-labeling assumption that powers NFL "ensures
training data is uninformative," but "relevant real-world datasets are highly
compressible" — so a simplicity/Solomonoff prior is broadly useful precisely
because natural data has structure (Goldblum, Finzi, Rowan & Wilson 2024,
"The No Free Lunch Theorem, Kolmogorov Complexity, and the Role of Inductive
Biases in Machine Learning," ICML 2024, https://arxiv.org/abs/2304.05366).
**This is the licence for the whole approach: speech is compressible — has
known physical structure — so a prior that encodes that structure is
legitimately, not coincidentally, data-saving.**

### How much data a prior buys back — the quantitative shape

The cleanest theoretical statement: in PAC learning, **sample complexity
scales linearly with the VC dimension** of the hypothesis class. A consistent
learner PAC-learns with `m ≥ O((d·log(1/ε) + log(1/δ)) / ε)` examples, and a
matching lower bound `Ω(d/ε)` holds — so VC dimension *characterizes* sample
complexity (Shalev-Shwartz & Ben-David 2014, *Understanding Machine
Learning*, Ch. 6, Fundamental Theorem of Statistical Learning,
https://www.cs.huji.ac.il/~shais/UnderstandingMachineLearning/understanding-machine-learning-theory-algorithms.pdf).
A stronger inductive bias = a smaller, more-constrained hypothesis class =
smaller `d` = **proportionally less data**. Halving effective hypothesis-class
complexity halves the data needed.

The Bayesian literature gives this a literal unit: a prior's **effective
sample size (ESS)** equates it to a number of equivalent observations —
`ESS ≈ (between-subjects SD / prior SD)²`; a tighter prior is worth more
equivalent data points, which can be subtracted from the required N
(Wiesenfarth & Calderazzo 2020, "Quantification of prior impact in terms of
effective current sample size," *Biometrics* 76(2): 626–636,
https://onlinelibrary.wiley.com/doi/full/10.1111/biom.13124). The same source
flags the key limit — **the buyback shrinks when the prior conflicts with the
data.**

What generalizes (and the right object of the prior): "generalization depends
largely on two properties: the **support** and the **inductive biases** of a
model" — capacity alone does not determine generalization, and the relevant
prior is the **function-space** prior, not the parameter prior (Wilson &
Izmailov 2020, "Bayesian Deep Learning and a Probabilistic Perspective of
Generalization," NeurIPS 2020, https://arxiv.org/abs/2002.08791). For speech,
the function-space prior is articulatory/acoustic physics.

### The principle, stated

> **Analytic structure substitutes for data to the exact extent that the
> structure is (1) *true* of the domain's generative process and (2) *not*
> already trivially recoverable from the data the learner has.** Where a
> domain has a known, low-dimensional generative physics (speech production)
> and a known efficient encoding (the cochlea), a prior encoding that physics
> collapses the hypothesis space the learner must search — buying back data
> proportional to how much of the variance the prior explains. The prior's
> value is largest in the low-data regime and *negative* when the prior is
> misspecified.**

This is why APC stayed SSL-shaped (it *learns* the predictive structure from
data, paying the unlabeled-data cost) while the analytic basis gave +7% from
zero data (it *encodes* the predictive structure as the residual term
`b_t − b̂(b_{t−1})` — a free, exact prior).

---

## (b) Ranked analytic priors — most data bought back, mapped to the agent's gaps

The agent has already named its own gaps in its `speech_science` theory:
**formants, source_filter_theory, place/manner_of_articulation,
coarticulation, lack_of_invariance, distributional_learning** — plus the
keystone principle **"shape = a residual-feedback recurrence"** (= predictive
coding). Each prior below is mapped to the gap(s) it fills and to the
data-efficiency evidence for it.

Ranking is by expected data bought back for **per-frame / per-phone
recognition**, weighting (i) strength of evidence that the structure is true
of speech, (ii) directness of the recognition payoff, (iii) how much the prior
is *free* (analytic, zero-data) vs. itself needing fitting.

---

### 1. Efficient-coding cochlear front end (gammatone / auditory filterbank)
**Fills: the un-named substrate prior under all of perception — the input
representation itself.** (Most of the project's front-end iterations.)

The strongest "structure is true of the domain" evidence in the whole stack.
Filter shapes **derived** by optimizing coding efficiency on natural-sound
statistics *reproduce* the cochlea: optimizing a filter population to encode
natural sounds efficiently "accounts for" auditory-nerve-fiber tuning
properties, and the optimal code follows the **scaling characteristics of
physiological data** only when optimized on the full mix of natural sounds
(Lewicki 2002, "Efficient coding of natural sounds," *Nature Neuroscience*
5(4): 356–363, https://www.nature.com/articles/nn831). Optimizing features
for natural sounds/speech yields filters with "striking similarities to
time-domain cochlear filter estimates" and "frequency-bandwidth dependence
similar to that of auditory nerve fibres," with **greater coding efficiency
than Fourier/wavelet bases** (Smith & Lewicki 2006, "Efficient auditory
coding," *Nature* 439: 978–982,
https://hearingbrain.org/docs/smith_lewicki_nature_2006.pdf). This is the
auditory analogue of Olshausen & Field's sparse-coding-recovers-V1 result
(1996, *Nature* 381: 607–609, https://www.nature.com/articles/381607a0), both
instances of Barlow's efficient-coding / redundancy-reduction hypothesis
(Barlow 1961, https://gwern.net/doc/psychology/neuroscience/1961-barlow.pdf).

**Why data-efficient:** the cochlea is an *evolved, pre-paid* prior — it
hands the learner a near-optimal, low-redundancy representation for free, so
no unlabeled audio is spent learning the front end. A small filterbank
captures the bulk of the variance (cross-species: 25 efficient filters encode
99% of cochleogram variance in bat echolocation — Chitradurga Achutha et al.
2021, *PLOS Comp Biol* 17(6): e1009052,
https://doi.org/10.1371/journal.pcbi.1009052).

---

### 2. Predictive-residual / autoregressive-residual term
**Fills: coarticulation; the "shape = residual-feedback recurrence"
keystone. This is the project's own +7% lever and maps 1:1 to the keystone.**

Predictive coding is the literal mechanization of the keystone: feedback
carries **predictions** and feedforward carries the **residual error** between
prediction and actual signal (Rao & Ballard 1999, "Predictive coding in the
visual cortex," *Nature Neuroscience* 2(1): 79–87,
https://www.nature.com/articles/nn0199_79). The free-energy principle frames
all of perception as minimizing prediction error against a generative-model
prior, the prior constraining (and so reducing) the inference burden (Friston
2010, "The free-energy principle: a unified brain theory?" *Nat. Rev.
Neurosci.* 11(2): 127–138, https://www.nature.com/articles/nrn2787).

**Why data-efficient as an analytic term (the crucial distinction):** when
the residual is *learned* (CPC/APC), it is label-efficient but
unlabeled-hungry — CPC gets 64.6% frame-level phone accuracy vs 39.7% for
MFCCs and 74.6% supervised (van den Oord et al. 2018, "Representation Learning
with Contrastive Predictive Coding," https://arxiv.org/abs/1807.03748,
numbers verified against the full-text table), and CPC v2 needs "2–5× less
labels" and works from "as few as 13 labels per class" (Hénaff et al. 2020,
"Data-Efficient Image Recognition with CPC," ICML 2020,
https://arxiv.org/abs/1905.09272) — *but it still pays the unlabeled-data
cost*. APC is explicitly "a generalization of linear predictive coding (LPC)"
and "benefits from large quantities of unlabeled data" (Chung et al. 2019,
https://arxiv.org/abs/1904.03240) — i.e., SSL-shaped, matching this project's
own measurement. The lesson: **encode the residual analytically (the LPC/AR
residual `b_t − b̂(b_{t−1})`) and you get the predictive-coding benefit for
free; learn it and you pay the SSL data tax.** This is precisely why the +7%
came from zero data.

---

### 3. Source–filter / formant decomposition
**Fills: source_filter_theory, formants, lack_of_invariance.**

The acoustic signal decomposes into an **independent source** (glottal buzz)
**filtered** by vocal-tract resonances (formants) — a physics-exact,
low-dimensional encoding of the phoneme (Fant 1960, *Acoustic Theory of
Speech Production*; cf.
https://www.fon.hum.uva.nl/praat/manual/Source-filter_synthesis.html). The
first 2–3 formants are determined by tract geometry and largely *characterize*
the vowel/phoneme, which is why explicitly tracked formants **improve phone
recognition on TIMIT** over the baseline (Wilkinson 2002, "Improved phone
recognition on TIMIT using formant frequency information," ICSLP 2002,
https://www.isca-archive.org/icslp_2002/wilkinson02_icslp.pdf) and why
formant-based vowel categorization helps **cross-lingual** phone recognition
(JASA 157(3): 2248, 2025, https://pubs.aip.org/asa/jasa/article/157/3/2248).

**Why data-efficient:** source–filter separation is the single biggest
*known* nuisance-variable factorization in speech — it analytically strips
pitch/speaker (source) from phonetic identity (filter), directly attacking
`lack_of_invariance` without spending data to learn the invariance. (Note:
this project's iteration logs already include a Klatt/LF forward model and
LPC-formant work — iterations 25, 40 — so the substrate is partway here.)

---

### 4. Articulatory inversion / articulatory-feature prior
**Fills: place/manner_of_articulation, coarticulation, lack_of_invariance.**

Recovering the speaker's articulatory gestures gives a representation that is
robust and **complementary to MFCCs**, especially under noise (Kirchhoff et
al. 2002, "Combining acoustic and articulatory feature information for robust
speech recognition," *Speech Communication* 37(3–4): 303–319,
https://www.sciencedirect.com/science/article/abs/pii/S0167639301000206;
Richardson, Bilmes & Diorio 2003, "Hidden-articulator Markov models," *Speech
Communication* 41(2–3): 511–529). Modern results quantify the low-resource
payoff: articulatory attributes give **−11 pp phoneme error rate** on
supervised languages and **−2.63 pp PER zero-shot across 84 languages**
(Glocker et al. 2023, "Allophant," Interspeech 2023,
https://arxiv.org/abs/2306.04306), and injecting predicted articulatory
features improves ASR "particularly under low-resource conditions" (Attia,
Liu & Espy-Wilson 2025, "Articulation-Informed ASR," arXiv:2510.08585).

This is the **analysis-by-synthesis / motor-theory** tradition: the objects of
speech perception are the speaker's *intended articulatory gestures*, detected
by inverting a production model (Liberman & Mattingly 1985, "The motor theory
of speech perception revised," *Cognition* 21(1): 1–36; Halle & Stevens 1962
analysis-by-synthesis). **Why data-efficient:** articulatory features are
near-speaker-invariant and the production manifold is low-dimensional, so the
prior factors out speaker and coarticulatory variation that a data-only model
must otherwise see many examples to average out. (Ranked below source–filter
because inversion is harder/less exact than the source–filter factorization
it depends on — and the project already has analysis-by-synthesis nodes,
iterations 16, 35.)

---

### 5. Sparse / efficient coding as a representational regularizer
**Fills: distributional_learning (gives it a structured target).**

Sparse coding recovers the same localized/oriented/bandpass structure the
brain uses, with "a higher degree of statistical independence among its
outputs" (Olshausen & Field 1996, above). **Why data-efficient (but ranked
last):** sparsity is a *generic* prior — it buys efficiency but does not, by
itself, encode speech-specific physics, so it overlaps with and is dominated
by priors 1–4. Best used as a regularizer on top of them, not as the primary
data-saver.

---

### Ranked summary

| # | Prior | Agent gap filled | Data-efficiency mechanism | Free? |
|---|---|---|---|---|
| 1 | Efficient-coding cochlear filterbank | (input substrate) | Evolved, pre-paid optimal low-redundancy code | Yes (analytic) |
| 2 | Predictive/AR residual term | coarticulation; residual-recurrence keystone | Encodes prediction-error structure analytically (vs SSL learning it) | Yes (analytic) |
| 3 | Source–filter / formant decomposition | source_filter_theory, formants, invariance | Factors source(speaker/pitch) from filter(phoneme) | Yes (analytic) |
| 4 | Articulatory inversion / artic. features | place/manner, coarticulation, invariance | Low-dim, speaker-invariant production manifold | Partly (needs inversion) |
| 5 | Sparse / efficient coding regularizer | distributional_learning | Generic independence/sparsity | Yes but generic |

The strongest single bet for "+ data bought back per unit effort" is the pair
**(1) cochlear front end + (2) analytic predictive residual** — both free,
both already validated by this project's own measurements, both upstream of
everything else.

---

## The existence proof: infants are lossy-but-right

Infants are the proof that strong priors make phonetic acquisition radically
data-efficient — they learn from *minutes*, not 60,000 hours:

- **8-month-olds segment words from a continuous stream after ~2 minutes** of
  passive listening, using transitional-probability statistics alone (Saffran,
  Aslin & Newport 1996, "Statistical Learning by 8-Month-Old Infants,"
  *Science* 274: 1926–1928,
  https://linguistics.berkeley.edu/~kjohnson/ling290e/saffran_et_al_1996.pdf).
- **Categorical perception of /ba/–/pa/ is present at 1 month** — a phoneme-
  relevant perceptual discontinuity *before* language experience, i.e., an
  innate prior (Eimas et al. 1971, *Science* 171: 303–306).
- Phonetic categories can be created/collapsed by the **distribution alone**:
  bimodal-exposure infants discriminate endpoints, unimodal do not (Maye,
  Werker & Gerken 2002, *Cognition* 82: B101–B111). This is
  `distributional_learning` *constrained by* innate categorical priors.
- **Perceptual narrowing** completes by 10–12 months — non-native contrasts
  lost, native sharpened — an experience-driven specialization of the prior
  (Werker & Tees 1984, *Infant Behavior and Development* 7: 49–63; Kuhl 2004,
  "Early language acquisition: cracking the speech code," *Nat. Rev. Neurosci.*
  5: 831–843, https://www.nature.com/articles/nrn1533).
- Learning happens from **~12 short live sessions**, and is **gated by social
  interaction** — audio-only recordings produce *no* learning (Kuhl, Tsao &
  Liu 2003, *PNAS* 100: 9096–9101). And the infant supplies its own data
  volume: **~3,500 protophones/day from the first month** (Oller et al. 2021,
  *Phil. Trans. R. Soc. B* 376: 20200255).

The pattern: **innate categorical/perceptual priors + a little distributional
learning + active production = phonetic competence from minutes-to-dozens-of-
sessions.** That is the "lossy-but-right = strong priors, not more data"
thesis instantiated in the only existence proof we have of a sample-efficient
phonetic learner.

---

## Low/zero-resource speech: where structure is forced to carry the load

When labels (or all transcripts) are scarce, structure is what remains:

- **Zero-resource:** the ZeroSpeech challenges discover subword/word units
  from raw audio with *no labels*, evaluated by ABX discrimination and term
  discovery — and "some [systems] even perform better than comparable
  supervised systems" (Versteegh et al. 2015, Interspeech,
  https://www.isca-archive.org/interspeech_2015/versteegh15_interspeech.html;
  Dunbar et al. 2019/2020). Bayesian-nonparametric structure recovers
  phone-like units that are "highly correlated with standard English phones"
  with zero labels (Lee & Glass 2012, ACL, https://aclanthology.org/P12-1005/;
  Kamper, Livescu & Goldwater 2017, ES-KMeans, https://arxiv.org/abs/1703.08135).
- **Low-resource ASR:** IARPA Babel built ASR from as little as **3 hours**
  (VLLP) transcribed, where multilingual shared-representation transfer
  "proved crucial" (Gales et al. 2014,
  https://www.isca-archive.org/sltu_2014/gales14_sltu.html).
- **SSL collapses the *label* requirement but not the *unlabeled* one:**
  wav2vec 2.0 hits **4.8/8.2 WER from just 10 minutes of labeled data** — but
  **pre-trained on 53k hours of unlabeled audio** (Baevski et al. 2020,
  NeurIPS, https://arxiv.org/abs/2006.11477, verified verbatim). HuBERT Large/
  X-Large are both pre-trained on **60,000 hours of Libri-Light** (Hsu et al.
  2021, https://ai.meta.com/blog/hubert-...). XLSR-53 pretrains on 56k hours
  across 53 languages for **−72% PER on CommonVoice** (Conneau et al. 2021,
  https://arxiv.org/abs/2006.13979).

This is the precise gap the structure-replaces-data thesis aims at: SSL has
already solved *label* efficiency, but it bought that with an enormous
*unlabeled* appetite. **The unbeaten floor is the unlabeled-data floor, and
the only thing known to undercut it is analytic structure.**

---

## Structured / generative-prior ML: the broader evidence

The structure-over-scale case generalizes well beyond speech:

- **Physics as prior = data efficiency, stated outright:** physics-informed
  neural networks are "a new class of **data-efficient** universal function
  approximators that naturally encode any underlying physical laws as prior
  information," and predict better "outside of the training set" and "with
  limited or noisy training data" (Raissi, Perdikaris & Karniadakis 2017/2019,
  https://arxiv.org/abs/1711.10561; *J. Comput. Phys.* 378: 686–707).
- **Program/structure priors learn from one example:** Bayesian Program
  Learning does one-shot Omniglot classification at human level, "from just a
  single example," beating deep nets, and passes Turing-like generation tests
  (Lake, Salakhutdinov & Tenenbaum 2015, "Human-level concept learning through
  probabilistic program induction," *Science* 350: 1332–1338,
  https://www.science.org/doi/10.1126/science.aab3050).
- **Neuro-symbolic structure = order-of-magnitude data savings:** the
  Neuro-Symbolic Concept Learner trained on **10% of CLEVR** reaches 98.9%,
  beating all baselines by 14% (Mao et al. 2019, ICLR,
  https://arxiv.org/abs/1904.12584).
- **Analysis-by-synthesis as fast recognition:** an inverse-graphics model
  "learns to invert a 3D face graphics program in a single fast feedforward
  pass," fitting human behavior and primate neural data better than
  discriminative DL (Yildirim et al. 2020, *Science Advances* 6: eaax5979,
  https://www.science.org/doi/10.1126/sciadv.aax5979).
- **The manifesto:** machines should "build causal models … rather than
  merely solving pattern recognition problems," "ground learning in intuitive
  theories of physics and psychology," and "harness compositionality" (Lake,
  Ullman, Tenenbaum & Gershman 2017, "Building machines that learn and think
  like people," *BBS* 40: e253, https://arxiv.org/abs/1604.00289).

The unifying form across all of these *and* speech: a generative model of how
the data is produced (graphics program / PDE / vocal tract / character
strokes) is inverted for recognition, and the generative prior is what makes
it data-efficient. This is the same shape as the agent's
**analysis-by-synthesis** and **shape-as-residual-recurrence** machinery.

---

## (c) Honest caveats — including the bitter lesson

### The bitter lesson (the strongest counterargument)

Sutton's "Bitter Lesson" is the central objection: "general methods that
leverage computation are ultimately the most effective, and by a large
margin," driven by the exponential fall in compute cost; "building in how we
think we think does not work in the long run," and doing so "only makes it
harder to see how the discovering process can be done" (Sutton 2019,
http://www.incompleteideas.net/IncIdeas/BitterLesson.html). Speech is a prime
exhibit: wav2vec 2.0 / HuBERT replaced decades of hand-built articulatory and
HMM machinery with scale, and scaling laws show test loss is a clean power law
in data/compute while "architectural details such as network width or depth
have minimal effects" (Kaplan et al. 2020, https://arxiv.org/abs/2001.08361);
Chinchilla shows more *data* (not parameters) is the compute-optimal lever
(Hoffmann et al. 2022, https://arxiv.org/abs/2203.15556). **In the abundant-
data regime, scale has repeatedly beaten structure.**

### When structure HURTS

A strong prior is a bet, and a wrong bet costs accuracy. The buyback shrinks
or reverses under **prior–data conflict** (Wiesenfarth & Calderazzo 2020,
above). Architectural inductive bias gives "the largest gains where the prior
fits the dominant dynamical structure" but is **weakest where the prior is
misaligned** (e.g., a wavelet/multiscale prior on chaotic advection-dominated
flows) — direct evidence a strong prior actively degrades performance when
misspecified. (Sankaran, Wang & Perdikaris, "Small Models, Strong Priors,"
arXiv:2605.25949 — *citation flagged: this is a recent preprint with a
post-dated arXiv ID that I could not independently re-verify; treat the
specific numbers as provisional, though the qualitative win/lose-by-alignment
finding is corroborated by the PINN and Bayesian-ESS literature above.*)

Brooks' rebuttal to Sutton is also a caveat on *us*: scaled methods still
smuggle in human structure (CNN translation-invariance is "designed by
humans"), so "the very essence of CNNs" already encodes a prior — the claim
that structure is unnecessary is "sleight of hand in moving the human
intellectual work to somewhere else" (Brooks 2019, "A Better Lesson,"
https://rodneybrooks.com/a-better-lesson/). The honest version: the question
is never structure-vs-scale absolutely, but *which* structure, and at *what
total cost*.

### The conditions under which structure wins

Synthesizing across the sources, structure beats scale when **all three** hold:

1. **Low-data regime** — sample complexity scales with VC dimension; the
   smaller the data, the more a constraint on the hypothesis space pays
   (Shalev-Shwartz & Ben-David 2014). The buyback is largest exactly where
   data is scarce.
2. **Known generative process / known physics** — when the domain's true
   structure is known and *true of the data*, encoding it is a correct bet
   (PINNs; source–filter theory; the cochlea). Speech production is one of the
   best-understood generative processes in all of perception.
3. **Out-of-distribution generalization** — structured/generative priors
   "make more accurate predictions outside of the training set" (PINNs;
   inverse graphics), where a data-only model has no examples to interpolate
   from.

**Speech satisfies all three for the analytic priors ranked above.** The
production process is known physics (source–filter), the cochlea is a known
optimal encoder, the bottleneck is the *unlabeled-data* floor (a data-scarcity
problem in disguise), and speaker/coarticulatory invariance is precisely the
OOD-generalization problem these priors factor out. This is the narrow,
defensible regime in which the structure-replaces-data thesis is not wishful
thinking but the consensus prediction of the literature — and it is exactly
the regime this project's own +7%-from-zero-data result already inhabits.

The bitter lesson is real and should keep us honest: do not hand-build what
the data can learn cheaply, and do not bet on a prior you cannot verify is
true of speech. But the cochlea, source–filter factorization, and the
predictive residual are not guesses about "how we think we think" — they are
*measured, evolved, and physical* facts about how speech is produced and
heard. Encoding facts is not the bitter lesson's target; encoding *guesses*
is.

---

## Sources

Inductive bias / sample complexity: Mitchell 1980; Wolpert 1996; Sterkenburg
& Grünwald 2021; Goldblum et al. 2024; Shalev-Shwartz & Ben-David 2014; Wilson
& Izmailov 2020; Wiesenfarth & Calderazzo 2020.
Efficient coding: Barlow 1961; Olshausen & Field 1996; Lewicki 2002; Smith &
Lewicki 2006; Chitradurga Achutha et al. 2021.
Source–filter / articulatory / motor theory: Fant 1960; Liberman & Mattingly
1985; Halle & Stevens 1962; Kirchhoff et al. 2002; Richardson et al. 2003;
Wilkinson 2002; Glocker et al. 2023; Attia et al. 2025; JASA 2025.
Predictive coding: Rao & Ballard 1999; Friston 2009/2010; van den Oord et al.
2018; Hénaff et al. 2020; Chung et al. 2019.
Infant acquisition: Saffran et al. 1996; Eimas et al. 1971; Werker & Tees
1984; Maye et al. 2002; Kuhl et al. 2003; Kuhl 2004; Oller et al. 2021.
Low/zero-resource: Versteegh et al. 2015; Dunbar et al. 2019/2020; Lee & Glass
2012; Kamper et al. 2017; Gales et al. 2014; Baevski et al. 2020; Hsu et al.
2021; Conneau et al. 2021.
Structured / generative ML: Raissi et al. 2017/2019; Lake et al. 2015; Mao et
al. 2019; Yildirim et al. 2020; Lake et al. 2017.
Bitter lesson / scale: Sutton 2019; Brooks 2019; Kaplan et al. 2020; Hoffmann
et al. 2022; Sankaran et al. (provisional).
