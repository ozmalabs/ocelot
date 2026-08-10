# Research spike: how humans and machines learn to READ and WRITE cursive

*Grounding a plan for a TRAINING-FREE (donkey=0) cursive reader.*
*Compiled 2026-07-06. Web research + synthesis, no code.*

## Why this spike

Runs 61-67 established the shape of the problem: we can WRITE connected
cursive (learned joins match real cursive 140/140, DTW 0.244 vs 0.566),
reading-with-lexicon-context is pure gain on hand-PRINT (67% char + lexicon
= 78% word), but reading CURSIVE floors at ~18% char / 0.7% word and does
NOT clear it via writer-adaptive allographs, Fisher weighting, or trie-beam
lexicon search. The binding constraint we measured: the per-letter geometric
signal is too weak (invariant same-letter distance 0.205 vs different-letter
0.235 — a razor margin), the separating signal lives in pose/placement that
invariance discards and whole-word matching re-entangles, and pose is
writer-dependent (doesn't generalize cross-writer).

The spike asks two crux questions of the human and machine literature:
(1) do humans have a STRONG per-letter cursive recognizer, or a WEAK one
rescued by top-down/context/motor? (2) is human cursive reading
training-free-compatible, or does it need the lifetime-learned strong
posterior that machines train for? Then: what is the donkey=0 path.

---

## A. How humans learn to WRITE cursive (pedagogy + motor learning)

**The staged curricula all share one order: strokes/drills → letters →
joins/connectors → words.** This is the same curriculum our writer learned.

- **Spencerian (c. 1840s-1860s, Platt Rogers Spencer)** — the ornate
  ancestor. Taught a small set of *principles* (the seven basic strokes:
  straight line, right/left curves, loops, ovals) drilled to muscle memory
  *before* any letter, then letters as combinations of principles, then
  words. Heavy repetition of the primitive strokes first.

- **Palmer Method (c. 1888, Austin Palmer)** — a simplification of
  Spencerian that "had quickly become the most popular handwriting system in
  the US." Its signature idea is *muscle motion*: "the more proximal muscles
  of the arm were used for movement, rather than allowing the fingers to move
  in writing" (Wikipedia, *Palmer Method*). Rhythmic, drilled ovals and
  push-pulls precede letters; **fluency/rhythm is trained as a motor program,
  not a shape copied.**

- **Zaner-Bloser (dominant US method today; ~90% of US schoolchildren use
  Zaner-Bloser or D'Nealian, per *Cursive Workshop*)** — "first teaches block
  letters and then cursive in order to enable written expression as quickly
  as possible." Each lesson is three steps: **model → practice → evaluate.**
  Print first, cursive second; cursive letters slant, exit strokes run to the
  midline (the *connectors* are explicit taught units).

- **D'Nealian (Donald Thurber)** — the clearest "join is a delta on the
  letter" pedagogy: students learn a print form, then add "monkey tails"
  (short exit strokes) to the print, then in step three the tails are
  **joined together to form cursive.** "Just 13 letters change shape between
  print and cursive, and the slant does not change at all." Cursive is
  literally print + a connector transform.

**Motor-learning findings (relevant to AbS):**

- "During the training process, handwriting evolves from a slow feedback
  process involving active attention and eye-hand coordination to a **fast
  automatic and ballistic process**. Writers exert an increased force in
  order to maintain a preferred **rhythm of movement**" (Zaner-Bloser
  written-language production standards; Ohio ELA handwriting appendix).
- "Establishing correct and consistent motor sequences from the start is
  optimal for developing **automaticity**." Fluency keeps developing through
  grade 9 (multi-year timescale).
- Development note: "even very young children can recognize the loops and
  connectors of cursive writing before they can write script themselves"
  (Big Think summary of handwriting-development research) — recognition of
  the *connector vocabulary* precedes production competence.

**Takeaway for us.** The human writing curriculum is exactly the
primitive-strokes → letters → joins → words ladder we already implemented,
and the join is taught as a *transform on a letter* (D'Nealian's tail), which
matches our RUN-63/65 result that generation-with-joins is a delta on the
letter shape. Handwriting becomes *ballistic/automatic* — a stored motor
program with a rhythm, i.e. a low-dimensional generator, consistent with the
sigma-lognormal view in section C.

---

## B. How humans READ cursive (cognitive psychology — the crux)

### B1. The word-superiority effect: letters ARE better recognised in words

**Reicher (1969) and Wheeler (1970):** a subject asked to identify a letter
"does better when the letter is embedded within a word than when it is
embedded in a nonsense string of letters or presented alone." Accuracy for
the critical letter was ~**70-80% in words vs markedly lower in single
letters or nonwords** (Wikipedia/Springer summaries). The two-alternative
forced-choice design (both alternatives complete a word) rules out guessing
from word redundancy — so the word context genuinely improves *letter-level*
perception. There is also a **pseudoword superiority effect**: pronounceable
non-words (that share sub-sequences with real words) also beat illegal
nonwords, in both children and adults (Ripamonti et al. 2018; Grainger et al.
ERP work in 7- and 11-year-olds, PMC3496077).

### B2. Interactive Activation: top-down word→letter feedback fills weak evidence

**McClelland & Rumelhart (1981), *An interactive activation model of context
effects in letter perception*.** Bottom-up: features → letters → words.
Crucially, **words send excitatory feedback DOWN to their constituent letter
units**, "increasing letter perceptibility." This is the canonical mechanism
for the WSE: when bottom-up letter evidence is weak or ambiguous, lexical
units that are partially activated feed activation back to the letters they
contain, and the *word* constrains which letter you perceive. McClelland's
own retrospective (2014, *Cognitive Science*, "Interactive Activation and
Mutual Constraint Satisfaction") frames perception as mutual constraint
satisfaction across levels — bottom-up evidence and top-down knowledge
*jointly* settle on the reading.

This is the single most important finding for us: **the human system does not
require a strong per-letter posterior in isolation. It runs a weak per-letter
signal and a strong lexical prior in a feedback loop, and the loop is what
produces confident letter identity.** That is structurally what our
"lexicon collapse over per-char candidates" does — except our collapse is
one-directional (letters → word) and does not feed back to re-score letters.

### B3. Word-shape / bouma envelope: largely debunked for print

The typographers' "word shape / bouma envelope" model is **not** the accepted
account. Kevin Larson (Microsoft, *The Science of Word Recognition*): "Word
shape is no longer a viable model of word recognition… we recognize a word's
component letters, then use that visual information to recognize a word."
"Parallel letter recognition is the most widely accepted model." Bouma (1973)
himself does not support a word-shape model. So for *print*, envelope is not
the primary cue — parallel letter recognition + lexical constraint is.

Caveat for cursive specifically: this literature is about *printed* words.
Ascender/descender/envelope cues may carry more weight in degraded/cursive
reading than in clean print, but the evidence base I found does not establish
envelope as a strong standalone cue for cursive. Our own RUN-15/16 finding
(scrambled-letter envelopes matched; envelope weak) is consistent with the
psychology: envelope is a weak feature, not the engine.

### B4. Reading handwriting activates MOTOR areas (embodied reading)

A consistent fMRI result (Longcamp, Anton, Roth, Velay and colleagues, 2003
onward):
- "Visual presentation of single letters activates a premotor area involved
  in writing" (Longcamp et al. 2003, PubMed 12948705) — left ventral premotor
  cortex (BA6), the same region used to *write* the letter, activates when
  you merely *look* at it.
- The effect is **specific to handwritten forms and largely disappears for
  printed text** ("this sensorimotor relationship disappears when the
  letterforms are displayed as printed text").
- It is **hand-specific**: in left-handers the *right* premotor BA6 activates,
  mirror-symmetric to right-handers (Longcamp et al. 2005, PubMed 16154456) —
  i.e. the activation tracks the reader's own *motor* program for producing
  the form, not a purely visual template.
- Interpretation: "the cerebral representation of letters is presumably not
  strictly visual, but based on a multicomponent neural network built up
  while learning concomitantly to read and write, with one component being a
  sensorimotor one." A PNAS study (Nazir/Dehaene-adjacent, PMC3528608)
  reports "universal brain systems for recognizing word shapes AND
  handwriting gestures during reading."

**This directly supports our generation-is-reading / AbS finding.** Humans
appear to *co-represent* the seen letter and the motor act that produces it;
reading handwriting recruits the writing system. We can WRITE — so a
motor-simulation reading path is biologically the *native* one for
handwriting, not an exotic trick.

### B5. Reading is a LEARNED expertise (bears on training-free-compatible)

Dehaene, McCandliss, Cohen et al. on the **Visual Word Form Area (VWFA)**:
"Learning to read results in the formation of a specialized region… which
responds selectively to written words." "Education recycles the human brain
by repurposing some visual regions towards the shapes of letters." In experts
"the visual system… has internalized and exploits the distributional
statistics of letters"; length effects (serial, slow) vanish only *with
expertise* — children start with strong length effects that "gradually
disappear with learning." Reading fluency is a multi-year acquisition.

So the human per-letter/per-word visual posterior is **learned** — over years,
from enormous exposure. It is not innate and not training-free in the "never
adapted" sense. But it is learned *unsupervised / weakly-supervised* from the
child's own reading+writing, not from labelled corpora with backprop.

---

## C. How machines READ cursive (ML / HWR)

### C1. The segmentation-free revolution: Graves et al. (2009)

**Graves, Liwicki, Fernández, Bertolami, Bunke, Schmidhuber (2009), "A Novel
Connectionist System for Unconstrained Handwriting Recognition," IEEE TPAMI
31:855-868.** Bidirectional LSTM + a **Connectionist Temporal Classification
(CTC)** output layer. The key move: *avoid pre-segmentation entirely.*
"Traditional RNN objective functions require a presegmented input sequence…
which has limited the applicability of RNNs in domains such as cursive
handwriting recognition, where segmentation is difficult to determine. CTC…
transforms the network output sequences into a conditional probability
distribution over possible label sequences." This was the first RNN to win
handwriting competitions.

**Why this matters for us.** The field's foundational insight is precisely
the chicken-and-egg we hit: *you cannot segment before you recognise, and you
cannot recognise before you segment.* CTC dissolves it by scoring whole label
sequences and marginalising over all alignments — recognition-by-alignment,
not recognise-then-segment. Our `vit_step`/`vit_backtrace` span lattice
("segmentation-by-recognition") is the same idea in graph form; the spike
confirms this is the correct architecture, independent of the trained net.

### C2. How much accuracy is VISUAL vs LANGUAGE MODEL

The trained visual posterior is *strong* — but the LM still matters and the
split is measurable:

- **Liu, Wang et al. (2020/2016), "A Study on Effects of Implicit and Explicit
  Language Model Information for DBLSTM-CTC Based Handwriting Recognition"
  (arXiv 2008.01532):** on IAM, **WER improves 22.2% → 17.3%** when an
  explicit LM is added — a ~5-point (≈22% relative) reduction — and "even when
  training DBLSTM with one million lines… using an explicit language model was
  found to be beneficial." So even with a heavily-trained visual model, an
  explicit lexical/LM constraint is worth ~1/4 of the remaining word errors.
- Modern CNN-BiLSTM-CTC on IAM reaches **~3.6% CER / ~9.4% WER** (arXiv
  2307.00664) — but this is a *trained* visual model doing the heavy lifting.
- Neural LMs beat n-gram LMs in the decoder (Zamora-Martínez et al.,
  *Pattern Recognition* 2014); best combined IAM WER ~16.1%.

**Honest reading of this for donkey=0:** in the trained pipeline the *visual*
model carries most of the accuracy and the LM trims ~20-25% of the residual
word errors. Our situation is inverted: our visual (per-letter) posterior is
weak (~18%), so the LM/lexical constraint has to carry *far more* than the
~5 WER points it buys in a strong-visual system. The machine literature does
not show a regime where an ~18% visual posterior is rescued to usable word
accuracy by an LM alone — the trained systems never operate that starved.
This is a genuine warning: LM/context is a multiplier on a decent posterior,
not a substitute for one.

### C3. Generation / analysis-by-synthesis

- **Graves (2013), "Generating Sequences With Recurrent Neural Networks"
  (arXiv 1308.0850):** generate realistic cursive by "predicting one data
  point at a time," conditioned on a text sequence (handwriting *synthesis*).
  Establishes that a *predictive, incremental* generator captures cursive with
  long-range structure. Note: this is a generator; using it for recognition
  (invert the synthesis) is the AbS direction, which Graves did not close but
  which the Bayesian models below do.
- **Bayesian Action-Perception (BAP) model — Gilet, Diard, Bessière (2011),
  PLoS ONE, "Interaction of Production and Recognition of Cursive Letters":**
  THE most directly relevant paper found. One probabilistic model does *both*
  writing and reading via a shared representation ("perceptual and motor
  representations… encoded in the same space… as in the common-coding
  approach"). Recognition uses **internal motor simulation**: "perceiving a
  letter would entail a motor simulation of movements associated with the
  writing of that letter." Quantitative results:
  - **93.36% correct letter recognition for a KNOWN writer**
  - **49.68% for an UNKNOWN writer**
  - 79.5% writer identification.
  This is a striking external confirmation of our exact wall: **a motor/AbS
  recognizer scores ~93% within-writer and collapses to ~50% cross-writer**,
  because pose/style is writer-specific. The BAP model is essentially
  training-free in our sense (a hand-specified probabilistic program, inferred
  not backprop-trained) — and it *still* shows the cross-writer cliff. That is
  the single most calibrating number in this spike.
- **Lake, Salakhutdinov, Tenenbaum (2015), Science 350:1332, "Human-level
  concept learning through probabilistic program induction" (BPL / Omniglot):**
  characters modelled as **probabilistic motor programs** — strokes (parts),
  sub-strokes, relations — inferred one-/few-shot. Matches or beats humans on
  one-shot classification and generation. This is the canonical *training-free*
  (well, weak-prior + program-induction) generative recognizer, and it is
  built on exactly our primitives: strokes, relations, composition. BUT:
  Omniglot characters are *isolated and pre-segmented*; BPL does not solve
  connected-cursive segmentation or cross-writer word reading. It is the right
  representation, demonstrated only on the easy (segmented, per-character)
  regime.

### C4. Kinematic / motor models: Plamondon's sigma-lognormal

**Plamondon's Kinematic Theory (sigma-lognormal / delta-lognormal model):**
handwriting is "the space-time superimposition of a discrete number of
lognormal movement primitives (strokes), each aimed at a virtual target."
Generation "starts with an action plan made up of virtual targets linked by
circular arcs… each command producing a lognormal stroke," summed in velocity
space. "Lognormality provides… an integrative standpoint to track… handwriting
generation, recognition and learning" (Plamondon et al.; PMC3867641 "The
lognormal handwriter"). The implication for recognition: cursive is generated
by a **very low-dimensional motor system** (a handful of virtual targets +
lognormal timing), so the *true* latent description of a cursive trace is
low-dimensional — which is exactly why AbS (invert the generator) is
tractable in principle, and echoes our memory note that "impractical scale =
wrong shape; the generator is low-dimensional."

### C5. Few-shot / training-free HWR

- Recent few-shot work is almost all **generation** (One-DM diffusion mimicker,
  GANwriting, CONSTANT one-shot style transfer) — style-transfer producers,
  not training-free readers.
- "Few-shot Writer Adaptation via Multimodal In-Context Learning" (2026,
  arXiv 2603.29450) does *inference-time* writer adaptation "without parameter
  updates" — but on top of a large pretrained recognizer (not donkey=0).
- Genuinely training-free *word* readers for cursive are essentially absent
  from the literature; the closest are the generative Bayesian models (BAP,
  BPL), and both are demonstrated only per-character / within-writer.

---

## D. Synthesis — the two crux answers, the ranked path, the plan

### Crux 1 — Do humans have a STRONG per-letter cursive recognizer, or a WEAK one rescued by top-down/context/motor?

**WEAK per-unit signal, rescued by a top-down loop.** The evidence is
convergent:
- WSE/pseudoword-SE (Reicher 1969, Wheeler 1970, IAM 1981): letters in
  isolation are *worse* recognised than letters in words; the lexicon feeds
  back to make the letter perceptible. Human confident letter identity is a
  *product* of weak bottom-up + strong lexical prior, not a strong
  bottom-up posterior alone.
- "When characters are observed in isolation, they are often ambiguous and
  require context" — stated identically for humans and machines.
- The BAP model *quantifies* it in the cursive-motor regime: even a motor
  recognizer is 93% within-writer but ~50% cross-writer — the raw per-letter
  cross-writer signal is genuinely near-coin-flip, exactly our ~18-margin
  wall, and humans live with it by leaning on context and their own motor
  model.

So **our floor is EXPECTED, not a bug.** A ~18% invariant per-letter posterior
is low but not obviously off the human bottom-up scale for cross-writer
cursive; the human system never runs the letter channel open-loop. The lever
is not "make the per-letter recognizer strong in isolation" (humans don't) —
it is the **top-down feedback loop** and the **motor model**.

### Crux 2 — Is human cursive reading TRAINING-FREE-compatible?

**Partly, with an honest asterisk.** Two things are true at once:
1. Humans do NOT run a labelled-corpus backprop trainer. Reading is acquired
   *unsupervised/self-supervised* from the child's own reading and, crucially,
   *concomitant writing* (VWFA "recycling"; motor co-representation). The
   mechanisms — statistical internalisation of letter distributions, learning
   your own motor generator, building a lexicon — are all donkey=0-shaped
   (structure grown from observation, not weights fit by a teacher signal).
2. But it IS *lifetime-learned*. Dehaene: expertise is years of exposure that
   "internalises the distributional statistics of letters"; length effects
   vanish only with practice. The strong *lexical prior* and the strong *motor
   generator* are both learned, from a lot of data.

**The honest conclusion:** human cursive reading is training-free in the
*mechanism* sense (no backprop, no labels — self-supervised structure growth)
but NOT in the *zero-experience* sense. It substitutes a **learned strong
prior (lexicon + own motor model) and a feedback loop** for the trained visual
posterior. The machine literature (C2) warns that context alone cannot rescue
an 18% posterior to usable words in a *feed-forward* pipeline. Humans get away
with a weak per-letter channel because (a) the loop is *bidirectional*
(word→letter feedback, which our collapse currently lacks) and (b) they own
a *strong writer-adapted motor generator* that turns the weak visual channel
into a strong within-writer channel (BAP: 93% once the writer is known).

**Implication:** the donkey=0 path is not "context rescues weak letters"
(that is the feed-forward regime the machine literature shows is
insufficient). It is: **build the two learned-but-not-backprop priors humans
use — the strong own-motor generator (which we already have: we can WRITE) and
a strong lexical prior — and close the loop between them and the letter
channel.** Writer adaptation is not optional polish; BAP shows it is the
difference between 50% and 93%.

### The ranked training-free path

**(a) MOTOR / AbS reading, INCREMENTAL + PREDICTIVE + WRITER-ADAPTED — RANK 1.**
Rationale: it is the biologically native path for handwriting (B4), it is the
one model that unifies our working writer with reading (BAP, C3), and it
turns the razor per-letter margin into a strong within-writer signal *once the
writer's generator is estimated* (BAP 93% known-writer). The literature
supports *incremental prediction* over whole-word matching: Graves-2013
generates cursive by predicting one point at a time; CTC scores by alignment
not whole-shape; whole-word matching is exactly what re-entangles pose with
the writing envelope (our RUN-16 finding). Concretely: read = infer the
writer's low-dimensional sigma-lognormal-style generator from the trace so
far, then *predict-and-verify* the next letter's trace incrementally (AbS
inner loop), letting the lexical prior feed back into which letter to
synthesise-and-check next. This is the interactive-activation loop realised as
analysis-by-synthesis. **Risk:** inferring the writer's generator from little
ink is itself hard; cross-writer it is the 50% regime until adapted. But this
is the only path with a proof-of-existence at 93% (BAP) and a working
generator on our side.

**(b) WORD-SHAPE + STRONGER LM — RANK 3 (support, not engine).** The psychology
demotes word-shape/envelope for print (B3), and our own runs found envelope
weak (scrambled letters matched). A pure envelope+LM reader is unlikely to
clear the floor. But **a genuinely stronger lexical prior with word→letter
FEEDBACK** (not our current one-directional collapse) is essential as the
top-down half of path (a). So: keep the LM, but as bidirectional feedback into
the letter channel, and do not expect envelope features to be the lever. Cheap
to add, high value *as the feedback term*, low value *as a standalone reader*.

**(c) A STRONGER TRAINING-FREE PER-UNIT POSTERIOR via metric learning from
exemplars — RANK 2, with a donkey=0 boundary flag.** Learning a discriminative
metric (e.g. a linear/Mahalanobis transform, or exemplar-weighted distance)
from the exemplars we already hold is "learning" but is NOT a trained neural
net — it is the same category as our earned codebook / ShapeSignature growth
and the Fisher weighting already tried. **Where the line is:** fitting a
closed-form/convex metric or growing exemplar prototypes = donkey=0-compatible
(structure grown from observation, no backprop over a deep net); training an
MLP/CNN/RNN feature extractor with SGD = crosses into trained-net territory,
NOT donkey=0. Fisher weighting already failed once, so a *new* discriminative
signal is needed — most likely the **pose/placement channel that invariance
throws away**, re-admitted in a *writer-relative* frame (see plan step 2).
This is really a component of path (a): the writer-adapted frame is what makes
pose discriminative again.

**(d) Accept the boundary — RANK 4 (the honest fallback).** If, after a
writer-adapted AbS loop with bidirectional lexical feedback, cross-writer word
reading still floors, the honest position is: cross-writer cursive per-letter
reading from geometry alone is at the human bottom-up limit (~50%, BAP), and
usable accuracy *requires* either writer adaptation (in-context, a few lines)
or a lifetime-learned prior we are choosing not to train. Report both the
within-writer number (should approach BAP's ~93%) and the cross-writer number
honestly; do not fake the latter.

### Concrete staged plan (each step: what it tests, honest risk)

**Step 1 — Close the top-down loop: bidirectional word↔letter feedback.**
Replace the one-directional lexicon collapse with an interactive-activation /
mutual-constraint loop: partially-activated lexicon entries feed activation
*back* to re-score per-letter candidates, iterate to a fixed point (this is
natural as a `run_rules` fixpoint — the loop IS the decode→re-decode we
already run for codebook growth). *Tests:* does word→letter feedback lift char
*and* word accuracy on hand-PRINT above the current feed-forward 67%/78%
(cheap regime where the letter channel is already decent)? *Risk:* if it only
helps where the posterior is already good (print), it confirms the C2 warning
— feedback multiplies a decent posterior, doesn't create one — and cursive
still needs Step 2/3. Low cost, high diagnostic value; do first.

**Step 2 — Re-admit POSE in a WRITER-RELATIVE frame (writer-adaptation as
generator estimation).** The separating signal we discarded (pose/placement)
is writer-dependent; estimate a per-writer frame (baseline, slant, x-height,
join geometry — the sigma-lognormal "virtual target" grid) from the current
line/word, then measure each letter's pose *relative to that estimated frame*.
This is BAP's "known writer" condition made operational, and the donkey=0
metric-learning of (c) done in the right coordinates. *Tests:* does
within-writer char accuracy rise toward BAP's 93% when pose is scored in the
writer's own frame? Report within- vs cross-writer separately. *Risk:*
estimating the frame from little ink is unstable (the 50% regime lives here);
needs enough of a line to fix the frame. This is the highest-leverage step and
the hardest.

**Step 3 — INCREMENTAL AbS reading (predict-and-verify), not whole-word
match.** Use our working writer as the forward model: given the writer frame
(Step 2) and lexical hypotheses (Step 1), *synthesise* the predicted next
letter's stroke incrementally and compare to the ink at that span (AbS inner
loop over the `vit` span lattice), advancing left-to-right and letting the
prediction pick the segmentation. This is CTC-style recognition-by-alignment
with our generator as the emission model, and Graves-2013-style
one-point-at-a-time prediction. *Tests:* does incremental AbS beat whole-word
render-and-compare (RUN-16 verdict layer) on cursive, and does it dissolve the
pose/envelope re-entanglement? *Risk:* synthesis-per-hypothesis is expensive;
needs the lexical prior (Step 1) to prune hypotheses hard, and the writer
frame (Step 2) to make the synthesis match. Depends on 1 and 2 landing.

**Step 4 — Motor co-representation: read with the SAME generator we write
with.** Make reading and writing literally share the stroke codebook /
generator (BAP common-coding; the biological B4 result). The writer's learned
joins (RUN-63/65) become the recognition emission model directly; no separate
reading representation. *Tests:* does sharing the generator (vs a separate
reading codebook) improve cursive reading, replicating the human
co-representation benefit? *Risk:* our writer was taught on our own synthetic
curriculum; real cursive writers are style *families* (RUN-9/15 finding), so
the shared generator may need the writer-adaptation of Step 2 to bridge to a
real hand. Mostly an integration/ablation step once 1-3 exist.

**Step 5 — Honest cross-writer gate + boundary report.** Power the gate
(RUN-15 standing rule): report within-writer and cross-writer word accuracy
with CIs, against the BAP calibration (93% / 50%). If cross-writer clears a
useful bar with a few adaptation lines, we have a training-free reader that
adapts like a human. If it floors at ~50% without adaptation, that is the
honest boundary (path d): cursive reading is writer-adaptive or lifetime-
learned, and we say so. *Tests/Risk:* this is the truth-telling step; the risk
is only self-deception, guarded by the powered gate.

### Ranking rationale in one line

Motor/AbS + writer-adaptation + bidirectional feedback (Steps 1-4) is Rank 1
because it is the *only* configuration with an existence proof at 93% (BAP),
it reuses our working writer, and it matches the human architecture (weak
letters + strong own-motor prior + top-down loop). Metric learning (c) is
Rank 2 but only *inside* the writer-relative frame. Word-shape/envelope (b) is
Rank 3 and only as the feedback term. Accepting the boundary (d) is the honest
Rank 4 fallback, to be reported not hidden.

---

## Search coverage and honest caveats

**Well-covered (multiple independent sources, specific numbers/quotes):**
word-superiority effect (Reicher 1969, Wheeler 1970) and interactive
activation (McClelland & Rumelhart 1981); word-shape debunk (Larson);
motor activation in reading handwriting (Longcamp 2003/2005); VWFA learned
expertise (Dehaene); Graves 2009 CTC and 2013 synthesis; Plamondon
sigma-lognormal; Lake et al. 2015 BPL; the BAP model (Gilet, Diard, Bessière
2011) with its 93%/50% numbers; the DBLSTM-CTC LM effect (22.2%→17.3%);
the four cursive curricula.

**Thin / not fully nailed:**
- I could not extract exact *cursive-specific* CER-without-LM figures at the
  starved (~18%) regime we operate in — the trained systems never run that
  weak, so the literature has no direct analogue. The C2 conclusion (LM
  multiplies a decent posterior, doesn't create one) is inferred from the
  strong-visual regime, not measured at 18%.
- The BAP "unknown writer 49.68%" is a per-*letter* number on their letter
  set (26-way), not word accuracy, and on their stimulus set — treat as a
  calibration analogue, not a like-for-like transfer to our benchmark.
- Envelope-for-cursive specifically: the debunk literature is about print;
  I did not find a clean cursive-envelope study either way. Our own runs are
  the main evidence that envelope is weak for cursive.
- I did not deep-fetch every primary PDF (some arXiv PDFs returned raw
  streams); several numbers are from abstract/summary pages and secondary
  syntheses (flagged inline). Primary-source verification of the DBLSTM-CTC
  numbers and the BAP internals would strengthen the report.
- "Human per-letter cursive is weak" is established via the WSE/context
  literature and BAP, which is *indirect* for cursive specifically; I found no
  study that isolates human cursive single-letter accuracy stripped of all
  context. The inference is strong but not from a single decisive experiment.

## Key citations

- Reicher, G. M. (1969). *Perceptual recognition as a function of
  meaningfulness of stimulus material.* J. Exp. Psychol. — word-superiority.
- Wheeler, D. D. (1970). *Processes in word recognition.* Cognitive Psychology.
- McClelland, J. L. & Rumelhart, D. E. (1981). *An interactive activation model
  of context effects in letter perception.* Psychological Review. (+ McClelland
  2014, Cognitive Science, mutual constraint satisfaction.)
- Larson, K. *The Science of Word Recognition* (Microsoft Typography). —
  parallel letter recognition; word-shape debunk.
- Longcamp, M., Anton, J.-L., Roth, M., Velay, J.-L. (2003, 2005). Premotor
  activation viewing letters; hand-specific in left-handers.
- Dehaene, S., Cohen, L., McCandliss, B. et al. *The Visual Word Form Area:
  expertise for reading in the fusiform gyrus* (TICS 2003) + reading as
  statistical/learned expertise.
- Graves, A. et al. (2009). *A Novel Connectionist System for Unconstrained
  Handwriting Recognition.* IEEE TPAMI 31:855-868. — BLSTM+CTC, segmentation-free.
- Graves, A. (2013). *Generating Sequences With Recurrent Neural Networks.*
  arXiv 1308.0850. — cursive synthesis by one-point-at-a-time prediction.
- Gilet, E., Diard, J., Bessière, P. (2011). *Bayesian Action-Perception model…
  cursive letters.* PLoS ONE. — motor simulation in recognition; 93% known /
  50% unknown writer. **Most directly relevant.**
- Lake, B., Salakhutdinov, R., Tenenbaum, J. (2015). *Human-level concept
  learning through probabilistic program induction.* Science 350:1332. — BPL,
  Omniglot, motor-program characters.
- Plamondon, R. et al. *Kinematic Theory / sigma-lognormal model* (multiple;
  "The lognormal handwriter," PMC3867641).
- Liu, Wang et al. *Effects of Implicit/Explicit LM for DBLSTM-CTC HWR* (arXiv
  2008.01532) — IAM WER 22.2%→17.3% with explicit LM.
- Curricula: Palmer Method, Zaner-Bloser, D'Nealian, Spencerian (Wikipedia +
  Cursive Workshop + Zaner-Bloser standards).
