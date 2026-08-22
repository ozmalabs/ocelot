# 15 · A Number Where a Shape Belonged

*Draft. Sources: `docs/research/engine_substrate/SHAPE_AUDIT.md` and its sweeps;
`docs/research/flight_control/regime_pareto_frontier_prereg.md`;
`docs/research/humanoid/HUMANOID_DECOMPOSITION_CONTINUATION.md`;
`docs/research/bigville/BIGVILLE_ADMISSIBILITY_GRAMMAR.md`;
`CONSTANT_RANKING_SELECTOR_CENSUS.md`, `ARGMIN_TIE_CENSUS_RESULTS.md`.*

---

Start with a regress, because it is the cleanest instance and it happened in
this project rather than being invented as an illustration.

A learner needs a rate. The obvious one divides by the number of observations —
average everything you have seen. But that assumes the world is stationary, and
it is not, so the learner stops adapting. Declare a floor, then, so the rate
never falls below some value. But a flat floor is wasteful in quiet regimes
where nothing is changing. So make the floor respond to surprise. But surprise
has to be measured against something, so add a running average as the reference.
And the running average needs a rate.

**Each rate needs a rate.**

That loop does not terminate. Every step is locally reasonable, every step is
defensible in review, and the sequence returns to where it started with more
machinery than it began with.

**This chapter is about that failure mode, which was measured independently in
three unrelated parts of this project in a single week, and which has one
description: a number standing where a shape belonged.**

---

## 15.1 The two primitives, and the question

The substrate has exactly two generative primitives for the two things that keep
getting replaced by scalars.

**For a quantity that changes: the sd loop.** Decode against a held codebook,
measure the residual, mint when it recurs — chapter 4. This is how the substrate
represents something that varies, *including* an ordered ladder of viability
from reflex through held-ratio to search.

**For a set of allowed moves: the grammar.** A production generatively decides
what edge is *allowed to exist*, and admissible moves are returned as a set with
weights — chapter 14. This is how the substrate represents what a system may do:
as a generated set, not as a filter applied to one.

These two are the **native loop**, and they are what makes the audit in this
chapter possible at all. A census of scalars is only meaningful against
something they could have been instead.

Which is also the method that produced it. Force every subsystem through those
two primitives, and whatever resists is either a limitation of the framework —
fix the framework — or an inherited convention that nobody examined because it
is how the thing is done elsewhere. §15.4a is both at once, and separating them
is what made it actionable.

So the standing question, for every new subsystem:

> Before adding a rate, a threshold, a fixed weight, or a rule whose effects
> write graph state directly — **which of the two is this actually?** A quantity
> that changes, or a set of allowed moves?

And if it is genuinely neither, say so explicitly — because on the measured
record it has usually been one of them, and the number was standing in for a
shape nobody had looked for.

---

## 15.2 The measurement

The failure mode was not asserted. It was counted, and the counting is the
chapter.

**Sixty count-divided learners across eight embodied seeds** — the `1/n` pattern
of the opening regress, in the flight and body work. And the detail that turns a
census into a finding: **not one of them is inside the sd-loop, codebook,
spatial-quanta or conversation faculties.**

The faculties that match shapes never needed a number. The ones that match
numbers are where every defect of this class lives.

**159 of 634 rule-carrying seed files mint edges through zero grammar
productions.** A quarter of the substrate's rule-bearing content writes
structure without going through the mechanism that decides what structure may
exist.

**Forty confirmed sites**, from about 150 examined.

And the number a reader should weight most: **two of the sweep's own reported
findings were checked, found wrong, and kept in the record.** That is the
method's error rate, disclosed by the method. Every other figure in this chapter
should be read with it attached.

---

## 15.3 The three independent occurrences

The same defect, in three embodiments, found by three separate lines of work
that were not looking for each other.

**The jet.** The rate regress of the opening, plus the finding that the motor
system's slope-collapse behaviour was hand-written as a bespoke rule when it is
rung 2 of the ladder that already exists — a residual read as one uniform step
along a held dimension. Chapter 9 carries this. Its summary sentence is the
chapter's title in another form: *everything the loop gives for free — recognise,
transform, infer, mint — the motor path reimplements or does without.*

**The humanoid.** A composer that sums nine cost terms unconditionally and
minimises greedily. The deciding path has **no grammar productions at all**, and
rule effects write edges *directly*, bypassing the admissibility check entirely
— the flag that would gate them is reserved and unbuilt.

The document that records this states the premise being violated better than a
summary can: *the entire point of admissibility grammar is that we don't have to
choose a single fixpoint.* A composer that sums and minimises has chosen one,
before anything downstream gets a say.

It also carries the correction that stops the obvious fix from being wrong:
**set-valued selection alone does not repair this** if the generated response set
has holes. A gate whose middle region is empty is a delay line — it does not
smoothly modulate, it waits and then jumps. So the repair is in what the grammar
can *generate*, not in replacing the selector that reads it.

**The town.** Chapter 13: violence as fifteen rules across four seeds, all four
declaring zero productions. A richly modelled behaviour built as a bespoke
subsystem per transgression, where the substrate's own shape says it should be a
generated absence — conduct admissible by default, inadmissibility as the rare
marked residual.

Three domains. Three teams-of-one. One defect.

---

## 15.4 The recogniser that scored by counting words

The most self-referential instance deserves its own section.

The function whose entire job is detecting *shape* — the agent's meta-shape
recogniser, which decides what kind of thing a new piece of knowledge is —
scored candidates by counting raw substring occurrences over attribute keys it
had already discarded, and broke ties **alphabetically by the shape's own name**.

Chapter 3 gives the measurement: 44 of 55 pairs tie, and the alphabet decided all
44.

That is the defect in its purest form. Not a rate, not a threshold — a *string
count* standing where a structural comparison belonged, inside the faculty whose
subject matter is structural comparison.

---

## 15.4a The clearest instance: a label where a boundary belonged

The audit above finds scalars standing in for the two primitives. This section
is the case where one was found by accident, and where the shaped alternative
was then built and measured — which makes it the only fully-closed instance in
the chapter.

A field of cells has to be grouped into regions. The mechanism is a **flood**: a
rule spreads a label outward, each cell taking the smallest label among its
similar neighbours, until a region has one identity.

**Membership is therefore equality of a number.** A cell belongs to a region
because its label matches. Which has two consequences nobody wrote down: reading
membership means scanning every cell in the field, and *establishing* it means
diffusing a value outward one hop at a time.

The reason this went unexamined is the reason chapter 14 gives. The substrate's
effect vocabulary is thirteen operations, and **every one of them is a local
write.** There is no merge, no union — no way for a rule to say *these two
regions are now one*. A component is a global object, so with local writes only,
its identity can only be replicated into every member and diffused. The flood is
not a bad choice within that vocabulary. It is what that vocabulary leaves.

**The shaped alternative** keeps the boundary as structure instead of the
interior as a value: mark which neighbour relations *disagree*, chain the cells
along that edge, and read membership as the components remaining once those cuts
are removed. Three rules, no new engine primitives, no new constants.

Measured against the flood:

- **Same partition**, bit-identical, on synthetic strips and on a real 18×18
  field — 13 regions, identical sets. This is a representation change, not a
  different grouping, and the gate asserts it.
- **Cost stops tracking size.** Three sweeps at 8 cells, at 32, at 64, at 128.
- **And cost stops depending on the derivation mode**, which is the property
  that matters and the one that was invisible until something broke.

The last point deserves the space. The change that exposed all this was
unrelated — an experiment called Stage A, deriving proposals against a frozen
base so that rules could not see each other's writes mid-round. It **failed**,
and it failed here:
the flood degraded to one hop per pass and a motion object 108 cells across
collapsed to 3. Which revealed that **the flood's speed had rested entirely on
same-round visibility** — later cells reading labels earlier cells had just
written. Nothing had ever stated that dependency. The boundary representation is
indifferent to it, because it never reads what a sibling wrote.

Two honest limits, both from the source document, which retracted two of its own
claims while establishing this. **Boundary tracing does not fix chaining** — a
threshold on a pairwise difference is not transitive, so any method that groups
by "adjacent and similar" chains identically, and that was measured rather than
assumed. Chaining is a property of the relation, not of the algorithm closing
it. And **nothing has replaced the flood**: the boundary is derived alongside the
label field, no rule was removed, and the contour is built but not yet ordered,
quantised, or decoded — which is the entire reason a contour beats a label, and
it is designed and unbuilt.

## 15.5 The live bug, stated plainly

One confirmed site is not a design debt but a defect that corrupts silently, and
it belongs in the body of the chapter rather than a list.

A capability axis's identity is a **truncated, order-dependent string join**.

Two consequences follow. Truncation means two genuinely different axes can
collide. Order-dependence means the same axis can be built twice under different
identities. And the direction of the failure is the dangerous one: a novel
observation can be **misrouted as a duplicate of something already held** — a
growth failure that presents as successful recognition.

Which is the shape chapter 3 named at a different grain. A recogniser that
always answers cannot produce a residual. An identity that collides cannot
either: the system does not fail to recognise, it recognises *wrongly*, and
nothing downstream can tell.

It is unfixed.

---

## 15.6 Why the number is not a simplification

The defence of a scalar knob is always the same: it is simpler, and the
generative version is over-engineering for a case that may never arrive.

Two things are wrong with that on this record.

**A scalar knob is not a simplification of a shape — it is unpaid debt.** The
opening regress is what repayment looks like when deferred: each ad hoc rate
eventually needs its own rate, and the total machinery exceeds what the
generative version would have cost, distributed across enough commits that
nobody sees the total.

**The measured distribution says which side is which.** Sixty count-divided
learners, none in the shape-matching faculties. If scalars were a reasonable
local simplification you would expect them everywhere, including in the parts
that work best. They are not there. The faculties built on the two primitives
did not need them.

---

## 15.7 Stated is not enforced

The honest status, which this chapter must carry because it is otherwise a list
of other people's mistakes written by the same person.

**The rule is stated. It is not enforced anywhere.** The ladder exists and is
live in the jet's own code. The humanoid's grammar refounding and the town's
admissibility refactor are **named, not built.** Thirty-eight of the forty
confirmed sites are unfixed, including §15.5's corruption bug.

So this chapter is a standing design rule for new work plus an enumerated list
of where existing work does not comply. It is not a claim that the substrate has
been repaired. The distinction matters because the enumerated form is the one
that can be checked — chapter 16's rule again: a baseline is a list, never a
count or a characterisation, and "we have mostly fixed this" would be exactly
the characterisation that lets the number grow underneath it.

---

## 15.8 What would falsify this

- **The census.** Sixty learners, 159 of 634 seeds, 40 of 150 sites — all
  countable, all re-runnable. A recount differing materially would falsify the
  measurement, and the two known-wrong findings say the method has a nonzero
  error rate already.
- **The dichotomy.** The claim is that a scalar usually stands in for one of two
  primitives. A clear case that is genuinely neither — and where the generative
  forms would be worse — would bound the rule to where it applies, which would be
  an improvement on stating it universally.
- **The distribution finding.** If a count-divided learner is found inside a
  shape-matching faculty, doing necessary work, §15.6's argument weakens
  considerably. That is a single grep away from being tested.
- **The delay-line correction.** If set-valued selection over the *existing*
  generated set does repair the humanoid composer, then the diagnosis is wrong
  about where the hole is — and the cheaper fix works.

---

*Ends. Next: chapter 16, which is how anything in this book came to be
believable enough to be worth auditing.*
