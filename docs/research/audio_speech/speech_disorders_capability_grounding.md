# The graph of speech-processing capabilities, read off the disorders

> Research spike. **Thesis to ground or challenge:** human speech processing is
> NOT a single system but a **graph of dissociable, interconnected
> capabilities** — and disorders, which selectively damage specific capabilities
> while sparing others, are the natural probe that reveals the modular structure
> (classic cognitive-neuropsychology *lesion logic*: a **double dissociation** —
> A lost / B spared in one patient, B lost / A spared in another — proves A and B
> are separable components, not two faces of one mechanism). **Verdict: GROUNDED,
> with one important qualification** — the boundaries are real and lesionable, but
> the components are richly *interconnected* (a dependency graph, not a pile of
> boxes), and several classic localizations (notably Broca's area) are contested.
> The dissociations licence the *components*; they do not licence naïve
> one-box-one-place anatomy.
>
> This complements (does not duplicate) `docs/research_speech_deficits.md`, which
> already mined dyslexia / APD / SLI / the agnosias for the iter-29
> representation-builder fix. This doc builds the **whole capability graph** —
> adding the aphasias, the planning/execution motor split, the dual-route reading
> model, prosody/aprosodia, amusia, CAS and stuttering — and maps **every** node
> to the project's speech findings. **No build, no commit beyond this doc.**
> Synthesis only.

---

## 0. The organizing backbone: the dual-stream model

Before the disorder table, one model organizes almost everything below. Hickok &
Poeppel's **dual-stream model** ([Nat Rev Neurosci 2007](https://www.nature.com/articles/nrn2113);
[review PMC 3468690](https://pmc.ncbi.nlm.nih.gov/articles/PMC3468690/)) splits
post-perceptual speech into two pathways after an early **bilateral**
spectrotemporal + phonological stage (dorsal STG → STS):

- **Ventral stream** ("what is said → meaning") — bilateral, temporal lobe; maps
  sound to lexical-semantic content. **Damage → comprehension deficits**
  (Wernicke's, transcortical sensory, word-meaning deafness).
- **Dorsal stream** ("sound → articulation") — strongly **left-dominant**;
  auditory-motor integration via area Spt (Sylvian parietal-temporal) → frontal
  articulatory network. **Damage → repetition / production deficits**
  (conduction aphasia, parts of Broca's).

This is itself the lesion-method's deepest single result: **perception-for-meaning
and perception-for-production are different streams**, dissociated by which
disorders cluster where. The capability graph in §3 is essentially this backbone,
unrolled to finer grain.

---

## 1. Disorder → capability dissociation table

Each row reads a disorder as a lesion: the **DAMAGED** capability is necessary
(what fails when it is gone); the **SPARED** capabilities prove it is a
*separable* component (they survive its loss). Controversy flagged in §5.

### 1a. The aphasias (post-perceptual language; mostly left perisylvian)

The aphasia taxonomy is itself a 2×2×... factorial of three dissociable axes —
**fluency** (production), **comprehension**, **repetition** — and the cells are
the classic types. That the three vary independently is the lesion-method proof
that they are three components.

| Disorder | DAMAGED (the lesioned capability) | SPARED (proves separability) | Localizes |
|---|---|---|---|
| **Broca's** (non-fluent / agrammatic) | speech **production** + **grammatical/syntactic assembly** — effortful, function-words omitted, content words kept (agrammatism) | **comprehension** relatively preserved (until syntax is load-bearing) | left inferior frontal (classically Broca's area) — but see §5: chronic Broca's needs damage *beyond* Broca's area ([PMC 4669036](https://pmc.ncbi.nlm.nih.gov/articles/PMC4669036/)) |
| **Wernicke's** (fluent / paraphasic) | **comprehension** + word→meaning mapping — fluent but semantically empty, paraphasic | **fluency / motor production** intact (speaks easily) | left posterior superior temporal — **ventral stream** ([taxonomy review](https://lonestarneurology.net/blog/brocas-vs-wernickes-aphasia/)) |
| **Conduction** | **repetition** — phonemic paraphasias, can't reproduce heard strings | **comprehension AND fluent production** both intact | classically arcuate fasciculus disconnect; modern: area **Spt** / left temporoparietal = **phonological short-term/working buffer** ([PMC 3090694](https://pmc.ncbi.nlm.nih.gov/articles/PMC3090694/)) |
| **Anomic** | **lexical retrieval** (word-finding) — the name won't come | fluency, comprehension, repetition all relatively spared | the lexical-access node in isolation ([PMC 7724433](https://pmc.ncbi.nlm.nih.gov/articles/PMC7724433/)) |
| **Transcortical motor** | spontaneous **production initiation** (non-fluent, Broca-like) | **repetition PRESERVED** + comprehension | the production-initiation path, *dissociated from the repetition loop* |
| **Transcortical sensory** | **comprehension** (Wernicke-like) | **repetition PRESERVED** + fluency | the comprehension path, *dissociated from the repetition loop* |
| **Global** | production **and** comprehension **and** repetition | (little spared) | large left perisylvian — the *conjunction* lesion (proves the others are normally separable: only a big lesion takes them all) |

**The decisive aphasia dissociation: repetition is its own axis.** The
transcorticals (repetition *spared* while production or comprehension fail) vs
conduction (repetition *lost* while both production and comprehension are intact)
is a clean double dissociation isolating a **repetition / echoic phonological
buffer** that is neither the comprehension path nor the production path — it is the
dorsal-stream auditory-motor loop, separable from both
([transcortical review](https://www.ncbi.nlm.nih.gov/books/NBK559315/)).

**The agrammatism dissociation:** Broca's omits **function words** (the, of, is)
and keeps **content words**; agrammatism vs paragrammatism is itself a cortical
double dissociation ([Matchin et al., *Neurobiol Lang* 2020](https://direct.mit.edu/nol/article/1/2/208/95868/)).
This directly touches the project's content-vs-function dissociation (§4).

### 1b. The motor split: PLANNING vs EXECUTION

| Disorder | DAMAGED | SPARED | Localizes |
|---|---|---|---|
| **Apraxia of speech (AOS)** | motor **PLANNING / programming** of articulation — knows the word, can't assemble the gesture sequence; inconsistent errors, groping, disrupted coarticulatory transitions | muscle strength & language (semantics/syntax) intact; can be present *without* dysarthria or aphasia ([ASHA AOS](https://www.asha.org/practice-portal/clinical-topics/acquired-apraxia-of-speech/)) | left frontal/insular motor-planning stage |
| **Dysarthria** | motor **EXECUTION** — weak/slow/imprecise/uncoordinated muscle control | the *plan* is intact; semantics/syntax intact | neuromuscular (central or peripheral); "output level... sparing semantics and syntax" ([ScienceDirect MSD](https://www.sciencedirect.com/topics/medicine-and-dentistry/motor-speech-disorders)) |

**The dissociation:** AOS = right plan, wrong gesture-assembly; dysarthria = right
plan, failing muscles. Both spare language, isolating **two distinct
post-linguistic motor stages**: *plan the articulatory trajectory* vs *execute the
muscle commands* ([Connected SLP](https://connectedspeechpathology.com/blog/dysarthria-vs-apraxia-key-differences-explained)).

### 1c. The perceptual / agnosic isolations (early, often bilateral)

| Disorder | DAMAGED | SPARED | Localizes |
|---|---|---|---|
| **Pure word deafness / auditory verbal agnosia** | **acoustic-phonetic decoding** of speech into phonemes | hearing thresholds, **reading, writing, speech production**, often non-speech sound recognition | the speech-specific phonemic decode stage; bilateral mid-superior-temporal / STS ([PubMed 26343343](https://pubmed.ncbi.nlm.nih.gov/26343343/)) — "Wernicke's area isolated from auditory input" |
| **Word-meaning deafness** | phoneme→lexicon→**meaning** linkage | phoneme discrimination, repetition, auditory lexical decision | the lexical-semantic mapping, *downstream of* phoneme perception |
| **Auditory (non-verbal) agnosia** | recognising any environmental **sound-object** | hearing thresholds; sometimes speech | early acoustic-object formation |
| **Phonagnosia** | recognising **WHO** is speaking (speaker/voice identity) | **WHAT** is said — comprehension fully intact | the speaker-identity channel; familiar-voice recognition → right inferior/lateral parietal; voice *discrimination* → either temporal lobe ([Van Lancker & Canter 1982](https://www.sciencedirect.com/science/article/pii/S0010945288800297); [Wikipedia](https://en.wikipedia.org/wiki/Phonagnosia)) |

**The decisive perceptual dissociation: phonagnosia ⊥ pure word deafness / receptive
aphasia.** A *double* dissociation — phonagnosics lose *who* and keep *what*;
receptive aphasics lose *what* and keep *who*
([dissociation review](https://en.wikipedia.org/wiki/Phonagnosia)). This is the
lesion-method proof of the project's **central** speech claim: **speaker identity
and phonetic content are architecturally separate channels** — "invariance to
voice is not an approximation to chase; it is a separately-implemented channel"
(echoed verbatim in `research_speech_deficits.md`). Strengthened here: voice
*discrimination* and voice *recognition* are themselves separable ([PubMed 3431677](https://pubmed.ncbi.nlm.nih.gov/3431677/)), so the speaker channel is itself sub-divided.

### 1d. The dual-route READING model — the cleanest sub-word/lexical/semantic dissociation

Reading is print→speech, so its acquired disorders dissociate the **same**
downstream nodes speech uses (sub-word assembly, lexical access, semantics) with
unusual surgical clarity. The dual-route model
([Coltheart; PMC 3491101](https://pmc.ncbi.nlm.nih.gov/articles/PMC3491101/)):

| Disorder | DAMAGED route | SPARED route | What it isolates |
|---|---|---|---|
| **Phonological dyslexia** | the **sub-lexical** grapheme→phoneme rule route — **can't read nonwords** ("blorp") | the lexical/whole-word route — reads known/irregular words fine | the **rule-based sub-word assembly** capability |
| **Surface dyslexia** | the **lexical** whole-word route — **can't read irregular words** ("yacht" → "yatched") | the sub-lexical route — regularises everything, reads nonwords fine | the **whole-word lexical lookup** capability |
| **Deep dyslexia** | **both** routes + makes **semantic** errors ("dog"→"cat") | (severe) | proves semantics is a *third* node — when phonology is gone, reading leaks through a **direct orthography→semantics** path that substitutes meaning-neighbours |

The **phonological ⊥ surface** double dissociation
([Castles & Coltheart; ScienceDirect 0028393295000385](https://www.sciencedirect.com/science/article/abs/pii/0028393295000385))
is the textbook proof of **two separable routes**: rule-assembly vs whole-form
lookup. Deep dyslexia's **semantic substitution errors** prove a separable
**semantics** node. The speech analogues: phonological dyslexia ≈ the inability to
*assemble* novel sub-word sequences (the project's chunk→word junction);
word-meaning deafness ≈ surface/access failure of the lexical→semantic link.

### 1e. Prosody / suprasegmentals — the OTHER axis (largely right-hemisphere)

| Disorder | DAMAGED | SPARED | Localizes |
|---|---|---|---|
| **Expressive (motor) aprosodia** | **producing** prosody — stress, intonation, melody; flat affectless speech | *recognising* prosody; segmental content | right frontal operculum (Broca's homologue) ([Ross Aprosodia Battery](https://pubs.asha.org/doi/abs/10.1044/nnsld18.2.66)) |
| **Receptive (sensory) aprosodia** | **comprehending** prosody — can't read the tune | *producing* prosody; segmental content | right temporoparietal (Wernicke's homologue) ([PMC 5471838](https://pmc.ncbi.nlm.nih.gov/articles/PMC5471838/)) |
| **Congenital amusia** | fine **pitch / pitch-contour** processing & pitch memory (~1.5% of people) | speech comprehension; *coarse* intonation largely spared | right fronto-temporal; **fine** intonation (question vs statement) IS impaired ([Peretz; PMC 3153840](https://pmc.ncbi.nlm.nih.gov/articles/PMC3153840/)) |

**Two dissociations here.** (i) Aprosodia mirrors the aphasia taxonomy on the
**right** — expressive ⊥ receptive prosody is a double dissociation
([PMC 5471838](https://pmc.ncbi.nlm.nih.gov/articles/PMC5471838/)), proving a
**suprasegmental** capability separate from segmental phonology AND lateralized
oppositely. (ii) Amusia dissociates **music pitch** from **speech**: amusics fail
music but mostly keep speech intonation — except where it needs *fine* pitch, so
the shared resource is *fine-grained pitch-contour extraction*, used coarsely by
speech and finely by music ([Peretz, *TICS* review](https://peretzlab.ca/wp-content/uploads/2020/12/peretz_i-_2016_tics.pdf)).
This isolates **segmental ⊥ suprasegmental** as a top-level split.

### 1f. Developmental disorders (the same nodes, failing in development)

| Disorder | DAMAGED | SPARED | Localizes |
|---|---|---|---|
| **Developmental dyslexia** | **phonological awareness** (segment/manipulate phonemes) ± rapid temporal-transition resolution | non-verbal IQ, hearing thresholds | the phonemic-contrast layer + the fast-transition resolver (mined in detail in `research_speech_deficits.md`) |
| **DLD / SLI** | **grammar / rule-governed hierarchical sequencing** (procedural-memory account, Ullman & Pierpont) | declarative memory partially compensates; IQ, hearing | the **sequence/transition-probability/rule** layer above the units |
| **Childhood Apraxia of Speech (CAS)** | speech **motor planning/programming** in development; inconsistent errors, disrupted coarticulatory transitions, off prosody; FOXP2-linked | (often co-occurs with, but is distinct from, phonological disorder) | the developmental analogue of AOS — motor *plan* ⊥ phonemic *knowledge* ([ASHA CAS](https://www.asha.org/practice-portal/clinical-topics/childhood-apraxia-of-speech/); [FOXP2, GeneReviews](https://www.ncbi.nlm.nih.gov/books/NBK368474/)) |
| **Stuttering** | **fluency / motor TIMING** — initiation of the next motor segment; cortico-basal-ganglia-thalamocortical loop timing-cue failure | language, semantics, segmental phonology; *external* timing cues (metronome, choral) abolish it | the **timing/sequencing-initiation** node, separate from planning and execution ([Frontiers PMC 6997432](https://pmc.ncbi.nlm.nih.gov/articles/PMC6997432/)) |

**CAS dissociation:** motor *planning* ⊥ phonemic *knowledge* (a child can have the
phonological representation and fail to program the gesture) — the developmental
echo of AOS ⊥ phonological deficit. **Stuttering dissociation:** *timing/initiation*
⊥ planning ⊥ execution — that an external metronome eliminates it proves the broken
piece is the **internal timing generator**, not the plan or the muscles.

---

## 2. The major dissociations, as top-level cuts

The disorders carve speech along these axes (each a proven double dissociation):

1. **Perception ⊥ Production** — Wernicke's/word-deafness vs Broca's/AOS; the
   dual-stream ventral⊥dorsal split.
2. **Content (what) ⊥ Speaker (who)** — pure word deafness ⊥ phonagnosia.
3. **Repetition ⊥ (comprehension & production)** — conduction vs transcorticals
   (the phonological buffer is its own node).
4. **Planning ⊥ Execution** (motor) — AOS ⊥ dysarthria.
5. **Timing/fluency ⊥ planning ⊥ execution** — stuttering vs AOS vs dysarthria.
6. **Sub-word rule-assembly ⊥ whole-word lexical lookup** — phonological ⊥ surface
   dyslexia.
7. **Lexical access ⊥ semantics** — anomia vs deep-dyslexia semantic errors.
8. **Grammar/syntax ⊥ lexical-semantics** — agrammatic Broca's vs Wernicke's.
9. **Content-word ⊥ function-word** — agrammatism keeps content, drops function.
10. **Segmental ⊥ suprasegmental (prosody)** — aphasia (left) vs aprosodia (right);
    amusia isolates fine pitch.
11. **Sequence/rule learning ⊥ per-frame perception** — SLI/DLD.

---

## 3. THE GRAPH OF SPEECH CAPABILITIES

Nodes = capabilities; edges = dependency / information flow (`A → B` ≈ "B consumes
A"); each node/edge annotated with the disorder that **dissociates** it (= proves
it is its own component). Top-down prediction edges run backward (dashed `⇠`).

```
                         ACOUSTIC INPUT (intact in every disorder below — that is the point)
                                   │
                                   ▼
              [N1] ACOUSTIC-OBJECT FORMATION  ── auditory (non-verbal) agnosia
                                   │
            ┌──────────────────────┼───────────────────────────┐
            ▼                       ▼                            ▼
 [N2] ACOUSTIC-PHONETIC     [N3] SPEAKER NORMALIZATION   [N12] PITCH/CONTOUR
      DECODING  ── pure          / SPEAKER-IDENTITY            EXTRACTION ── amusia
      word deafness             ── phonagnosia (the WHO          │  (fine pitch)
            │                      channel, ⊥ N2)                ▼
            ▼                       │ (feeds, doesn't gate N2)  [N13] PROSODIC /
 [N4] PHONEMIC / CATEGORICAL ◄──────┘                           STRESS EXTRACTION
      CONTRAST LAYER  ── dyslexia (phonological core),         (suprasegmental)
      pure word deafness                                    ── receptive aprosodia
            │                                                    │
            ▼                                                    │
 [N5] WORD SEGMENTATION  ── (project: TP-trough / sonority)      │
      (transitional-probability / rhythm)                       │
            │   ▲                                                │
            ▼   │ (N11 ⇠ top-down)                               │
 [N6] SUB-WORD / PHONOLOGICAL ASSEMBLY  ── phonological dyslexia │
      (rule-based grapheme/phone→sequence)                       │
            │                                                    │
            ▼                                                    │
 [N7] LEXICAL ACCESS  ── anomic aphasia, surface dyslexia        │
      (whole-form lookup)        │                               │
            │                    └──► [N8] SEMANTIC MAPPING ── word-meaning
            ▼                              deafness, deep dyslexia (semantic errors)
 [N9] SYNTACTIC / GRAMMATICAL ASSEMBLY ── agrammatic Broca's     │
      (+ content⊥function split) ── agrammatism                  │
            │                                                    │
   ┌────────┴─────────────────────────────────────────┐         │
   ▼ (comprehension done)                              ▼ (to produce)
 [N11] PREDICTION / TOP-DOWN CONTEXT          [N10] REPETITION / ECHOIC
       (lexical & motor predictive coding)          PHONOLOGICAL BUFFER
   ⇠ feeds back onto N2/N4/N5/N6              ── conduction aphasia (⊥ N7,N9)
                                                     │
                                                     ▼
                                      [N14] MOTOR PLANNING (articulatory
                                            gesture assembly) ── apraxia of speech / CAS
                                                     │
                                                     ▼
                                      [N15] MOTOR TIMING / FLUENCY
                                            (segment-initiation clock)
                                            ── stuttering (⊥ N14, ⊥ N16)
                                                     │
                                                     ▼
                                      [N16] MOTOR EXECUTION
                                            (muscle commands) ── dysarthria (⊥ N14)
                                                     │
                                                     ▼
                                                 SPEECH OUTPUT
```

**Stream membership (dual-stream backbone).** N1–N5, N12–N13 = early/bilateral
front end. **Ventral stream:** N7→N8→N9 (comprehension). **Dorsal stream:**
N6→N10→N14→N15→N16 (sound→articulation). N11 (prediction) wraps both streams as
feedback (predictive coding from lexical-conceptual AND motor systems —
[PMC 3468690](https://pmc.ncbi.nlm.nih.gov/articles/PMC3468690/)).

**Edge annotations (which disorder dissociates each edge):**
- N2→N4 dissociated by pure word deafness (decode lost, downstream lexicon/reading
  intact via other input).
- N3⊥N2 (the *who* channel does not gate the *what* channel) dissociated by
  phonagnosia ⊥ word deafness — the project's keystone.
- N4→N7 (phoneme→lexicon) vs N7→N8 (lexicon→meaning) dissociated by word-meaning
  deafness (former intact, latter lost).
- N6 ⊥ N7 (sub-word assembly vs whole-word lookup) dissociated by phonological ⊥
  surface dyslexia.
- N7 ⊥ N8 dissociated by anomia (access lost, semantics intact) vs deep-dyslexia
  semantic errors (semantics leaks when phonology gone).
- N9 ⊥ N7/N8 (syntax vs lexical-semantics) dissociated by agrammatic Broca's ⊥
  Wernicke's; content⊥function inside N9 by agrammatism.
- N10 ⊥ {N7,N9} (repetition buffer) dissociated by conduction vs transcorticals.
- N14 ⊥ N16 (plan vs execute) dissociated by AOS ⊥ dysarthria.
- N15 ⊥ {N14,N16} (timing) dissociated by stuttering (external metronome restores
  fluency → the timing generator is the broken piece).
- N13 ⊥ {N4,N7,N9} (suprasegmental vs segmental) dissociated by aprosodia (right
  hemisphere) ⊥ aphasia (left).
- N11 ⇠ (top-down prediction) — not a classic lesion-isolated node, but the
  dual-stream model posits two prediction sources (lexical + motor); the project
  builds this explicitly (§4).

---

## 4. Mapping to the PROJECT'S speech findings

Each project finding mapped to the capability node(s) it touches, with the
have/lacks verdict. (Findings drawn from `CONTINUOUS_SPEECH_FINDINGS.md`,
`docs/blind_effort_estimate.md`, `docs/prosody_syllable_frame.md`,
`docs/stage_a_continuous_entrainment.md`, the iter-14/41 docs, and
`research_speech_deficits.md`.)

| Project finding / build | Capability node(s) | Have / Lacks |
|---|---|---|
| **Word segmentation by transitional probability** (TP-trough chunker, forward_segmentation); **sonority-valley landmark** segmenter (iter-14) | **N5** (word segmentation) | HAVE the operator; **over-segments ~8× / chunks don't cluster by word** (continuous-speech crux) — N5→N6→N7 junction is where it breaks |
| **Theta-oscillator syllable entrainment** (`entrain_theta`, Stage-A) | **N5 / N13** (rhythm-based segmentation; the Goswami syllable clock) | HAVE — builds the *delta/theta rhythmic segmenter* dyslexia's temporal-sampling deficit names |
| **Sub-word / phone / syllable sequence recognition** (codebook units, categorical_perception, DTW lexicon) | **N4** (phonemic contrast) + **N6** (sub-word assembly) | PARTIAL — N4 present in recognition; the contrast layer is **absent from the representation-BUILDER** (the iter-29 hole; the dyslexia fix) |
| **STRESS as the rate-invariant identity**; prosody/syllable frame as a soft excluder | **N13** (prosodic/stress extraction) + **N3** (it is a speaker-rate-invariant) | HAVE a *segmental-count* prosody frame; **lacks** the suprasegmental-as-meaning channel (aprosodia's receptive node) and fine pitch-contour (amusia's N12) |
| **EFFORT / thermodynamic efficiency** (predictable words reduced) | **N11** (prediction / top-down context) | HAVE — this IS the predictive-coding feedback edge; reduction-when-predictable = the dual-stream lexical prediction source |
| **CONTENT vs FUNCTION word dissociation** | inside **N9** (grammar) — agrammatism's exact signature | HAVE the dissociation as data; **direct match to Broca's agrammatism** (function words dropped, content kept) — strongest cross-validation in this doc |
| **Lexical access** (DTW chunk→word lexicon grounding) | **N7** (lexical access) | PARTIAL — grounding gives purity 0.179, below usable (the N6→N7 junction failure) |
| **"Did the signal transmit" / information measure** (weighted-admissibility, soft-veto) | **N11** + the **N7/N8 decision** (collapse over frames) | HAVE — the information/under-determination measure is the project's signature; maps to the comprehension *decision* over the graph |
| **Cross-speaker invariant transform** (VTLN→CMVN→predict-remove; speaker-invariant centroids, iter-41) | **N2/N3** (the *what* ⊥ *who* separation) | PARTIAL — the design *wants* N3 separable from N2 (phonagnosia proves it is), but the front-end **entangles** them; iter-41 is the attempt to enforce the separation |
| **CortexLoop analysis-by-synthesis** (one op, swappable Hat) | **N11** (predictive coding, generative) + N14 (motor forward model, by analogy) | HAVE the *mechanism*; not yet wired as the top-down loop onto N2/N4 |

**Capabilities the project has NOT built (flagged by the disorder evidence):**

- **N3 as a first-class SPEAKER-IDENTITY READOUT** (phonagnosia). The project
  treats voice as a *nuisance to remove*; the lesion evidence says it is a
  *separable channel worth reading* (who-is-speaking). The project has no
  speaker-ID output, only speaker-*invariance*. **The dissociation says the who
  channel is real data, not just noise.**
- **N6 RULE-BASED SUB-WORD ASSEMBLY for novel forms** (phonological dyslexia). The
  chunker segments but does not *assemble* a novel word from a phone-rule route;
  the lexicon is whole-form (N7) only. The project is "surface-only" — it has the
  lexical route, lacks the sub-lexical generative route. **This is exactly the
  N5→N6→N7 over-segmentation crux** in CONTINUOUS_SPEECH_FINDINGS.
- **N10 REPETITION / ECHOIC PHONOLOGICAL BUFFER** (conduction aphasia). No
  short-term phonological buffer that holds a heard string for reproduction —
  separate from comprehension and lexicon. Conduction proves it is its own node.
- **N13 SUPRASEGMENTAL-AS-MEANING + N12 FINE PITCH CONTOUR** (aprosodia, amusia).
  The project has *segmental-count* prosody (syllable count as an excluder) but
  not intonation-as-meaning (question vs statement, affect) nor fine pitch-contour
  extraction. Receptive aprosodia + amusia name this whole right-hemisphere axis as
  missing.
- **N14–N16 the full MOTOR EXPORT chain** (AOS / stuttering / dysarthria). The
  project is perception-heavy; the production side (plan → time → execute) is
  largely a forward-model sketch. The three motor disorders say it is *three*
  separable stages, not one.

---

## 5. Honest caveats — where the evidence is contested

1. **Broca's area's real role is genuinely contested.** Classic localization
   (production = Broca's area) does not survive: chronic Broca's *aphasia* requires
   damage extending **beyond** Broca's area into Wernicke's and the underlying
   white matter ([Fridriksson et al., PMC 4669036](https://pmc.ncbi.nlm.nih.gov/articles/PMC4669036/)),
   and lesioning Broca's area alone often does not produce chronic Broca's aphasia.
   **What survives:** the *functional* dissociation (a production/grammar
   capability separable from comprehension) is robust; the *one-region-one-function*
   anatomy is not. Use the capability cut, not the pin on the map.
2. **Conduction aphasia's anatomy moved.** The textbook arcuate-fasciculus
   disconnection has largely been replaced by a cortical account (area Spt /
   temporoparietal phonological buffer; [Buchsbaum, PMC 3090694](https://pmc.ncbi.nlm.nih.gov/articles/PMC3090694/)).
   The *repetition-buffer capability* is solid; the white-matter story is partial.
3. **The aphasia taxonomy itself is a clinical idealization.** Pure types are rare;
   most patients are mixed; the classical category boundaries blur with lesion size
   and recovery. The *axes* (fluency / comprehension / repetition) dissociate
   cleanly; the *named cells* are convenient labels, not natural kinds.
4. **Dyslexia subtypes (dual-route) are challenged by connectionist single-route
   models** (Plaut/Seidenberg) that reproduce the double dissociation with one
   graded system + division of labour ([PMC 3491101](https://pmc.ncbi.nlm.nih.gov/articles/PMC3491101/)).
   So phonological⊥surface proves *two separable functions*, not necessarily *two
   anatomical routes*. The capability cut holds; the architecture is debated.
5. **Amusia's speech-sparing is partial.** Early claims of full speech-sparing are
   now qualified — amusics fail *fine* intonation ([PMC 3153840](https://pmc.ncbi.nlm.nih.gov/articles/PMC3153840/)).
   The dissociation is *graded by pitch resolution*, not absolute.
6. **CAS ⊥ phonological disorder is hard to draw clinically** (they co-occur and
   look alike; [ASHA CAS](https://www.asha.org/practice-portal/clinical-topics/childhood-apraxia-of-speech/)).
   The motor-plan vs phonemic-knowledge distinction is theoretically clean but
   diagnostically fuzzy.
7. **"Necessary in humans" need not transfer to the agent** (inherited from
   `research_speech_deficits.md` §5). The cortical *separations* are a **design
   licence** (these channels CAN be separated, and the dissociations say it is
   worth doing), not a constraint the agent must inherit. The agent may sub-divide
   or fuse differently.

---

## 6. The capability graph says: build these next (ranked)

Three-to-five concrete next capabilities/experiments the disorder evidence points
to, each tied to a node and a dissociation, each within the project's
selection-not-fitting thesis:

1. **N6 — a sub-lexical RULE-ASSEMBLY route (phonological dyslexia is the
   diagnosis of the continuous-speech crux).** CONTINUOUS_SPEECH_FINDINGS locates
   the loss at the chunk→word junction (over-segment ~8×, purity 0.179). The
   dual-route model says: the project has only the **whole-form lexical route**
   (N7) and lacks the **sub-lexical assembly route** (N6) — it is "surface-only."
   *Build:* group over-segmented chunks into a phone/syllable inventory, then
   **assemble** word candidates from sub-word sequences (a generative
   sub-lexical route), so the lexicon grounds at word scale. Test: does adding the
   assembly route lift word-clustering purity and word accuracy above unigram?
   **This is the single highest-leverage build — it is the project's named crux,
   and the disorder names the missing component precisely.**

2. **N3 — a first-class SPEAKER-IDENTITY readout (phonagnosia says the *who*
   channel is real data, not just noise).** The project removes the speaker;
   phonagnosia⊥word-deafness proves the speaker channel is a *separable
   capability*. *Build:* a speaker-ID readout from the SAME front-end that feeds
   the invariant transform — a who-classifier alongside the what-recogniser. Test
   (the dissociation as a control): the speaker-ID readout should succeed on
   held-out *utterances* of trained speakers while the word-recogniser is
   speaker-*invariant* — i.e. demonstrate the double dissociation *in the agent*
   (lesion N3 → who fails, what survives; lesion N2 → what fails, who survives).
   This both yields a new capability and is a clean test of the architecture's
   separation.

3. **N10 — a REPETITION / ECHOIC PHONOLOGICAL BUFFER (conduction aphasia isolates
   it).** Add a short-term phonological buffer that holds a heard sub-word string
   and can reproduce it, *separate from* lexical access and comprehension. Test:
   the agent should repeat a **nonword** it cannot comprehend (buffer intact,
   lexicon bypassed) — and a "lesion" of the buffer should kill repetition while
   sparing comprehension (the conduction signature). This is also the natural home
   for the N6 assembly route's working memory.

4. **N13/N12 — SUPRASEGMENTAL-as-MEANING + fine pitch-contour (aprosodia + amusia
   name the whole right-hemisphere axis as missing).** The project has
   segmental-count prosody (syllable count); it lacks **intonation as a
   meaning-bearing channel** (question vs statement, affect) and **fine
   pitch-contour extraction**. *Build:* a pitch-contour (F0) extractor + an
   intonation-class readout (rising→question) as a *separate* excluder/channel.
   Test (amusia's graded dissociation): coarse intonation should survive a coarse
   pitch front-end; fine question/statement discrimination should require the fine
   pitch resolver — reproducing amusia's pitch-resolution-graded sparing.

5. **N14→N15→N16 — the three-stage MOTOR EXPORT chain (AOS ⊥ stuttering ⊥
   dysarthria say it is three nodes).** The project is perception-heavy; the
   CortexLoop's analysis-by-synthesis already implies a motor forward model.
   *Build:* split production into **plan** (articulatory gesture sequence) → **time**
   (segment-initiation clock) → **execute** (parameter rendering), and show each is
   separately lesionable — AOS = scramble the plan, stuttering = perturb the clock
   (and restore with an external metronome, the stuttering signature), dysarthria =
   degrade the renderer. Lower priority than 1–3 (production is downstream of the
   perception crux), but it completes the graph and gives the analysis-by-synthesis
   loop its motor half.

---

## Sources

**Dual-stream backbone:** Hickok & Poeppel, [Nat Rev Neurosci 2007](https://www.nature.com/articles/nrn2113) · [feedback/predictive-coding review, PMC 3468690](https://pmc.ncbi.nlm.nih.gov/articles/PMC3468690/)

**Aphasias:** [Broca's vs Wernicke's taxonomy](https://lonestarneurology.net/blog/brocas-vs-wernickes-aphasia/) · agrammatism⊥paragrammatism double dissociation, [Matchin et al. *Neurobiol Lang* 2020](https://direct.mit.edu/nol/article/1/2/208/95868/) · chronic Broca's needs damage beyond Broca's area, [Fridriksson, PMC 4669036](https://pmc.ncbi.nlm.nih.gov/articles/PMC4669036/) · conduction / phonological buffer / area Spt, [Buchsbaum, PMC 3090694](https://pmc.ncbi.nlm.nih.gov/articles/PMC3090694/) · transcortical / anomic / global, [StatPearls NBK559315](https://www.ncbi.nlm.nih.gov/books/NBK559315/), [anomic profile PMC 7724433](https://pmc.ncbi.nlm.nih.gov/articles/PMC7724433/)

**Motor split (planning vs execution):** [ASHA Acquired AOS](https://www.asha.org/practice-portal/clinical-topics/acquired-apraxia-of-speech/) · [motor speech disorders overview, ScienceDirect](https://www.sciencedirect.com/topics/medicine-and-dentistry/motor-speech-disorders) · [dysarthria vs apraxia](https://connectedspeechpathology.com/blog/dysarthria-vs-apraxia-key-differences-explained)

**Perceptual/agnosic isolations:** pure word deafness bilateral STS, [PubMed 26343343](https://pubmed.ncbi.nlm.nih.gov/26343343/) · [auditory verbal agnosia, Wikipedia](https://en.wikipedia.org/wiki/Auditory_verbal_agnosia) · phonagnosia, [Van Lancker & Canter / ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0010945288800297), [Wikipedia](https://en.wikipedia.org/wiki/Phonagnosia), voice discrimination⊥recognition [PubMed 3431677](https://pubmed.ncbi.nlm.nih.gov/3431677/)

**Dual-route reading / dyslexias:** [dual-route subtypes, PMC 3491101](https://pmc.ncbi.nlm.nih.gov/articles/PMC3491101/) · surface⊥phonological dissociation, [ScienceDirect 0028393295000385](https://www.sciencedirect.com/science/article/abs/pii/0028393295000385) · [deep dyslexia, Wikipedia](https://en.wikipedia.org/wiki/Deep_dyslexia)

**Prosody / aprosodia / amusia:** Ross aprosodia battery, [ASHA NNSLD](https://pubs.asha.org/doi/abs/10.1044/nnsld18.2.66) · expressive⊥receptive prosody double dissociation, [PMC 5471838](https://pmc.ncbi.nlm.nih.gov/articles/PMC5471838/) · amusia speech-intonation, [Peretz PMC 3153840](https://pmc.ncbi.nlm.nih.gov/articles/PMC3153840/), [Peretz *TICS* review](https://peretzlab.ca/wp-content/uploads/2020/12/peretz_i-_2016_tics.pdf)

**Developmental (CAS, stuttering):** [ASHA CAS](https://www.asha.org/practice-portal/clinical-topics/childhood-apraxia-of-speech/) · [FOXP2, GeneReviews NBK368474](https://www.ncbi.nlm.nih.gov/books/NBK368474/) · stuttering / basal-ganglia timing, [Frontiers PMC 6997432](https://pmc.ncbi.nlm.nih.gov/articles/PMC6997432/)

**Prior project doc this complements:** `docs/research_speech_deficits.md` (dyslexia / APD / SLI / agnosias → the iter-29 contrast-builder fix).
