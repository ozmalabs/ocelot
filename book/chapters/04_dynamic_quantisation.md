# 4 · Dynamic Quantisation

*Draft. The implementation chapter for chapters 2 and 3. Sources:
`docs/features/dynamic-quantization.md`, `runners/dsl/src/shape_decode.rs`,
`seeds/shape_decode_loop.json`, `runners/dsl/src/space_quantize.rs`,
`CLAUDE.md` § dated arc entries. Figure: SD-1.*

---

Chapter 3 argued that a substrate needs a way to decide something is new. This
chapter is that mechanism, in the code that runs it.

The name is literal rather than metaphorical. **Quantisation** is expressing a
signal as indices into a codebook of representative pieces — the operation
behind every codec that has ever compressed anything. **Dynamic** quantisation
is that operation with one constraint removed: the codebook is not fixed in
advance. It grows, as a side effect of the same decode that uses it.

That single change is the difference between a compressor and a learner. A codec
with a fixed codebook meets a novel input and does its best. A codec whose
codebook grows meets a novel input, fails to cover it, and — if the failure
recurs — acquires the piece it was missing.

**The claim of this chapter: growth is not a phase attached to this loop. It is
the loop reaching fixpoint.**

---

## 4.1 The operation

An observation arrives. It is decoded against a held codebook of shapes: parts
of the codebook compete to cover parts of the observation, an assignment
emerges, and whatever is not covered is the **residual**.

Three things about that sentence are load-bearing.

**Parts compete.** This is not a lookup. Multiple held shapes may partially
explain the same observation, and which assignment survives is decided by
coverage rather than by order of trial.

**The residual is first-class.** It is not an error signal to be minimised or a
remainder to be discarded. It is the object the rest of the loop operates on,
and chapter 3 explains why: it is the only admissible evidence that something
new is present.

**The same operation runs in both directions.** Decoding an observation against
held shapes, and decoding a *goal* against held capabilities to see what would
satisfy it, are the same call with different inputs. What had been two separate
Python subsystems — a beam search that composed designs for goals, and a
procedure that induced concerns from observations — are the same operation at
two points of one loop. Deleting them and replacing both with one term is the
form the migration took.

---

## 4.2 The ladder

A residual could mint immediately. It must not, and the ordering is the design
[SD-1].

**Rung 1 — recognise.** The observation is covered well enough by what is held
that nothing is worth adding. This is the common case and the cheapest.

Note what that does *not* say. It does not say the residual is zero — chapter
14's standpoint axiom guarantees it never is, since every view is partial. The
ladder is not asking *is there a residual*, a question with a standing answer.
It is asking whether **this** residual pays: whether acting on it compresses.
Which is also why the loop terminates. Not because residual runs out, which it
cannot, but because it stops earning.

**Rung 2 — transform in the existing basis.** The residual is one uniform step
along a dimension the codebook already has. A rotated shape, a shifted one, a
scaled one: same shape, different position along a known axis. What is added is
a `Transform{dimension, delta}` — a small piece of graph data recording the step
— and not a new shape. The predicate slot is never transformable, and an
identity transform is flagged rather than accepted.

**Rung 3 — infer a dimension.** The residual is *coupled* across the dimensions
the system can see, in a way none of them explains: the canonical example is
rotating a flat rectangle in a third dimension, which produces a change in the
two you can see that no combination of those two can reproduce. Such a residual
is decoded against a held codebook of **dimension generators** — rotations,
reflections, the multiplicative and modular bases of chapter 2 — and if one
fits, a `LatentDimension` is minted. The dimension set is itself dynamic:
quanta *of* dimensions.

This rung is load-bearing well beyond its size, and chapter 14 collects on it:
**time is minted here.** A system is not handed a temporal coordinate by any
observation — succession is a relation between states, not a property of one —
so a time axis has to be *inferred*, and this is the operation that infers it.
Which means the capacity for time is downstream of the capacity for inference,
and a system without this rung has succession and no time at all.

**Rung 4 — mint novelty.** Only when all three fail. A new codebook entry, a
genuinely new shape.

The order is Occam's razor made operational: try the cheapest description first,
and add to the codebook only what three cheaper readings could not absorb.

### Why this criterion requires a generator

One consequence of the criterion is not obvious and is load-bearing for three
later chapters, so it belongs here rather than where it is used.

**You cannot compute a residual without rendering.** "What the codebook
explains" is not a number the codebook hands you; it is a *reconstruction* you
have to produce and subtract. So the moment growth is driven by residual, the
system has committed to generation — a decoder that emits only an index cannot
say what it failed to account for.

And two models cost two descriptions. A recogniser and a generator held
separately store the same codebook twice, in two parameterisations that can
silently disagree; one model used in both directions costs half as much and its
consistency is structural rather than maintained. The criterion takes that trade
without being asked.

**Which is why generation and perception are one model here.** Not as a design
preference, and not because it measured well on a benchmark — chapter 5 reports
the run where its measured advantage evaporated, and the architecture was
unaffected, because a benchmark delta cannot touch something the growth
criterion entails. It also explains why the stroke renderer had to be the
quantiser's *exact* inverse with the round trip proven rather than assumed: an
approximate inverse contaminates the residual with its own reconstruction error,
and the growth signal stops being a measurement of the world.

Stated as a criterion rather than a ladder: **mint if and only if it
compresses.** Which is minimum description length, and it is worth noticing that
this is the same test the *author* of this substrate runs on claims — name the
assumption, remove it, and see whether anything observable was resting on it.
The loop applies it to observations; chapter 16 applies it to results; the
introduction describes it being applied, ten times over, to a single word. One
operation, three grains.

Its consequence is measurable rather than rhetorical. A rotated tromino mints
**zero** — rung 2 reads it as a step along an axis already held. A scrambled one
mints **exactly one**. A loop that minted first would have minted in both cases,
grown twice as fast, learned half as much, and — the real cost — would never
have discovered that rotation was a dimension, because it would have stored
every rotated variant as a separate thing.

---

## 4.3 The fixpoint is the loop

The rungs are rules. Not a control-flow ladder in a host language calling into
an engine — rules, in graph data, matched and fired by the same evaluator that
runs everything else.

Which means the growth loop is not a loop anyone wrote. **The rule engine's
fixpoint is the decode → grow → re-decode cycle.** A decode leaves a residual; a
residual that recurs mints; minting advances a codebook epoch; the epoch change
re-arms decode; the re-decode covers more. Run the rules to fixpoint and that
sequence happens because those rules are all live at once.

The termination argument is the epoch gate. Minting is guarded so that a given
residual mints once; the epoch bump re-arms decoding rather than re-arming
minting. Without that, a residual that recurs would mint on every pass and the
codebook would grow without bound — which is the same unbounded-growth failure
chapter 3 records for rule mirroring, and it is worth noticing that the two were
prevented by the same kind of guard.

There is no host-language iteration anywhere in it. That is not architectural
purity for its own sake: it is what makes the loop *inspectable*, because every
step is graph data the agent can read, and — per chapter 3 — what makes it
extensible by the agent rather than only by its author.

---

## 4.4 One loop, many grains

The claim that would make this a general mechanism rather than a vision
subsystem is that the same operation runs at every grain. It does, and the
evidence is unusually direct: the codebook loader is grain-agnostic, and this
was established by reading it rather than by assuming it.

- **Pixels.** Chapter 1's dimensional stack: time, depth, stereo.
- **Strokes.** Ink is quantised into relative-turn and normalised-length
  classes, with pose held as separate single-slot relations — so a rotated
  stroke is a *step along a pose dimension*, read by the unchanged transform
  rung. Chapter 5 takes this up.
- **Statements.** Program constructions, decoded from a corpus of real code
  into a codebook of construction quanta. Chapter 8.
- **Space.** Spatial quanta decoded from a persistent map belief. Below.
- **Meta-shapes.** The agent's own abstract categories. Chapter 3.

The stroke case is the most instructive, because it shows the representation
being *chosen to make the ladder work*. Encode a stroke so that similarity
transforms become per-dimension steps, and rotation costs a rung-2 read instead
of a rung-4 mint. The representation is doing work the mechanism would otherwise
have to do, which is the ordinary way this substrate makes something cheap.

---

## 4.5 The same loop, spatial

Applying the loop to space required one reframe and produced several
consequences worth stating, because they generalise.

**The map is a belief, not a grid.** What the agent holds is a persistent
observation belief in which **not-yet-observed is a state in its own right** —
not a default zero, and distinct both from a dimension that is absent altogether
and from one whose value has not been determined at all (chapter 7 makes the
full distinction). A world that hands over its whole map at load time
is then the degenerate case rather than the normal one.

**Quanta are decoded per body.** Spatial boxes are decoded from that belief
*for the body doing the routing*: a one-by-one and a two-by-two agent route
differently over the *same* underlying belief, because the decode erodes by body
shape. One belief, many decodings.

**Decoding is foveated.** It happens in the current focus region, reusing prior
decode work incrementally, rather than re-flooding the whole map.

**Resolution is per-dimension.** The flood does not occur per cell; it occurs at
quanta, and a remainder routes to a finer split *in the dimension that needs
it* — not uniformly.

The lifecycle sits in rules too: stale quanta, retirement, frontier-seeking
exploration from multiple sources. The older cell-based navigation remains
available and byte-identical to its pre-change baseline, which is the property
that made the comparison honest.

---

## 4.6 What this chapter's own record says did not work

Three results from building this belong in the chapter, because a mechanism
chapter that reports only what worked is not describing engineering.

**Unconditional mirroring: no-go.** Covered in chapter 3 — 190 files at risk,
51,769 nodes for one rule, +2,557 per reload cycle with no convergence.

**The wrong precedent, caught mid-rung.** The first primitive chosen for
persisting structure writes no graph nodes at all, which makes it precisely the
wrong model for a mechanism whose entire question is what to write. Corrected
inside the same rung.

**Dedup was never the reason.** The sizing document originally led with
compression figures — how much smaller the corpus would be — and had to correct
itself: the case for this machinery is derivation, not deduplication. The
correction stands in the document rather than replacing what it corrects.

And one engine-level gotcha found along the way, recorded because it will bite
again: two same-type incoming edges on one node can break rule matching for that
edge type. It was reproduced, and the affected path uses a distinct edge type to
avoid it. That is a workaround, not a fix.

---

## 4.7 What would falsify this

- **The ladder's ordering.** If minting first, or minting at rung 2, produces
  equal or better codebooks on a powered protocol, the Occam ordering is
  decoration. The tromino result is a single mechanism demonstration, not a
  benchmark.
- **Grain-agnosticism.** If a new grain requires a mechanism change rather than
  a representation choice — if some observation stream cannot be encoded so that
  its natural variations become per-dimension steps — §4.4's claim narrows to
  the grains it has been run on.
- **Termination.** If a residual can be constructed that mints repeatedly under
  the epoch gate, §4.3's termination argument is wrong. This is the most
  mechanical of the falsifiers and the most worth attempting.
- **The belief reframe.** If per-body decoding over one belief can be shown to
  lose information that per-body maps retain, §4.5's central claim fails.

One bound on the whole chapter: what is demonstrated is that the loop *runs* at
these grains and produces the growth described. What is **not** demonstrated is
that the resulting codebooks are competitive with purpose-built representations
at any of those grains. That is a benchmark question, chapter by chapter, and
chapter 5 is where it is asked most sharply — including where the answer was
uncomfortable.

---

*Ends. Next: chapter 5, where this loop meets a real benchmark, a powered gate,
and a correction that invalidated five of its own prior results.*
