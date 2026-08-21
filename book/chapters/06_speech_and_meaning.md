# 6 · Speech, and What Words Mean

*Draft. Sources: `docs/features/audio-speech.md`; `docs/research/audio_speech/`
(≈146 documents); `docs/research/agent_loop/` (≈71, including the numbered
iteration log). Register per `BOOK_VOICE.md`.*

---

A child learning to speak has a harder problem than the one usually described.

It is not "map sounds to meanings". Before that can start, the sounds have to
be separable, and they are not: speech arrives as a continuous acoustic stream
with no gaps at the word boundaries. And the meanings are not given either — a
pointed finger and a spoken word underdetermine what the word refers to, which
is philosophy's *gavagai* problem and a toddler's ordinary Tuesday.

**This chapter reports a system that learns word meaning from real children's
television and speech structure from real audio, from scratch, faster than
real time on a consumer CPU, with no pretrained model anywhere in the decision
path.** And it reports a second thing, which is more interesting: **the order it
learned things in matches the canonical order of child language acquisition,
without that order having been imposed.**

Those are separable claims and the chapter keeps them separate, because they
fail differently.

---

## 6.1 The scale, stated first

This is a research prototype. The grounded vocabulary is a handful of words.

That number is small enough that it should be established before anything else
in the chapter is read, because every claim below is bounded by it. What is
being demonstrated is a *method and its cost profile* — no pretrained encoders,
no GPU, faster than real time on ordinary hardware — not a recogniser competitive
with a deployed system.

The tree's own shorthand for the constraint is that no borrowed model appears in
the decision path. Pretrained tools appear at all only as removable bootstrap
scaffolds or as evaluation-only scorers, never as something the agent's own
decisions route through. The point of that constraint is not purity; it is that
a capability standing on a borrowed model teaches you nothing about whether the
mechanism under it works.

---

## 6.2 The developmental order, which was not imposed

Here is the claim that makes this more than a small recogniser.

The system traversed the canonical stages of child language acquisition, in the
canonical order, hitting the canonical problems and solving them the canonical
way — and the order was **not** a curriculum. Each stage was reached because the
previous one had run out of room.

**Production before perception.** The system learned to perceive speech by
*inverting its own babble*. It makes a sound, hears what it made, and thereby
acquires a mapping from acoustic result back to the articulatory act that caused
it. This is motor theory, and its developmental version — babbling as the route
into perception rather than a byproduct of it. Chapter 5's analysis-by-synthesis
is the same architecture in a different modality: propose, render through a
forward model, compare.

**Perceptual narrowing before word recognition.** Sensitivity tuned to the
ambient sound distribution — sharpening the contrasts that matter in the
language present and letting others go — before word-level recognition worked at
all. The developmental literature has this well documented, and it is
counterintuitive as an engineering choice: the system gets *worse* at
discriminating sounds it will not need.

**The meaning problem, hit and diagnosed.** Isolated sound-form recognition
turned out to be a dead end. Recognising that a particular acoustic pattern
recurs is not the same as knowing it means something, and there is no amount of
better acoustic modelling that crosses the gap. A deliberate literature check
caught this as a wrong turn and corrected it, which is worth recording as a
methodological event: the correction came from reading, not from measurement.

**Word learning under referential ambiguity.** The gavagai problem, solved the
way children solve it — cross-situational statistics accumulated over many
partial exposures, plus joint attention narrowing the candidate set at the
moment of the utterance. Neither alone is sufficient; the combination is.

**Meaning reshaping perception.** Then the reversal. Once words have referents,
the referential structure *preserves acoustically weak contrasts* that pure
sound-learning would discard as noise — because two forms that sound nearly
identical but mean different things are worth telling apart, and nothing in the
acoustics says so. Perception, having bootstrapped meaning, is then reorganised
by it.

**Communication as a two-mind problem.** Modelling what the listener knows, and
repairing when they have misunderstood.

**Grounding in real multimodal footage.** Binding word to object at ostensive
moments, using the agent's own earned vision — chapter 1's eye — rather than a
pretrained vision network.

**And the repetition law**, which was rediscovered rather than imported:
vocabulary grows through *depth* of genuine repetition, not breadth of exposure.
Which is the mechanistic reason children's television is so relentlessly
repetitive. The system found this because its own vocabulary growth depended on
it, and only afterwards was it recognised as a known result.

---

## 6.3 Why the order is the evidence

A system built to a curriculum proves nothing about developmental order: it
proves someone knew the order. This one is interesting only insofar as the
stages arrived because the previous stage had exhausted its own room.

That is a claim about *residual*, and it is chapter 3's claim in a different
domain. Each stage ends when its representation stops covering what arrives.
Sound-form recognition saturates and leaves a residual that no acoustic
refinement absorbs — the residual is *meaning*, and it is not in the signal.
Word-meaning pairing saturates and leaves a residual that is not in the
utterance either — it is in the listener.

The stages, on this reading, are not developmental milestones. They are the
successive shapes of what the previous representation could not cover.

The honest bound: *not imposed* is a claim about the design, and the design is
inspectable. What it is not is a controlled demonstration that the order is
forced. To show that you would need to attempt the stages out of order and fail,
and that experiment has not been run.

---

## 6.4 The self-directed loop

The bulk of the record here is not a curated summary. It is the working log of
the agent's own **synthesise → pick → build → measure** loop, run against its
standing problem: recognising the same word across different speakers.

Reading it late in the arc gives the flavour of the mechanism, and one iteration
pair is representative.

The recogniser combined evidence from several nodes, each weighted by how
reliable it had been. Iteration 48 found that a single reliability weight per
node is **too coarse** — a node can be confidently wrong on one specific
contrast, say *b* against *d*, while averaging perfectly well. Its average
reliability then dilutes exactly the contrast it is bad at, everywhere.

Iteration 49's fix gives each node its own admissibility structure per contrast:
reliability becomes per-(word, contrast) rather than per-node, so a node can
*abstain* on precisely the distinctions it is unreliable for instead of dragging
down every prediction with its mean.

That is a refusal, in the sense chapter 3 gave the word — an abstention creating
a residual where a confident average would have buried it. And the combination
step is graph evaluation rather than host arithmetic: a product over per-node
blends toward a flat prior, expressed as terms.

The recurring levers across the loop are worth naming for anyone scanning: a
leave-one-speaker-out protocol as the standing cross-speaker metric; dynamic
time warping as the single largest cross-speaker jump found; the order-*N*
machinery of chapter 4 applied to formant trajectories; and
analysis-by-synthesis as the recurring architecture.

The cognition itself — fusion, back-off, the recognition path — has since been
migrated out of the host language into native terms, the same cutover chapter 4
describes for the loop.

---

## 6.5 What would falsify this

- **The developmental claim.** If the stage order can be shown to have been
  induced by the training material's own structure rather than by successive
  residuals, §6.2 becomes a fact about the corpus. This is the most likely place
  for the chapter to be wrong.
- **The from-scratch claim.** It rests on a source audit: no borrowed model in
  the decision path. A single path where a pretrained component's output reaches
  a decision would falsify it, and the audit is mechanical enough to repeat.
- **The repetition law.** If vocabulary growth under matched exposure is
  indifferent to repetition depth, the rediscovery is an artefact of the
  training schedule.
- **The cost profile.** Faster than real time on a consumer CPU is checkable and
  should be re-checked at a larger vocabulary, where it is most likely to fail.

The bound that matters most is §6.1's, and it applies to every sentence above: a
handful of grounded words is a demonstration of a method. Whether the method
scales is not established here, and no result in this chapter should be read as
suggesting it is.

---

*Ends. Next: chapter 7, where the same loop meets a space the agent has to move
through — and where what is unknown has to be represented as unknown.*
