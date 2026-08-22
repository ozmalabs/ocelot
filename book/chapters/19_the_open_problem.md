# 19 · The Open Problem

*Draft. Part VII closes here. Source:
`docs/research/theory_convergence/GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md` §4,
`runners/dsl/src/future_manifold.rs`, `runners/dsl/src/substrate.rs`.*

---

Two pieces of code exist in this substrate. Neither has ever called the other.

The first takes a candidate trajectory and audits it against a target: how much
width is retained, how much is lost, how much information goes, and the tick at
which the outcome becomes decisive. It is real, it is tested, and **every call
site passes it exactly one candidate.**

The second enumerates the moves a grammar admits from a given position, with
weights. Also real, also tested, and **every use of it is weighted selection
among admitted moves** — pick one and proceed.

An exhaustive sweep of the call sites found no site that composes them.

**That composition is the whole of this chapter, and it is small.** Run the
deformation audit over the admissible set rather than over one candidate, and
what comes back is a reachable-deformation set: the object chapters 17 and 18
are about.

---

## 19.1 What is currently not false

The precise status of Part VII's central claims is unusual and worth stating
exactly, because it is not the same as "unproven".

*An always-admissible but never-selected candidate contributes nothing.*
*Termination is visible when the deformation class admits it.* Reachability as a
measure over deformation. Narrativium. The horizon.

These are **not false in this substrate. They are not expressible.** There is no
reachable-deformation set for them to be true or false of, because nothing
constructs one. A claim whose subject does not exist in a system has no truth
value there, and calling it unverified overstates how far the work has got.

That distinction matters for how the preceding two chapters should be read.
Chapter 17's manifold and chapter 18's budget are not results awaiting stronger
evidence. They are definitions awaiting a referent.

---

## 19.2 Why it has not been done

Not difficulty. The audit takes a trajectory; the enumerator returns a set of
admitted moves; mapping one over the other is not a research problem.

What has been missing is a *reason inside a running system* — a caller that
needs a reachable set rather than a verdict on one candidate. Every consumer so
far wanted "is this trajectory acceptable" and got a correct answer. Nothing
wanted "what is reachable", so nothing built it.

Which is its own small finding, and it is chapter 3's shape one more time. The
algebra existed and the object it operates on did not. Here the object exists on
both sides and the *composition* is what nothing needed yet — a gap that is
invisible from inside either half, because each half works.

---

## 19.3 What it would make measurable

Composing the two turns most of Part VII from definitions into experiments.
Named in rough order of how directly each falls out:

**Reachability under a real grammar.** The first thing to look at is not a
number but a shape: whether the reachable-deformation set is *convex, holed, or
sparse* — because chapter 15's humanoid correction says a generated set with
holes cannot be repaired by better selection over it. A gate whose middle region
is empty is a delay line. The same question, asked of a manifold, is whether
what a frame can reach is continuous in the relevant sense or comes in
disconnected islands.

**Minimum intervention, tested rather than asserted.** Chapter 17's proposition —
that doing nothing is the baseline an action must beat — becomes checkable once
there is a reachable set to evaluate the no-intervention continuation inside.

**Narrativium, computed the way it is defined.** A measure over reachable
deformation, rather than the forbidden running sum chapter 18 catalogues.

**The horizon as an equality.** Available deformation against revision cost, on
a common dimension, in a system where both are instantiated.

**And chapter 9's regime selection, from the other end.** The Pareto result
there was measured empirically without any of this machinery; a reachable-set
formulation would say whether the frontier it found is the frontier the theory
predicts.

---

## 19.4 Free will, since this is where it arises

One question sits exactly at this composition, and Part VII is the right place
for it because it needs both halves.

An agent operating over a reachable set is choosing among futures that are, in
its frame, genuinely open — unresolved, multiple, and reachable. That is not an
illusion to be explained away; it is an accurate description of the frame's
situation. **And** those same futures may be structurally determinable from
sufficiently deep present-frame or containing-frame structure, which is chapter
14's determinism.

Both hold. The apparent conflict comes from expecting one frame's description to
be the whole account, and chapter 14's Axiom −1 already refuses that: there is
no view from nowhere, and a description indexed to a frame is not thereby wrong.

Note what this does *not* do. It does not resolve the free-will question by
picking a side, and it does not smuggle in randomness to make room for choice —
chapter 14 is explicit that apparent stochasticity is incomplete observation
rather than a property of the dynamics. It preserves the dichotomy: openness is
frame-real, determinability is structure-real, and they are statements about
different frames.

Whether that is a satisfying answer is not something this book can settle. What
it can say is that the position is forced by commitments made for unrelated
reasons, seventeen chapters earlier, rather than adopted because it was
comfortable.

---

## 19.5 The shape of the remaining work

Beyond the composition, three things are named and unbuilt, and they are named
rather than characterised because chapter 16 requires it.

**The rule-side reload fix**, which has to exist before rule structure can be
mirrored into the graph safely (chapter 3's measured no-go: unbounded growth per
checkpoint cycle, with the grammar-side fix already done and the rule-side one
not).

**The grammar refoundings** — the humanoid composer and the town's conduct
subsystem, both of which currently mint through zero productions (chapter 15).

**The thirty-eight remaining audit sites**, including the live identity-collision
bug that misroutes novel observations as duplicates.

None of those are Part VII's. They are listed here because this is the chapter
where the book stops claiming and starts pointing, and a list of pointers should
be complete.

---

## 19.6 What would falsify this chapter

- **The composition being harder than stated.** If joining the two halves turns
  out to require a third thing — a representation neither side carries — then
  §19.2's "not difficulty" is wrong, and the gap is a design problem rather than
  an absence of demand.
- **The set being uninteresting.** If the reachable-deformation set under a real
  grammar is trivially convex or trivially sparse, most of Part VII's structure
  is machinery for a case that does not arise.
- **The free-will position.** If openness in a frame can be shown to require
  ontological indeterminacy — that a frame cannot be genuinely choosing among
  determinable futures — then §19.4 is incoherent rather than merely
  unsatisfying.

---

*Ends. Part VII closes, and with it the argument. What follows is an epilogue
about where the work stopped, which is not the same as where it ended.*
