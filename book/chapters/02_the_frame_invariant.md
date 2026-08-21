# 2 · The Frame Invariant

*Draft. Short by design. Sources: `CLAUDE.md` § BASE-AS-DIMENSION,
`runners/dsl/DYADIC_DEPTH_DESIGN.md`, `runners/dsl/src/shape_decode.rs`.
Figures: FR-1, FR-2. Register per `BOOK_VOICE.md`.*

---

Chapter 1 left a question standing, and it was not rhetorical. If time is the
number of times a transformation was applied, and depth is what no single flat
transformation explains, then neither of them is *in* any of the frames the eye
saw. So where are they?

**The answer is the invariant this chapter states: within a frame, coordinates
are integers; every real-valued structure lives in the map between frames.**
Time and depth are not in the frames because they were never the kind of thing
that could be. They are properties of the *relations* between frames, and that
is not a limitation of how this eye happens to work — it is a claim about
where continuous quantities can coherently live in any grounded system.

The chapter is short because the claim is short. What earns it space is that it
is a *decision procedure* — for every number you are about to write, one
question with two answers — and a chapter that hands the reader a procedure
should not bury it.

---

## 2.1 The question, in its useful form

Here it is:

> **Is this value IN a frame, or BETWEEN frames?**

In-frame ⇒ it must be an integer. A float there is a category error.

Between-frames ⇒ it may be real. A float in a map, a metric, or a rendering is
exactly right.

That is the whole invariant. The rest of this chapter is why each half holds,
and what goes wrong when the question is not asked.

---

## 2.2 In-frame is integer, because sampling is what grounding is

The first half sounds like a restriction and is closer to a definition.

What is a grounded observation? It is what a sensor with a finite aperture,
finite sampling rate and finite dynamic range reported. Every one of those
finitudes is a quantisation. A pixel is a spatial bin. A tick is a temporal
bin. An intensity is a level. There is no operation you can perform on a
grounded observation that recovers a coordinate finer than the bin it arrived
in — not because the machinery is crude, but because the information was never
carried.

So the integer lattice is not a coarse approximation to a continuous truth that
better instruments would reveal. **Within a frame, it is the whole of what is
there.** Sampling is not something that happens *to* grounding; it is what
grounding is.

The engine enforces this, and the enforcement is worth looking at because it
reads as a bug and is not. The function that reads coordinates out of an
observed signature returns *nothing* when handed a floating-point slot. It does
not round, coerce, or approximate. It refuses.

Every instinct trained on ordinary numerical code says: fix that. Accept the
float, quantise it, carry on. But the refusal is load-bearing. A float in an
observed coordinate means one of two things has happened — either a cross-frame
quantity has been written into a frame, which is the error this chapter exists
to name, or precision is being claimed that no observation supports. The refusal
catches both, at the point where they are cheap to fix.

---

## 2.3 Non-integer structure is cross-frame

The second half is the one that does real work, because it says where all the
mathematics went.

Rotation by a real angle. A scale ratio. π. A Fourier transform between space
and spectrum. A logarithm between linear and log. A comparison metric between an
observation and a candidate. A rendering of a hypothesis into pixels. Every one
of these is real-valued, and not one of them is a property of an object. They
are all **maps** — from a frame to a frame [FR-1].

This is not a reclassification for tidiness. It changes what a system is
allowed to store, and what it must instead *apply*.

Consider a rotation. In-frame, an object occupies integer cells. Rotate it by
thirty degrees and the question "which cells does it occupy now?" has an answer
only after the rotation has been *applied and rendered* — and that answer is
again integer cells, because it is again a grounded frame. The thirty degrees
lives in the map. The before and after live in frames. There is nowhere in this
picture for a cell at coordinate 4.37, and asking for one is asking to store the
map inside the object.

Chapter 1's dimensional stack is this invariant, measured. Time is the exponent
of a transition generator — the generator is the map, the exponent is the
integer count of applications, and nothing continuous appears in either frame.
Depth is the ordering that reconciles two frames whose velocities disagree.
Stereo is the same reconciliation with the frames drawn from eyes rather than
ticks. None of it needed a continuous coordinate; all of it needed a map.

---

## 2.4 Continuity is intensional only

Here is the sharpest form of the claim, and the one most likely to be misread as
a denial of continuous mathematics. It is not. It is a statement about where
continuous mathematics can be *held*.

**A continuous quantity is a rule you apply, never a datum you observe.**

π is not a number this system can store; it is a procedure it can run, to
whatever depth the current question needs. A real-valued rotation angle is not a
measurement; it is a parameter of a map that will be applied and then rendered
back into a frame. A Cauchy sequence is a generator, not a value.

The distinction is between holding something *intensionally* — as a rule that
produces terms — and holding it *extensionally*, as the terms themselves. A
grounded system can hold the rule. It cannot hold the completed object, because
the completed object is not finite and observation is.

So: **you can apply π, but any given circle is stepped.** Both halves of that
sentence are load-bearing. The first says continuous structure is fully
available. The second says its observable is always a stepped rendering.

There is an identifiability guard attached, and it is the practical form of the
principle. A cross-frame map may carry a real parameter, but that parameter can
only be pinned to the resolution the observation supports. Fitting an angle to
six decimal places from a sheet whose cells are one unit wide is not precision;
it is encoding a number the steps cannot carry, which the description-length
criterion of chapter 1's coda rejects on its own terms — those extra digits cost
bits and buy nothing.

---

## 2.5 Two unbounded directions, and why one of them cannot reach the other

The invariant has a consequence that looks like a separate topic and is not
[FR-2].

A graph like this is unbounded in two directions at once.

**Outward — the extensive direction.** The frontier. There is always one more
step you have not taken, one more region you have not visited, one more thing
you have not observed. Unknown is *absence* here, and absence is first-class:
not a default zero, not a filled-in guess, but a representable fact that there
is something you do not have. Step outward as often as you like; you never
finish. This direction is countable.

**Inward — the intensive direction.** Refinement. Between any two things you
hold, there is room to look more closely: a finer grain, a subdivision, another
level of detail. Refine as often as you like; you never finish either. And the
*limit* of this direction — refinement carried to completion — is the continuum.

The two are orthogonal, and there is a specific thing you cannot do with them:
**you cannot reach the continuum by extending the frontier.** A countable union
of countable steps stays countable. No amount of stepping outward arrives at
uncountability. So the continuum is not somewhere far along the extensive
direction; it is on a different axis entirely, and that is a fact about
cardinality rather than a design choice.

Both are unbounded for the same reason — unknowability — and neither is ever
stored complete. What is held is the finite observed part, plus the fact that it
does not end. That second clause is a *representable fact*, not a gap in the
representation, and the distinction matters: a system that stored the observed
part alone would be a system that believed it had everything.

The epilogue collects on this. A substrate unbounded in two directions has no
completion condition, so any ending is a chosen cut.

---

## 2.6 A base is a dimension

The invariant pays for itself in a place that looks unrelated: what to do about
scales, cycles and logarithms.

The naive treatment makes these configuration. This frame is log-scaled; that
one wraps at twelve; this other one is linear. Each is a per-frame setting, set
by hand, and each new family of observations needs its own.

The invariant says otherwise. A base — a log scale, a doubling, a cyclic wrap —
is a *map between frames*. And a map between frames, in this substrate, is a
thing the system can hold, select and mint. So a base is not configuration. **A
base is a dimension**, and it can be discovered like any other.

Two of them are built. A multiplicative generator — values related by ×2^k — and
a modular generator, where a step wraps at n. Both sit in the same codebook of
dimension generators as rotation and reflection, and both are selected by the
same machinery that selects those.

The payoff is not elegance, it is compression. Under a multiplicative generator,
a ratio of two becomes the additive integer *k* that the transform rung already
reads for free. A whole family — every member of a scale sequence, every phase of
a cycle — collapses to one held shape plus one dimension, instead of a fresh
entry per member. The system grows *and* gets cheaper, which is not the usual
trade.

---

## 2.7 The refusal that shows the invariant has teeth

A principle that only ever licenses things is not doing much work. This one also
refuses, and the refusal is instructive because it cost a design and was written
down rather than quietly abandoned.

The candidate was refinement depth — the intensive direction of §2.5 — as a
dimension generator. It looks like an excellent fit. Depth is an integer. Going
one level finer is a step. Steps along a dimension are exactly what the transform
rung reads.

It does not work, for two reasons that only appear when you write the coordinate
map down.

**The count-preserving reading is an alias.** At depth *d*, a coordinate *x*
becomes 2*x* at depth *d+1* — each cell's origin becomes the corner of its
children. But `x → 2x` is byte-for-byte what the multiplicative generator of
§2.6 already computes. At the level of an observed signature, a depth step and a
scale step produce the *identical* transformed signature. They are
mathematically indistinguishable there, so adding depth as a generator would add
a second name for a map already held.

**The count-multiplying reading breaks a contract.** What "finer grain" actually
means is that one cell becomes 2^ndim filled children — the cell count
*multiplies*. Every other generator in the codebook preserves cell count: the
same cells, transformed. A generator that changes how many cells there are
violates the equal-count contract the candidate-construction machinery depends
on.

So the distinction the concept wants is real — *the shape grows in a fixed
lattice* is genuinely different from *the lattice gets finer under a fixed
shape* — but it does not live on the occupied-cell coordinates at all. It lives
in graph structure the signature does not currently carry: a depth attribute, and
edges relating a fine quantum to the coarse one it refines.

Which is a different home, and the design says so and stops: **design only, not
implemented**, with the stop condition named. Refinement depth belongs to the
spatial ladder as a first-class coarse-to-fine axis whose limit is the
continuum, co-designed with that ladder's own residual machinery — not bolted on
to a mechanism whose contract it breaks.

The invariant held throughout that analysis, and it is worth noticing how: at no
point did anyone propose a continuous coordinate. Refinement depth is a discrete
integer count. The refusal was about *which mechanism*, not about whether to
break the lattice.

---

## 2.8 Where the two halves meet: bins propose, continuous decides

The invariant is not a wall between the discrete and the continuous. It is a
division of labour, and chapter 5 will measure it.

The pattern, stated here and paid for there: **earned quanta are the proposal
layer; strong continuous geometry is the verdict layer.** The codebook proposes
candidates — cheaply, discretely, from what has been learned. The comparison
that decides between them is a cross-frame metric, continuous and correctly so,
because comparing an observation to a rendered candidate is exactly a map
between frames.

Bins propose. Continuous decides. Both halves are in their right place, and
chapter 5 reports what happened when the same representation was run against a
weak verdict and then a strong one: +51.5 percentage points, interval-separated,
with the *representation unchanged*.

---

## 2.9 What would falsify this

- **A grounded observable that is irreducibly non-integer.** Not a convenient
  float — a quantity that is genuinely observed, in a frame, and whose value
  cannot be expressed on any lattice without losing something the system
  demonstrably uses. That would break §2.2.
- **A continuous quantity that must be stored extensionally.** If some capability
  requires holding a completed real value rather than a rule that generates it
  to demanded precision, §2.4 is wrong.
- **The refusal being wrong.** If refinement depth *can* be expressed as a
  count-preserving coordinate remap that is not an alias of the multiplicative
  generator, §2.7's analysis fails — and, more usefully, the substrate gets a
  dimension it currently lacks.
- **The division of labour inverting.** If a discrete verdict beats a continuous
  one at equal proposal quality, on a powered protocol, §2.8 is backwards.

Two honest bounds on the chapter as it stands. The invariant is stated as
governing *this* substrate, and its generality beyond it is asserted rather than
demonstrated. And it is a rule that has been *followed* far more often than it
has been *tested* — the strongest evidence for it is a refusal (§2.7) and a
measurement made for another purpose (§2.8), which is thinner support than the
confidence of the preceding sections might suggest.

---

*Ends. Next: chapter 3, where the same question is asked about the substrate's
own rules — and the answer is that a system whose execution layer has no shape
cannot expand its own execution layer.*
