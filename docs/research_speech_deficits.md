# Speech/language DEFICITS: the lesion complement to the polyglot study

> Step-back study triggered by the user: "the one area we haven't mined is people
> with dyslexia and/or language 'blindness' or trouble understanding." The polyglot
> study (`docs/research_polyglot_machinery.md`) read the machinery working
> OPTIMALLY and gave us the representation-builder (iter-29). This is its
> complement: read the machinery BROKEN. **A deficit reveals a component's role by
> what fails when it is missing** — the lesion method. Each deficit isolates one
> NECESSARY stage of the working system, by its absence.
> **No build, no commit.** Synthesis only.

## Why this matters NOW — the iter-29 residual

iter-29 (`docs/agent_loop_iteration29_representation_builder.md`) confirmed the
representation-builder works and that the cohort warp WAS the baked-in HVPT failure
(held-out 1-NN 0.379→0.513). But it found a precise, honest hole: **the cross-voice
SURVIVAL selector does not bite.** Shuffling utterance→voice labels gives the *same*
grown patch bank (shuffle 0.517 ≈ real 0.513), and selected ≈ unselected ≈
fixed-bank. The reason is named in that doc: the build signal —
`grown_representation.masked_prediction_error`, the trivial 1-step predictor
`r̂_t = r_{t−1}` — rewards patches whose channel is **temporally SMOOTH /
predictable**, *regardless of which voice they help or what they discriminate*. It
is **voice-agnostic and contrast-agnostic**. So the cross-voice part of the
selector is near-inert.

The deficits below converge, independently, on exactly what that build signal is
missing. The single sharpest finding of this study: **the thing dyslexics cannot
do — resolve the rapid, fast-changing phonemic/transition cues — is the thing the
agent's smoothness build signal also cannot do, and by construction PENALISES.**
The deficit names the discriminating signal iter-29's selector needs.

---

## 1. The deficit → necessary-component map

Each deficit is read as a lesion: remove the component, observe what breaks,
conclude the component is necessary to the intact system. (Mechanism over label;
controversy flagged in §5.)

### 1a. DYSLEXIA — two dissociable lesions, two necessary components

Dyslexia is the richest case because it splits into two competing/complementary
sub-lesions, and **each names a different necessary component**.

**(i) The phonological-core deficit (Ramus, Snowling).** The behavioural core of
dyslexia is poor phonological processing: weak phonemic awareness — difficulty
segmenting and manipulating phonemes (rhyme, deletion, blending) — and the deficit
is now argued to be in *access to* phonological representations rather than in the
representations themselves
([Ramus, *Curr Opin Neurobiol* 2003](http://www.lscp.net/persons/ramus/docs/CONB03.pdf);
[neuroimaging review, PubMed 24568928](https://pubmed.ncbi.nlm.nih.gov/24568928/)).
- **Broken component:** a discrete **phonemic/categorical layer** with crisp,
  separable, manipulable category identities — and the *access path* to it.
- **Therefore NECESSARY:** the working system must carry **phoneme-level
  categorical contrast as an explicit, separable representation** (not just a
  blurred acoustic trajectory). Reading load-bearingly: phonology must be
  *carved into discrete contrastive units*, or downstream linkage fails.

**(ii) The rapid auditory / temporal-processing deficit (Tallal; Goswami).** A
subgroup of dyslexics cannot resolve **rapidly-changing acoustic events on the
tens-of-ms timescale** — the brief **formant transitions** between stop consonants
and vowels, and voice-onset times. Tallal (1980): rapid auditory processing within
a ~40 ms window is impaired; the ba–wa / ba–da distinctions, which hinge on
formant-transition *duration/rate*, are mis-perceived
([Tallal; rise-time & transition in ba–wa, PubMed 21159086](https://pubmed.ncbi.nlm.nih.gov/21159086/)).
Crucially for *this* substrate: **fast gamma-band activity (25–80 Hz) is what
tracks these rapidly-varying phonetic cues (formant transitions, VOT)**
([temporal processing review, AMU/HAL](https://amu.hal.science/hal-01481057/document)).
Goswami's **temporal-sampling framework** adds the slower axis: impaired
phase-locking to the **amplitude-envelope rise-time** at delta/theta (2 Hz / 4–8 Hz
= the syllable rate), the rhythmic timing that segments the stream
([Goswami, *TICS* 2011 (PDF)](https://personal.utdallas.edu/~otoole/HCS6330_F12/10_dyslexia.pdf);
[MEG phase-locking, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1053811911011505);
rise-time impaired cross-linguistically: English, French, Spanish, Hungarian,
Finnish, Chinese, Dutch).
- **Broken component:** the **temporal-contrast resolver** — the machinery that
  reads the *fast change* (transition = order-1-over-time of formant frequency) and
  the *envelope dynamics* (rise time, modulation rate), at the timescale where
  phoneme identity actually lives.
- **Therefore NECESSARY:** the working system must **represent and weight the rapid
  temporal CHANGE**, not just the static or smooth spectrum. The phonetically
  load-bearing cue is the *transition*, not the steady state.

**The dyslexia synthesis, stated for the agent.** The two sub-lesions are the
two halves of one missing thing: **a representation organised around phonemic /
temporal-transition CONTRAST.** Static blurry spectra (which a smooth predictor
loves) are exactly what is *least* informative about phoneme identity; the
information is in the fast transitions and the envelope rhythm — the very things
the deficit removes.

### 1b. AUDITORY PROCESSING DISORDER (APD) — figure-ground / speech-in-noise

APD = "trouble understanding speech despite a *normal audiogram*" — the ear and its
sensitivity are intact, but the central system cannot use the information: impaired
**temporal integration/discrimination/ordering** and, most characteristically,
**speech recognition in competing noise / degraded speech** (King–Kopetzky /
"auditory disability with normal hearing")
([ASHA CAPD portal](https://www.asha.org/practice-portal/clinical-topics/central-auditory-processing-disorder/);
[APD overview, Wikipedia](https://en.wikipedia.org/wiki/Auditory_processing_disorder)).
- **Broken component:** **central figure-ground / robust-to-degradation
  extraction** — pulling the speech stream out of competing acoustic structure
  using temporal regularities.
- **Therefore NECESSARY:** an invariance that holds **under noise and degradation**,
  i.e. a representation selected for *robustness across nuisance acoustic variation*
  — the same structural property as cross-voice invariance, generalised. (And note:
  APD localises the lesion *central to a perfect ear* — exactly the agent's
  situation, where the gammatone front-end is the *stronger* raw representation and
  the gap is downstream processing, per the Whisper mine.)

### 1c. SPECIFIC LANGUAGE IMPAIRMENT / DLD — the sequencing/grammar lesion

SLI (developmental language disorder): impaired **grammar / rule-governed
hierarchical sequencing** despite normal IQ and hearing. Ullman & Pierpont's
**procedural deficit hypothesis**: the lesion is in **procedural memory**
(frontal/basal-ganglia, esp. caudate), which underlies *implicit, rule-governed,
hierarchically-sequenced* learning; the largely-intact **declarative** system
partially compensates (children with SLI lean on stored exemplars instead of rules)
([Ullman & Pierpont, PDH (ResearchGate)](https://www.researchgate.net/publication/7866150_Specific_Language_Impairment_is_not_Specific_to_Language_the_Procedural_Deficit_Hypothesis);
[SRT-task meta-analysis, PMC 3989038](https://pmc.ncbi.nlm.nih.gov/articles/PMC3989038/);
[memory systems in SLI, PMC 3664921](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3664921/)).
- **Broken component:** the **sequential-structure / transition-probability
  learner** over time (statistical learning of the order, the rule, the
  hierarchy) — distinct from per-frame perception.
- **Therefore NECESSARY:** a **sequence-structure layer** above the units
  (transition probabilities, segmentation, hierarchical chunking). This is the
  *other* axis from perception — and the agent already has the strongest evidence
  here (the sentence-learning shuffle-collapse result; see have-vs-lacks).

### 1d. THE AGNOSIAS — the stage-isolation lesions (perception → phoneme → word → meaning)

These rare focal lesions dissociate the pipeline stage by stage, giving the
*cleanest* map of necessary stages because each isolates ONE break:

| Deficit | What is intact | What breaks | Necessary stage it isolates |
|---|---|---|---|
| **Auditory (non-verbal) agnosia** | hearing thresholds | recognising *any* environmental sound (dog bark, phone) | early **acoustic-object** formation, above raw audibility |
| **Pure word deafness / verbal auditory agnosia** | hearing, *non-speech* sound recognition, reading, speech production | decoding speech **phonemes into linguistic units** | the **speech-specific phonemic-decode** stage — speech is processed by dedicated machinery, separable from general audition ([auditory verbal agnosia, Wikipedia](https://en.wikipedia.org/wiki/Auditory_verbal_agnosia); [cortical speech disorders, PubMed 35964993](https://pubmed.ncbi.nlm.nih.gov/35964993/)) |
| **Word-meaning deafness** | phoneme discrimination, repetition, auditory lexical decision | **comprehending** the word's meaning | the **phoneme→lexicon→meaning** linkage, separable from phoneme perception |
| **Phonagnosia** | speech comprehension | recognising **who** is speaking (familiar-voice ID) | the **voice/speaker-identity** channel, separable from *what* is said |

**The decisive dissociation for the agent: pure word deafness vs phonagnosia.**
*What is said* (phoneme→word identity) and *who said it* (voice identity) are
**separable, independently-lesionable channels.** This is the lesion-method proof
of the project's central speech claim: speaker-invariant phonetic identity is a
real, separable component — recognisable when the voice channel is destroyed (pure
word deafness leaves *who* intact but kills *what*), and vice versa. **Invariance
to voice is not an approximation to chase; it is an architecturally distinct
channel the brain implements separately.**

---

## 2. Have-vs-lacks — the deficits' necessary components against the agent's pipeline

The agent's perception path (`stt_pipeline.py`, `invariant_units.py`,
`grown_representation.py`, `dynamics_features.py`):

```
gammatone (32 log bands, fixed)                      ── Layer 0, the ear
  → A1 STRF patch bank (fixed 25, or GROWN in iter-29)── Layer 1, conv
  → invariant_transform: VTLN→cohort canonical, CMVN, ── speaker/context norm
    predict-remove
  → categorical_perception leader-follower clustering  ── phoneme carve
  → lexicon (DTW signatures, refine_lexicon)           ── word
```

| Necessary component (from a deficit) | In the agent? | Where / the gap |
|---|---|---|
| **Phonemic / categorical CONTRAST as a separable layer** (1a-i, dyslexia phonological core; 1d word deafness) | **PARTIAL — present in RECOGNITION, absent from the BUILDER** | `categorical_perception.py` carves clusters, but **on the frozen front-end's output and downstream of the representation**. The representation-builder `grown_representation.py` has **NO notion of contrast** — grep confirms zero `contrast`/`phoneme`/`same-word` references; its selector reads only temporal smoothness. The contrast layer exists for the recogniser, never for *building* the representation. |
| **Rapid temporal-CHANGE / transition resolver** (1a-ii, Tallal/Goswami) | **PARTIAL — the OPERATOR exists; it is wired to the wrong place** | **The agent OWNS this exactly.** `dynamics_features.compose_formant_transitions` composes `F(late) − F(early)` where `F = ArgMax(region bands)` = **order-1-over-time of formant frequency = the place-of-articulation transition** (`order_n_concepts.py` provides order-N over any dimension; the doc literally names "order-1 over TIME = formant TRANSITION"). The envelope-rhythm axis (Goswami rise-time/modulation) is implicit in the cochleagram. **BUT** these are emitted as `exhibits` edges consumed only by the recogniser (`develop.py`, `cutover_test.py`) — grep confirms `grown_representation` never calls them. The build signal `masked_prediction_error` rewards the OPPOSITE: temporally SMOOTH channels. **The transition is what dyslexics lose and what the smoothness signal also discards.** |
| **Robust figure-ground / degradation-invariance** (1b, APD) | **NO** | No noise/degradation in the build loop; no robustness-across-nuisance selector. The cross-voice survival selector is the *structural seed* of this (survive across a nuisance), but it doesn't bite (iter-29). |
| **Sequence / transition-probability / hierarchy** (1c, SLI procedural) | **HAVE (strongest area)** | The sentence-learning result (held-out next-unit prediction beats frequency 1.52×, COLLAPSES under shuffle — structure is in the ORDER) is the agent's clearest win; `compositional_chunking`, `forward_segmentation`, `sonority_valley`, TP-trough segmentation all live here. The agent is *good* where SLI is *bad*. This component is present. |
| **Speech-specific decode, separable from general audition** (1d word deafness) | **PARTIAL** | The pipeline is speech-tuned (A1 patches, phoneme clustering) but there is no explicit "is this speech" gate separating a speech-decode path from general acoustic-object recognition. Minor for current goals. |
| **Voice channel separable from word channel** (1d phonagnosia ⊥ word deafness) | **PARTIAL / inverted** | The agent's design *wants* voice-invariant word identity, but the frozen front-end **entangles** them via the cohort VTLN warp (`canonical_log_centroid`), and iter-29 removed the warp but couldn't yet make the selector *use* cross-voice agreement. The separation the agnosias prove is real is exactly the separation the selector must enforce and currently does not. |

**Crux of the map.** Against the deficits, the agent has the **sequence** component
(SLI axis) and OWNS the **transition operator** (the dyslexia temporal axis) and a
**categorical layer** (the dyslexia phonological axis) — but the last two are wired
to *recognition*, and the **representation-BUILDER's selector reads neither**. It
reads temporal smoothness, which is contrast-blind and voice-blind. The deficits
say the discriminating information lives precisely in the **fast transitions** and
the **same-phoneme-across-voices contrast** — the two things the smoothness signal
ignores.

---

## 3. The proposed fix — does the dyslexia deficit identify iter-29's missing discrimination? YES.

**The diagnosis, stated cleanly.** iter-29's selector keeps a patch if it lowers
1-step prediction error on every voice. That rewards **broadly-coherent, smooth**
channels — and a smooth channel is smooth on shuffled voice labels too, so the
cross-voice partition carries no information → shuffle ≡ real. The build signal is
*voice-agnostic AND contrast-agnostic*. Dyslexia tells us why this is the wrong
signal: **phoneme identity is not in the smooth part of the signal; it is in the
fast transitions and the categorical contrasts** — exactly the cues the
phonological-core and temporal-processing lesions destroy. A selector that rewards
smoothness is, structurally, a selector that throws away phonetic information — it
is *building a dyslexic representation.*

**The fix: replace the smoothness build signal with a PHONEMIC/TEMPORAL-CONTRAST
build signal.** A patch survives iff it makes **the same word/phoneme look the same
across voices AND different words/phonemes look different**, where "look" is read
through the **transition** (order-1-over-time), not the static spectrum. This is a
*discrimination/contrast* selector, not a gradient fit — fully within thesis. The
two contrast terms map straight onto the two dyslexia sub-lesions:

1. **Temporal-transition contrast (the Tallal/Goswami axis).** Score a candidate
   patch not by `masked_prediction_error` (smoothness) but by how much **structure
   it carries in its order-1-over-time channel** — i.e. the patch's *transition
   response*, the thing that resolves the fast formant sweep. The agent already
   composes this: `dynamics_features.compose_formant_transitions`
   (`F_late − F_early`, `F = ArgMax`) and the general `order_n_concepts` order-1-
   over-time operator. **Lift that operator down into the build signal**: a patch
   earns its keep when its transition channel discriminates, not when its static
   channel is smooth. (Optionally add the Goswami envelope-rhythm axis: reward
   patches whose response tracks the 4–8 Hz syllabic modulation — order-1-over-time
   of the envelope.) This *inverts* the current signal's sign of preference and is
   the direct, mechanism-level fix.

2. **Cross-voice SAME-vs-DIFFERENT contrast (the phonological-core + agnosia axis).**
   This is the piece iter-29 *named* as missing ("a build signal that actually
   depends on the cross-voice agreement of a patch's response to the *same word*").
   Make survival depend on a **same-word-across-voices vs different-word margin**:
   a patch survives iff, over the training voices, it *increases* the margin
   (same-word-different-voice similarity − different-word similarity) — read through
   the transition channel. Now shuffling voice labels **must** destroy the signal
   (there is no real same-word-across-voice structure to find), so the selector can
   no longer survive its own shuffle. **This is the test that iter-29's selector
   failed; the contrast signal is built to pass it.** And it is the structural
   realisation of the phonagnosia⊥word-deafness dissociation: select for the
   *what*-channel that is invariant to the *who*-channel.

**Why this is within-thesis (no gradient-fit).** Both terms are *selectors over a
discrete authored inventory*, exactly the project's rule:
- Patches are still authored `(centre, sigma)` Gaussians rendered exactly
  (`grown_representation.patch_weights`); nothing fits coefficients.
- The selector reads the *sign* of a contrast-margin change and counts voices —
  the same shape as the current `patch_survives`, just with a contrast/transition
  objective instead of a smoothness one. No optimiser, no backprop.
- The contrast objective IS compression/discrimination, the project's selector
  ([[ozma_ideas_outside_the_seed]]: "the selector is everything; the right selector
  is compression"). **Caveat from memory:** raw discrimination *overfits*
  (spread=1.0 on noise) — so the selector must be **cross-voice-held + margin-based**
  (the held-out voice rejects cohort-memorising patches), not raw separation. That
  is precisely why the selector must be *cross-voice contrast*, the two terms
  together, not either alone.

**How the agent builds it from existing machinery (nothing exotic):**
- transition channel: `dynamics_features.compose_formant_transitions` +
  `order_n_concepts.nth_order_terms(samples, order=1)` over the time dimension —
  already authored, already graph-resident, already evaluated natively.
- same/different margin: the agent's own DTW/cosine same-word vs different-word
  comparison (the HVPT harness already computes this margin as a *metric* —
  promote it from metric to *selector*).
- cross-voice survival shell: keep `grown_representation.patch_survives`'s
  voice-counting structure; swap `representation_quality` (smoothness) for the
  contrast-margin-on-transition objective.
- robustness (APD) extension, later: run the same survival under added noise /
  degradation — a patch survives iff its contrast margin holds under nuisance.

**Other necessary stages the deficits expose that the agent lacks (ranked):**
1. **Contrast/transition build signal** (above) — the iter-29 fix. **Top.**
2. **Degradation/figure-ground robustness in the selector** (APD) — natural
   extension of #1 (survive contrast under noise), second.
3. **Speech-vs-nonspeech decode gate** (word deafness) — present implicitly,
   low priority for current digit/word goals.

---

## 4. The single most promising first step

**Swap the representation-builder's build signal from temporal smoothness to a
cross-voice TRANSITION-contrast margin, and re-run the iter-29 shuffle control.**

Concretely, the smallest honest experiment, reusing iter-29's exact harness
(`scripts/grown_representation_hvpt_accept.py`):
- Read each candidate patch's response **through the order-1-over-time transition
  channel** (`compose_formant_transitions` / `order_n` order-1-time), not the
  static patch sum.
- Define `representation_quality` as the **same-word-across-voices minus
  different-word margin** on that transition channel (promote the harness's
  existing margin metric to the selector).
- Keep `patch_survives`'s cross-voice voice-counting shell unchanged (sign of
  per-voice margin change, count voices).
- **The decisive read: does the real run now BEAT its own shuffle?** iter-29's
  shuffle ≡ real was the whole failure. If the transition-contrast selector makes
  shuffle < real (shuffling voice labels destroys the same-word-across-voice
  structure the margin depends on), the selector is finally doing discriminating
  cross-voice work — and it is doing it on the exact cue dyslexia proves is
  load-bearing.

This is the right first step because it (a) changes *one thing* — the build signal —
on the existing benchmark, (b) is the mechanism-level fix the dyslexia deficit
points to, (c) uses only machinery the agent already owns (the transition operator
+ the margin metric + the survival shell), with **no gradient-fit**, and (d) its
result is interpretable as the deficit prediction: a representation built to resolve
phonemic/temporal contrast generalises across voices where a smoothness-built one
(the "dyslexic" representation) cannot.

---

## 5. Honest caveats — where the deficit theories are contested, and where "necessary in humans" may not transfer

1. **The dyslexia temporal/magnocellular axis is genuinely contested.** Ramus
   found auditory deficits in only ~39% of dyslexics, weakly correlated with
   phonology/reading; the magnocellular deficit appears in roughly a third of cases
   and many with the deficit read normally
   ([Ramus *CONB* 2003](http://www.lscp.net/persons/ramus/docs/CONB03.pdf);
   [magnocellular critique, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0028393218301155)).
   Skottun has published 30+ critical commentaries. **What survives the controversy
   is the weaker, sufficient claim** we actually use: rapid formant transitions and
   envelope rise-time *are* phonetically load-bearing cues (uncontested — that is
   acoustics/phonetics, not the etiological theory), and a representation that
   discards them loses phonetic information. We are not asserting the temporal
   theory *causes* dyslexia; we are using the *cue inventory* the deficit
   highlights. The contrast-margin fix stands even if the magnocellular etiology
   falls.

2. **"Access vs representation" is unresolved for the phonological core.** Recent
   neuroimaging favours impaired *access* to intact phonemic representations rather
   than degraded representations
   ([PubMed 24568928](https://pubmed.ncbi.nlm.nih.gov/24568928/)). For the agent
   the distinction matters less (it must build *and* access the contrast layer), but
   we should not over-claim that the deficit proves the *representation* is the
   problem — it may be the link to it (which maps to the agent's phoneme→lexicon
   linkage, 1d word-meaning deafness).

3. **APD is a diagnostically contested category** (heterogeneous, overlaps with
   attention/language disorders, debated whether it is a distinct auditory entity).
   The *mechanistic* read we use — central figure-ground/robustness above a normal
   ear — is sound regardless; the diagnostic label's validity is not load-bearing
   for us.

4. **The procedural-deficit hypothesis for SLI is one of several** (others:
   processing-speed, generalised slowing, phonological-STM limits). We use it only
   to *name the component* (sequence/rule learning), which the agent independently
   demonstrated it has via the shuffle-collapse result — so the agent's evidence,
   not the contested hypothesis, carries the "have" verdict here.

5. **"Necessary in humans" need not transfer to the agent.** The lesion method
   shows a component is necessary *in the human architecture*; the agent is an
   entity, not a human replica (cf. [[ozma_wall_is_self_imposed]] — its senses are
   ours to extend). Two specific non-transfers: (a) The human voice⊥word
   dissociation (phonagnosia/word-deafness) reflects *cortical* separation; the
   agent could in principle entangle or separate them differently — we take it as a
   *design licence* (separation is achievable and worth enforcing), not a
   constraint. (b) The temporal-window limits (Tallal's 40 ms) are human
   biophysics; the agent's front-end can resolve finer or use multiple
   time-frequency trade-offs (two_ears), so it need not inherit the *limit*, only
   the *lesson* that the transition cue is where the information is.

6. **The fix's own bound (inherited from the polyglot study §3/§5).** A
   contrast/transition selector is only as good as the transition operator and the
   same/different labels available; with weak labels or a degenerate transition
   estimate (the blurry-cochlea formant problem) the margin is noisy. And the
   no-donkey line still holds: grow the *inventory* by discrete accretion under the
   contrast selector — do **not** slide into fitting STRF coefficients to maximise
   the margin (that is the open weight-constructor, out of thesis). The selector
   chooses among authored patches; it never fits one.

---

### One-line answer

The deficits name, by their absence, the discriminating signal iter-29's selector
lacks: **dyslexia's two lesions (phonological-core + rapid-transition) prove that
phoneme identity lives in the fast TEMPORAL-TRANSITION and the categorical CONTRAST
— exactly the cues the agent's smoothness build signal discards** — so the fix is to
replace the smoothness build signal with a **cross-voice transition-contrast
margin** (same-word-across-voices vs different-word, read through the agent's
already-owned order-1-over-time transition operator), which by construction destroys
under the voice-label shuffle that iter-29's selector survived; the agnosias
(word-deafness ⊥ phonagnosia) independently prove the *what*-channel is
architecturally separable from the *who*-channel, licensing the cross-voice
selector; SLI's procedural lesion names the sequence component the agent already
has; APD names the noise-robustness extension for later — all within thesis, all by
selection over an authored inventory, no gradient-fit.

---

## Sources

- Dyslexia phonological core (Ramus): [*Curr Opin Neurobiol* 2003 (PDF)](http://www.lscp.net/persons/ramus/docs/CONB03.pdf) · [neuroimaging review, PubMed 24568928](https://pubmed.ncbi.nlm.nih.gov/24568928/) · [phonological deficit & lexical processing (MEG), ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0010945223002587)
- Dyslexia temporal/rapid auditory (Tallal; rise-time/transition): [ba–wa rise-time & formant transition, PubMed 21159086](https://pubmed.ncbi.nlm.nih.gov/21159086/) · [revisiting temporal processing deficits (gamma tracks transitions), AMU/HAL](https://amu.hal.science/hal-01481057/document) · [MMN meta-analysis, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0149763420304590)
- Goswami temporal-sampling framework: [*TICS* 2011 (PDF)](https://personal.utdallas.edu/~otoole/HCS6330_F12/10_dyslexia.pdf) · [reduced phase-locking to slow AM (MEG), ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1053811911011505) · [over-arching oscillatory framework, PMC 4224062](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4224062/)
- Magnocellular theory + critique: [current status, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0028393218301155) · [magnocellular theory, PubMed 11305228](https://pubmed.ncbi.nlm.nih.gov/11305228/)
- APD / CAPD: [ASHA practice portal](https://www.asha.org/practice-portal/clinical-topics/central-auditory-processing-disorder/) · [APD overview, Wikipedia](https://en.wikipedia.org/wiki/Auditory_processing_disorder) · [European perspective, PMC 5702335](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5702335/)
- SLI / procedural deficit (Ullman & Pierpont): [PDH paper, ResearchGate](https://www.researchgate.net/publication/7866150_Specific_Language_Impairment_is_not_Specific_to_Language_the_Procedural_Deficit_Hypothesis) · [SRT meta-analysis, PMC 3989038](https://pmc.ncbi.nlm.nih.gov/articles/PMC3989038/) · [memory systems in SLI, PMC 3664921](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3664921/)
- Agnosias (stage isolation): [auditory verbal agnosia, Wikipedia](https://en.wikipedia.org/wiki/Auditory_verbal_agnosia) · [cortical disorders of speech processing, PubMed 35964993](https://pubmed.ncbi.nlm.nih.gov/35964993/)
- Perceptual narrowing (Werker & Tees): [oscillatory dynamics 6–12 mo, PMC 6601985](https://pmc.ncbi.nlm.nih.gov/articles/PMC6601985/) · [theta indexes narrowing, PMC 3795304](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3795304/)
</content>
</invoke>
