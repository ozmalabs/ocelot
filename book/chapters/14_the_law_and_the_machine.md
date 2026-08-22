# 14 · The Law, and One Machine That Obeys It

*Draft. Part V. The formal statements are Paper 01 (theory) and Paper 05
(construction); this chapter is those papers by subtraction, placed here rather
than first. Figures: PAPER-01-1, PAPER-01-2, PAPER-05-1.*

---

Thirteen chapters ago this book started with an eye. Since then: characters,
speech, space, programs, six bodies, emotion, two failure regimes, a coupling
between two people, a town.

**This chapter is the smallest statement of what all of that was an instance
of.** It is placed here, near the end, rather than at the beginning — because a
reader who has watched fourteen capabilities grow from one loop meets a
formalism as *compression*, and that is the only way axioms are ever pleasant to
read.

Nothing in this chapter is new. Everything in it has already been used.

---

## 14.1 Where the theory starts, and where it declines to

Before the standpoint, a boundary — because the theory is routinely read as
claiming more than it does.

**This theory does not attempt to specify the intrinsic nature of
pre-relational existence.** It begins at the first level at which distinguishable
relational structure is representable, and says nothing about what is underneath
that. The pre-graph substrate may be continuous, discrete, purely mathematical,
or unclassifiable from any frame available to us. The move being made is:

> **? ⇢ observable relational structure ⇒ graph representation.**

The dashed arrow is the part not claimed. What follows the second arrow is the
theory; what precedes the first is outside it.

This matters because "everything is a graph" is available as a reading and is
not the claim. The claim is that *where there is distinguishable relational
structure, that structure is representable as a graph, and the dynamics below
govern it.* A reader who takes the stronger version will find the theory
overreaching, correctly, about something it did not say.

## 14.2 The standpoint

One commitment comes before the graph, and it is the kind that is easy to agree
with and then quietly violate.

**There is no operational view from nowhere.** Every distinction, every
measurement, every identity relation, every judgement of what is allowed, is
made *in some frame*. Frames can represent one another, compare one another,
predict one another. But no quantity this theory uses requires an evaluator
standing outside all frames.

That is not scepticism and it does not remove determinacy. Within a frame,
relations can be exact, restrictive, comparable and falsifiable — and the whole
of this book has been such relations. What it removes is the privileged
observer, and the removal has a cost that is paid throughout: every quantity has
to be indexed to the frame that holds it.

Chapter 2 was this commitment made operational. *Is this value in a frame or
between frames* is the same question as *whose frame is this quantity indexed
to*, asked in a form you can check.

The standpoint has company in physics — the relational readings of quantum
mechanics make the same architectural move, and the theory acknowledges the
resonance without deriving anything from it.

---

## 14.3 The graph

A graph is three things:

> **G = (g, r, Γ)**
>
> **g**, represented state. **r**, operative transformation structure. **Γ**,
> the admissibility grammar governing what the graph may do to itself.

That is all of it. No parent pointer, no world model, no catalogue of
affordances, no goals, no values, no self-model. Those may exist *in* g when the
graph actually represents them, as ordinary content — and in this book they
usually do — but none is a primitive of being a graph.

The claim being made by that austerity is a specific one: **anything required
only by a particular capability is content or grounding, not structure.** A
graph that cannot see is still a graph. So is one with no goals. What it cannot
lack is participation in the transition relation below.

---

## 14.4 The one move

Everything happens by one operation, applied repeatedly [PAPER-01-1]:

> **G_t → 𝒫(G_t) → 𝒞_t → G_{t+1}**

Present structure determines **admissible possibility** — the set of
continuations Γ allows. **Collapse** realises exactly one of them. The realised
successor becomes the antecedent of the next step, and the loop closes.

Three things follow, and each has appeared already in this book.

**What may happen and what does happen are different questions.** Chess in the
prologue hands this over free: the legal-move relation is one thing, the move
played is another. The admissible set can be large and the realised successor is
always one. Candidates that are admissible but not realised contribute nothing —
that is what collapse *means*, and it is why the figure draws them terminating
rather than arriving.

**Antecedent state is distinct from consequences of the current transition.**
The graph the rules read is the graph as it was, not as it is becoming. Chapter
4's fixpoint is this; §14.6 is how an implementation is forced to make it true.

**Time is not a primitive of any of this.** Nothing above requires a temporal
dimension to be instantiated. Existence does not require time; what produces a
time dimension is *persistent directed succession* — a ratchet of
distinguishable change, which the transition relation above is. Informally:
something exists; something changes in a persistent directed way; a ratchet
exists; therefore a time dimension becomes meaningful. Chapter 1's eye minted
exactly that axis from exactly that condition, which is why it could mint it at
all — and why shuffled frames minted nothing.

**Residual is what the realised successor did not absorb.** Not an error, not a
diagnosis — a *mismatch*, and one that need contain no explanation of itself.
Chapter 3 argued that residual is the only admissible channel for growth;
chapter 4 built the loop that grows on it; chapter 10 found it inside a person
as the locus of attribution. Here it is simply a primitive of the dynamics, and
the reason it can carry all that weight later is that it is defined so early and
so thinly.

---

## 14.5 Boundaries, and what admissibility is not

A graph that is *situated* meets its containing frame through a boundary
[PAPER-01-2]. And the proposition that boundary exists to state is the one most
easily misread from a distance:

> **Admissibility is self-governance, not armour.**

Γ constrains what the graph may do to *itself*. It gives the graph no veto over
what the world does *to* it. Three legs, distinct:

- self-originated transformation, which Γ governs;
- outward influence, which the graph exerts;
- inbound world forcing, which arrives whether or not Γ would have permitted it.

Collapsing those three is how a safety story becomes wrong. A grammar that
restricts what a system may do is not a shield against what may be done to it,
and reading it as one produces confidence in exactly the wrong place.

Two consequences worth naming. **Identity is frame-typed**: whether this is
still the same graph is a question asked *in* a frame, not answered absolutely.
And **termination is frame-relative** — where a containing frame no longer admits
an identity-preserving continuation, that situated identity ends. It does not
become malformed. It stops being admitted, which is a fact about the frame.

A represented self, meanwhile, is ordinary content in g. It can be copied. The
theory declines to make selfhood special, and the epilogue collects on that.

---

## 14.6 Determinism, and where the randomness went

The law is deterministic. Systems that obey it look stochastic all the time.

Both are true, and the reconciliation is the whole content: **apparent
stochasticity belongs to incomplete observation, not to the transition
relation.** An observer who does not represent every determining dimension sees
a distribution. That distribution is a fact about the observer's frame — real,
usable, statistically well-behaved — and not a fact about the dynamics.

This is why chapter 12's ensemble statistic is described there as measuring an
observer's population-level evidence rather than adding noise to a mechanism,
and why chapter 7's surprise curve is a property of a model rather than of a
world.

Two distinctions keep the determinism from being overclaimed, and both are about
words that are easy to use loosely.

**Determinable is not determined.** A continuation may be entirely determinable
from present structure and *not yet realised*. "Determined" belongs to what has
collapsed into realised history; everything ahead of the collapse boundary is at
most determinable. The future is not an extant region lying to the right of now,
waiting to be reached — it is the set of continuations represented, now, as
reachable.

**And what does the determining is present structure, not a past.** The
condition is *causally sufficient present structure*, including whatever
containing-frame relations are relevant: identical causally sufficient present
structure implies identical realised continuation. Past states are not required
to remain extant for this to hold, because **history matters only where it
survives as present structure**. That is not a weakening. It is what makes the
claim checkable — a stack of still-existing historical frames is not something
any frame has access to, and a theory that required one would be unusable.

---

## 14.7 One machine that obeys it

A theory of this shape can be satisfied by many executors. Paper 05 builds one,
and the value of having built it is not the executor — it is the list of
distinctions that only became visible when something had to actually run
[PAPER-05-1].

**A round.** Every rule in a round reads the same immutable antecedent base and
writes into a fresh effect set. **Same-round writes are not visible.** That
barrier is the antecedent-state principle of §14.3, made mechanical: without it,
rule order silently becomes semantics.

**Merge.** After the round, effects merge deterministically where compatible,
and incompatibility is *explicit* rather than resolved by precedence.

**Closure.** Iterate to least fixed point. Under stated conditions — monotone
positive derivation, base-stable or monotone-sensitive admissibility,
deterministic merge on compatible effects, properly stratified invention of
fresh names — the result is **independent of the order the rules were
enumerated in**. That independence is the property that makes a rule set a
specification rather than a program.

**Removal is stratified**, because deletion and freshness interact in ways that
addition does not.

**Weighting is relative.** Comparisons are invariant under a common offset — a
gauge condition — and no numeric weight is assigned to candidates outside the
comparison domain. Chapter 15 is about what happens when that discipline lapses.

**Input is separated into three things**: direct data, residual, and represented
precision or freshness. World-caused integration is not checked against
self-admissibility, per §14.5 — the graph does not get to refuse what happened.

The paper also states its own conformance tests: enumeration-order invariance,
same-round non-readability, monotone frontier growth, stratification,
deterministic merge, boundary publication, absence of accidental cross-boundary
atomicity, stable tie behaviour, gauge invariance, provenance-preserving
residual, frame-local termination, absence of hidden executor stochasticity, and
reproducibility of realised successors from identical antecedents.

That list is the useful part of having built the machine. It is what "obeys the
law" means operationally, and it is checkable.

---

## 14.8 What implementation taught the theory

The distinctions the construction forced, which survive replacement of this
particular executor. Several have already done work in this book:

- antecedent state is distinct from the consequences of the current transition;
- self-admissibility cannot function as armour against world-caused change;
- outward action and inbound observation are different causal legs;
- identity must be frame-typed;
- a failed interaction requires no persistent attempt object;
- residual is mismatch and need not contain explanation;
- previous failure changes later dynamics only if its consequences survive in
  state — which is chapter 12's traumatic-bond mechanism stated abstractly, and
  Part VII's narrative momentum stated early. Momentum, on this reading, is not
  history carried forward through time: it is a *currently instantiated*
  structural consequence of prior change, constraining what can happen next.
  Ordinary momentum and narrative momentum then have the same form rather than
  one being a metaphor borrowed from the other;
- distinct boundaries cannot be silently treated as one atomic transaction;
- higher-frame quantities may be first-class without being primitives of the
  lower graph;
- **absent dimensions must not be represented by zero or an extreme sentinel** —
  chapter 7's whole design, arrived at here from a different direction;
- apparent stochasticity belongs to incomplete observation.

A theory that gained eleven distinctions by being built is a theory that was
underspecified in eleven places, and saying so is more useful than the eleven.

---

## 14.9 What would falsify this

The papers state their own commitments; these are the ones this book has
exposed most.

- **Minimal graph sufficiency.** If some capability demonstrated in Parts I–IV
  turns out to require a primitive not in (g, r, Γ) — something that cannot be
  content — the austerity claim of §14.3 fails.
- **Order-independence.** Its conditions are stated. A rule set meeting them
  whose fixpoint depends on enumeration order would falsify the closure theorem
  as applied here, and is mechanically testable.
- **The three legs.** If self-governance can be shown to function as armour in
  some configuration — Γ actually vetoing world-caused change — §14.5 is wrong
  in the direction that matters most.
- **Determinism.** If a realised successor differs across runs from an identical,
  causally complete antecedent configuration, there is hidden stochasticity in
  the executor, and one of the conformance tests exists to catch exactly that.
- **The standpoint.** Axiom −1 is not empirically falsifiable in the ordinary
  sense; it is the frame the rest is written in. What *can* fail is its
  operational form — chapter 2's decision procedure — and that has been tested
  more thinly than the confidence of this chapter suggests.

---

*Ends. Next: chapter 15, which is what happens where this law is not followed —
counted, rather than characterised.*
