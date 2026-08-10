---
title: "Fixing Whisper - Using a graph substrate to in-place modify trained models without gradient descent"
status: draft
---

# Fixing Whisper - Using a graph substrate to in-place modify trained models without gradient descent

What if, instead of retraining a neural network when it behaved badly, we
could read it, understand the relevant part of its computation, and make a
small, reversible correction?

That is what we have been teaching Jabberwock, our graph-based cognition
engine, to do.

We tried the idea at three very different scales:

1. a tiny digit recogniser, where the desired change is completely obvious;
2. Whisper, where a widely reported hallucination failure has a real but
   easily misunderstood mechanism; and
3. [Gemma 4](https://ai.google.dev/gemma/docs/core/model_card_4), where we
   asked for an intentionally silly change—make informal replies more
   sweary—while preserving several named behaviours.

The progression matters. The digit recogniser shows that the machinery can
make an exact change. Whisper shows that it can investigate a real model,
reject a tempting but false explanation, and find a more defensible one.
Gemma shows that the same method is not specific to speech recognition.

None of these changes used gradient descent, fine-tuning, a LoRA training run,
or a search through candidate patches.

The central idea is simple:

> Treat a trained model as a program that can be understood and edited, not
> only as a black box that can be prompted, tested, or retrained.

## First: the change you can see immediately

Before attempting Whisper, we wanted the smallest possible demonstration.

Imagine a recogniser with three outputs:

```text
zero    one    two
```

We ask Jabberwock to change its meaning so that every input previously called
“zero” is now called “two”, every “two” becomes “zero”, and “one” is completely
untouched.

For the final layer of this small recogniser, those three meanings correspond
to three rows of numbers. Jabberwock reads that structure and concludes that
the exact edit is to exchange the “zero” and “two” rows, including their
biases.

That sounds almost trivial—and that is why it is a useful first example. There
is nowhere for a vague explanation to hide.

After the edit:

- the zero and two scores are exchanged for every possible input;
- the one score is exactly unchanged;
- applying the same edit again restores the original model; and
- the model does not need to see a single training example.

This miniature recogniser is a structural demonstration, not an accuracy
benchmark. Its purpose is to establish the basic contract: Jabberwock can
derive a requested behavioural change from the organisation of a network,
apply it directly to the model, state exactly what it preserves, and undo it.

The interesting question is whether that contract survives contact with a
real failure in a real published model.

## Whisper gave us a convincing wrong answer

[Whisper](https://openai.com/index/whisper/) is a strong speech-recognition
model, but like other speech systems it can produce fluent text when the audio
contains silence, noise, music, or something speech-like that is not actually
speech.

We began by asking Jabberwock to find where that behaviour lived.

It systematically suppressed parts of Whisper and measured what happened on
spoken digits and matched non-speech controls. One attention head appeared to
be a striking result: suppressing it reduced false transcripts on held-out
non-speech audio by 66.7%.

That could easily have become the headline.

It was also not a valid repair. Suppressing the head damaged real speech
recognition.

Jabberwock then tried a more selective policy. It used Whisper’s own estimate
that a segment contained no speech and only suppressed the head in suspicious
cases. False transcripts fell by 69.2%, while measured speech accuracy no
longer fell.

That looked better—until the control experiment.

The same policy using a randomly selected head performed just as well. The
useful part was listening to Whisper’s no-speech signal. The supposedly
special head was not special.

This negative result is one of the most important parts of the work. A system
that can produce explanations but cannot discard an attractive explanation
when a control defeats it is not doing science. It is generating stories.

Jabberwock retained the failed result in its graph and changed the question:

> If the no-speech estimate is useful, what does Whisper actually do with it?

## Reading Whisper as a program

Whisper does more than turn audio into words. Its transcription code combines
the neural network’s outputs with a policy for deciding whether a segment
should be skipped.

In simplified form, that policy says:

```text
if the no-speech evidence is strong:
    plan to skip the segment

if the proposed transcript is very confident:
    cancel that decision
```

The second rule exists for a sensible reason. Whisper’s no-speech estimate can
be wrong, and a highly confident transcript can rescue real speech.

But it also creates a precise failure mode. Whisper can simultaneously have:

- strong evidence that nobody spoke; and
- a fluent, high-confidence transcript supplied by its language model.

In that situation, confidence wins and the segment is transcribed.

Jabberwock did not reach this conclusion by asking a language model for a code
review and trusting the prose. It converted the relevant model and source
structure into a graph: model parts, parameters, program variables, decisions,
conditions, and the order in which values are changed. Rules then connected
the no-speech signal, transcript confidence, and the skip decision.

The resulting explanation points to the specific later operation that cancels
the earlier decision.

## The proposed Whisper repair

Given the goal “transcript confidence must not cancel an already established
no-speech decision,” Jabberwock authored a small source change that preserves
the earlier decision.

Before allowing the edit, it checked that:

- both operations really affect the same skip decision;
- the confidence-based operation happens later;
- the three signals have the meanings claimed for them; and
- the source code is byte-for-byte the version that was inspected.

If any of those conditions is false, the patch is refused.

This is a real diagnosis and a compilable correction to the inspected Whisper
source. It is not yet a claim that the stricter policy improves Whisper in
every setting. That requires a fresh evaluation on continuous speech, silence,
music, environmental sound, accents, difficult recordings, and multiple
Whisper sizes.

The honest result is:

> Jabberwock found and removed a concrete path by which language confidence
> can override Whisper’s prior decision to abstain. The broader quality of
> that policy change remains to be measured on new data.

That distinction—between proving what a change does and proving that it is a
good product decision—is essential.

## What is—and is not—novel

We are not claiming to be the first people to reduce Whisper hallucinations.
For example, [Calm-Whisper](https://arxiv.org/abs/2505.12969) uses head masking
to locate hallucination-related behaviour and then fine-tunes selected heads.
Other work uses learned
[sparse-autoencoder features](https://arxiv.org/abs/2606.07473) to detect and
steer related internal states.

Our result is about a different capability: a cognition engine reading a
published network and its inference program, falsifying its own initial causal
story, and compiling a direct, reversible change from the structure it found.
The method is the proposed contribution, not the claim that nobody has
mitigated this failure before.

## Editing Whisper itself, not merely wrapping it

The investigation also gave us a second kind of result.

During the experiments we suppressed attention heads using temporary runtime
hooks. Jabberwock inspected Whisper’s attention calculation and found that the
same intervention could be compiled into a direct change to the corresponding
part of the model’s output weights.

It then checked that:

- the direct weight edit and the temporary intervention produced exactly the
  same calculation;
- unrelated weights were unchanged;
- the edit applied only to the intended head; and
- restoring the saved values returned the whole model to its original hash.

The measured numeric difference between the two implementations was zero.

This does **not** revive the rejected claim that this particular head is the
right semantic repair. It establishes something different and reusable:
Jabberwock can turn a temporary experiment into an exact, reversible in-place
model edit once it understands the surrounding computation.

The failed causal claim and the successful engineering claim coexist. One
should not be used to smuggle in the other.

## Then we tried something deliberately odd

A Whisper-specific tool would be interesting but limited. We wanted to know
whether the same faculty could alter a very different kind of network.

So we gave Jabberwock an intentionally conspicuous goal for Google’s Gemma 4
language model:

> In a few informal, frustrated contexts, use a stronger and more profane
> reaction—while leaving named formal, code, and safety-refusal responses
> unchanged.

This was not an attempt to remove safety training. It was a harmless style
change chosen because the result is immediately visible and cannot be mistaken
for a rounding error.

The obvious edit would have been unsafe. Gemma uses some of the same weights
both to read tokens and to choose output tokens. Directly changing the output
rows could therefore also change how the model understands those words when
they appear in a prompt.

Jabberwock noticed that shared structure and chose a different intervention
point: a small removable addition after the shared output calculation. It
derived that addition directly from the requested before-and-after
constraints—there was no training loop and no candidate search.

On the official Gemma 4 E2B-IT checkpoint, the change produced:

| Situation | Before | After |
| --- | --- | --- |
| Third deployment failure | “Ugh…” | “Damn.” |
| Cache-deleting bug | “Ugh.” | “Fuck.” |
| Supposedly fixed build breaks | “Ugh, seriously?!” | “Damn! …” |

At the same time, the captured response prefixes for:

- a formal factual answer;
- a code-only answer; and
- a safety refusal

remained identical.

The resulting adapter was rank two, independently removable, and left every
original Gemma parameter untouched. Removing it restores the original
computation.

The protection claim is deliberately narrow. We proved the requested change
and zero effect on the particular captured response paths. We did not prove
that every formal answer, every program, or every safety response is unchanged.
Generalisation beyond those named situations is a separate empirical question.

That limitation is not an embarrassment. It is the boundary of the evidence.

## What the graph contributes

The graph substrate is not merely a diagram of work performed elsewhere. It
holds the objects needed to reason about the edit:

- the parts of the published model;
- the meanings assigned to relevant signals;
- the requested behavioural change;
- the structural facts that make an edit legal;
- the promises the edit makes;
- the evidence needed before those promises are accepted; and
- the information required to reverse the change.

The surrounding Python code is allowed to inspect tensors, expose source
structure, carry out an edit already selected by the graph, and report the
result. It is not allowed to quietly choose the component, rank candidate
patches, or decide that a result is good enough.

This separation matters because otherwise an apparently graph-native agent can
hide all of its real decisions in a conventional experiment script.

In less formal language, the workflow is:

```text
read the model
    ↓
state the intended change
    ↓
derive an edit from the model’s structure
    ↓
list what must be true for that edit to be valid
    ↓
refuse, or apply it with a receipt and an undo path
```

## Why not just retrain?

Retraining remains the right tool for many problems. If we want a model to
learn a broad new skill from many examples, gradient descent is extraordinarily
effective.

But retraining often answers “what parameter change improves this score?”
rather than:

- What precise mechanism produced the failure?
- Why is this particular edit legal?
- Which behaviours are guaranteed to remain unchanged?
- Does the patch apply to this exact model version?
- Can it be reversed exactly?
- Did the proposed explanation survive a meaningful control?

Graph-based model engineering is complementary. It is most attractive when a
change is narrow, the relevant computation can be understood, and we care
about a precise account of what was altered.

The three demonstrations have different strengths:

| Demonstration | What it establishes | What it does not establish |
| --- | --- | --- |
| Digit recogniser | Exact all-input class swap and exact reversal | A difficult real-world diagnosis |
| Whisper | Real causal investigation, falsification, source diagnosis, and compilable repair | Production-wide hallucination reduction |
| Gemma 4 | A non-trivial contextual edit at a safe architectural boundary | Global preservation outside the named response paths |

Together they are more informative than any one of them alone.

## The methodology is the result

The first Whisper result would have made a cleaner story:

> We found the hallucination head and turned it off.

Unfortunately, the control experiment showed that story was false.

The better story is about a system that can recover from being wrong:

1. It formed a causal hypothesis.
2. It found a large held-out improvement.
3. It noticed collateral damage.
4. It introduced a conditional policy.
5. It compared the result with a matched random control.
6. It rejected its component-level explanation.
7. It followed the surviving no-speech signal into the published program.
8. It derived a narrower repair from the actual control flow.
9. It kept the untested consequences outside the claim.

That is the behaviour we want from a cognition engine. The purpose is not to
produce a clever modification at any cost. It is to understand enough of the
object to make a justified change, know what has been proved, and retain the
ability to say “the evidence did not support our original explanation.”

## Reproducing the work

The repository contains the full technical details, preregistrations, graph
rules, scripts, machine-readable results, and tests:

- `docs/published_model_engineering.md` describes the exact model-editing
  machinery and the digit-recogniser transformation;
- `docs/whisper_autonomous_causal_debugging.md` documents the causal study;
- `results/whisper_causal_debugger_replication.json` contains the held-out
  Whisper measurements;
- `results/whisper_deterministic_engineering.json` records the source diagnosis,
  parameter edit, hashes, and rollback;
- `docs/contextual_model_editing.md` and
  `results/gemma4_contextual_style_edit.json` describe the Gemma 4 experiment.

The Whisper work used OpenAI’s official `base.en` checkpoint and a pinned
revision of the
[Free Spoken Digit Dataset](https://github.com/Jakobovski/free-spoken-digit-dataset).
The Gemma experiment used Google’s official Gemma 4 E2B-IT checkpoint. The
model files remain outside the repository.

## What comes next

The immediate Whisper experiment should be a preregistered evaluation of the
source repair on genuinely new material:

- real silence and environmental sound;
- music and speech-like noise;
- ordinary and difficult continuous speech;
- multiple speakers, accents, and recording conditions; and
- more than one Whisper model size.

The larger program is to teach the graph substrate more of the language of
neural networks: convolutions, residual paths, normalization, nonlinearities,
tied parameters, quantisation, and cross-layer data flow. Each newly understood
operation creates another family of edits that can be derived rather than
searched for.

The long-term goal is not a collection of one-off model hacks. It is a
general-purpose ability to inspect unfamiliar trained systems, explain a
specific behaviour, make a bounded change, and carry the evidence and the undo
operation with the patch.

## Conclusion

We began with a digit recogniser because it made correctness easy to see.

We moved to Whisper because it offered a real, consequential failure—and
because it forced Jabberwock to abandon a compelling wrong explanation.

We moved to Gemma because a deliberately strange style change showed that the
method was not tied to one architecture or one task.

The most important result is not that one model says “two” instead of “zero,”
that Whisper can be made more reluctant to transcribe, or that Gemma can be
made to swear.

It is that a graph substrate can turn a trained network into something closer
to an inspectable engineered system: a thing whose relevant structure can be
read, whose changes can be justified, whose limits can be stated, and whose
edits can be undone.
