# 5 · One-Shot Characters

*Draft. Sources: `CLAUDE.md` § The Omniglot arc, § RUN 15 CORRECTION, § RUN 16
RECONCILIATION; the run logs under `results/`. Register per `BOOK_VOICE.md` —
and this is the chapter where its rule about intervals is not advice.*

---

Show a person one handwritten character from an alphabet they have never seen.
Show them twenty candidates, one of which is another example of that same
character written by someone else. They will pick it out.

Machines find this hard for a specific reason: there is one example. Not one
thousand, not one hundred. One.

**This chapter is about a system that learns to do that with a growing
codebook of stroke shapes — and about the run that discovered every improvement
reported in the preceding fifteen runs, except one, was noise.**

Both halves matter. The capability is real and the arc that built it was
substantially wrong about itself, and the correction is the more valuable of
the two results.

---

## 5.1 Composition: the effect that survived

Start with what holds, because everything else in this chapter is a subtraction
from it.

A character decomposes into strokes. The obvious representation is the set of
strokes it contains — a bag of parts, matched against the bags of other
characters. The alternative treats the *arrangement* as first-class: not which
strokes, but where each sits relative to the others, as relations in the same
codebook the strokes live in.

Arrangement wins by **twenty-one percentage points**, interval-separated. It is
the largest effect in the arc and the only one that survived the correction
below.

There is an empirical fact underneath it that explains why. Real strokes, once
quantised, occupy only about **five to seven classes**. That is a very small
alphabet — far too small to identify a character by its parts, because most
characters share most of their parts. So identity cannot be in the inventory.
**Identity lives in the arrangement**, and the measurement says how much: the
twenty-one points is the difference between those two claims about where
information is.

That is the sd loop of chapter 4 applied one level up. Strokes are quanta; a
character is a composition of quanta plus relations; and the same decode that
covers a stroke covers a character made of them.

---

## 5.2 What fifteen runs reported

The arc ran for fifteen runs, each measuring a change against the last, and
each reporting a delta. In order: 2.5% one-shot accuracy at twenty-way, then
3.8%, then **33.8%** when composition landed — the jump of §5.1. Then a series
of refinements, each measured, each reported:

- A finer base grain: **26.2%**, *worse*. Recorded as a loss, with a stated
  reason — finer grain fragments the parts, and detail belongs in refinement
  rather than in the base representation.
- Partial-credit metrics and higher-order relations: 30.0%, three times over.
  Also losses, with the lesson drawn that strictness was carrying signal that
  a softer metric discarded.
- **Analysis-by-synthesis: 37.5%**, the arc's high-water mark and its most
  satisfying result architecturally — of which more in §5.4.

Every one of those numbers is reproducible. The machinery is deterministic. Run
the controls again and you get them again.

---

## 5.3 The run that corrected the arc

Then somebody powered the gate.

The evaluation had been running on four alphabets. Run 15 moved to ten, with
n = 400 and intervals computed rather than eyeballed. Two things came back.

**The four-alphabet evaluation had been an easy subset.** The honest ceiling at
power is **26.8% [22.6, 31.3]** — not 37.5%.

**Every post-composition delta in the arc was noise.** Analysis-by-synthesis
+3.7, dwell scheduling +1.3, appearance +2.5, higher-order relations −3.8,
sub-strokes −1.2. At power, **all arms sit inside each other's intervals**. Each
of those deltas was one to three episodes of difference on a small evaluation
set — the granularity of the measurement, reported as signal.

And the detail that settles it: the higher-order-relations change had been
recorded as a *loser*, at −3.8. At power it is numerically **on top**. The arc
had not merely overstated its improvements; it had ranked them wrongly enough
that a change it discarded was as good as the ones it kept.

What survives, interval-separated: composition's twenty-one points; a proposal
coverage figure of about 54% at five candidates; a roughly 5% tail the proposal
stage never reaches at all; the saturation facts; and the exact
control-reproduction chain — because *the machinery was never wrong*. Every
number reproduced. **The evaluation set was the error.**

Both open forks — sub-strokes, junction blending — came back null under power
too, which is its own finding: the representation-grain corridor was exhausted,
and the next lever would have to be a different kind of feature rather than a
finer version of the same one.

Three standing rules were minted here, and they govern the rest of this book:

1. **Power the gate before the endgame.** Deltas within about three times the
   per-episode step are not results.
2. **A synthetically-proven mechanism is not a benchmark value.** Report both.
3. **Eval-subset coverage is part of every claim.** A number without the set it
   was measured on is incomplete in the same way a number without its condition
   is (chapter 16).

Five reported improvements and a headline figure, deleted by one measurement
that nobody outside this project would have required.

---

## 5.4 Analysis-by-synthesis, which was right for a different reason

Run 15 removed the +3.7 that analysis-by-synthesis had been credited with. It
did not remove the architecture, and the architecture matters more than the
delta did.

The stroke quantiser turns a pen path into indices. Its **exact inverse** was
built: a renderer that turns indices back into a pen path, with the round trip
proven rather than asserted. Which makes reading and writing one model — a
character is recognised by *proposing* a quantised index, rendering it, and
comparing the rendering to the observation.

The reason this is architecturally right, independent of its measured delta, is
what it did to a standing problem. The system had a frame-instability residual —
error that came from the observation and the candidate not being in a common
frame. Analysis-by-synthesis **dissolved** it rather than patching it: render
the candidate into the observation's frame and the mismatch has nowhere left to
live. A residual that disappears because the representation changed is a better
outcome than a residual with a correction term bolted on, and chapter 2 says why:
the comparison is a map between frames, and doing it as one is what a rendering
*is*.

That is a mechanism result. Run 15 established it was not, on this benchmark, a
performance result. Both are reported, which is rule 2 above.

---

## 5.5 The reconciliation: it was the verdict, not the representation

Run 15 looked like a terminus. It was a comparator artefact, and run 16 found it.

An earlier line of work in this project — unrelated, months before, on the same
task — had reached roughly 81%, training-free, using strong continuous geometry
to compare shapes: fused shape-context and thin-plate-spline matching on raw
points, with parse marginalisation, under a matched protocol.

So there were two numbers: ~81% from the earlier line and 26.8% at power from
this one. The temptation is to decide which was wrong.

**Both were right.** The difference was not the representation, the codebook, or
the composition. It was the **verdict comparator** — what decides which
candidate matches.

Transplanting the strong comparator onto the powered protocol, with everything
else unchanged: **73.5% [67.0, 79.1]**. An improvement of **51.5 percentage
points**, interval-separated.

And it is *cheaper*. About 2.3 milliseconds per comparison — less than the weak
render-and-compare path it replaced. This was not a quality-for-cost trade.

Which yields the synthesis this book has already used twice:

> **Earned quanta are the proposal layer. Strong continuous geometry is the
> verdict layer. Bins propose; continuous decides.**

Chapter 2 stated that as an invariant. This is the measurement: the discrete,
learned codebook does what it is good at — generating a small set of plausible
candidates from what has been seen — and a continuous cross-frame comparison
does what *it* is good at, which is deciding between them.

One earlier conclusion inverted along the way. Run 11 had found that widening
the candidate set hurt. Under a strong verdict it helps: full dwell beats the
shortlist by 25.5 points. A weak comparator is confused by more candidates; a
strong one is not. So proposal recall — that ~54% at five — becomes a real lever
again, having looked like a closed question.

One figure is explicitly *not* claimed. A neighbouring result of about 83% is
discounted here: ten-way rather than twenty, n ≤ 40, and a borrowed pretrained
network doing the deciding. Under this book's rules it is not comparable, and it
is mentioned only so a reader who finds it knows why it is absent.

---

## 5.6 Three facts the arc established that are not accuracy numbers

**Real writers are style families, not one slant.** The natural model of a
writer's hand — a consistent transformation applied to everything they write —
is wrong on real data. A hand is a distribution over transformations, and
treating it as a point breaks in a way that no amount of parameter fitting
repairs.

**Strictness is signal.** Three separate attempts to soften the matching
criterion — partial credit, tolerant metrics, richer relations — lost. Something
that looks like a generous scoring rule is, on this task, discarding the
information that discriminates.

**Check every read-back.** A binding-layer call returns tuples where the code
tested for lists. The type check silently disabled part of the codebook growth
path. No error, no test failure, just a mechanism that quietly stopped
happening — chapter 16's inert instruments, in a different disguise.

---

## 5.7 What would falsify this

- **Composition.** The one surviving effect. If a properly powered evaluation
  shows arrangement and inventory within each other's intervals, §5.1 goes and
  the chapter has nothing left.
- **The comparator synthesis.** If a discrete verdict at equal proposal quality
  matches the continuous one on the powered protocol, "bins propose, continuous
  decides" is not a division of labour but an implementation detail.
- **The proposal ceiling.** The ~5% proposal-blind tail is a claim that some
  characters are never proposed at all. A proposal stage reaching them without
  loss of precision would falsify the ceiling's location.
- **The correction itself.** If the ten-alphabet evaluation is *also*
  unrepresentative — in a different direction — then run 15 corrected one
  sampling error with another. Nothing about the correction protects it from
  being an instance of the same failure.

That last one is not rhetorical. The lesson of this chapter is not that the new
number is the true one. It is that a number is only ever as good as the coverage
of the set it was measured on, and that this arc has been wrong about exactly
that once already.

---

*Ends. Next: chapter 6, where the same loop meets an input stream that arrives
whether or not the system is ready — and where the learning order was not
imposed.*
