# 7 · Space as a Belief

*Draft. Sources: `docs/features/ls20-spatial.md`; `docs/research/ls20/`;
`runners/dsl/src/space_quantize.rs`; `seeds/quanta_navigation.json`;
`tests/test_quanta_navigation_migrated.py`. Register per `BOOK_VOICE.md`.*

---

Give a navigation system a map with a hole in it and something has to fill the
hole. Usually it is a zero. Sometimes an optimistic default, sometimes a
pessimistic one, occasionally a probability — but something, because the data
structure has a slot and the slot must contain a value.

**This chapter is about not filling it.**

The map here is a *belief*, and in a belief, **unknown is a state in its own
right** — distinct from empty and distinct from occupied. The agent does not
hold a grid with unknowns filled in; it holds what it has observed, plus the
fact that this is not everything.

The theory's own vocabulary makes a three-way distinction here, and it is worth
having before the chapter uses it:

> **NULL ≠ unknown ≠ resolved.** *NULL* is a dimension that is absent — not
> instantiated at all. *Unknown* is a dimension that exists but whose value is
> unresolved. *Resolved* is a realised value.

An unvisited cell is **unknown**, not NULL: the spatial dimensions are
instantiated, and what is missing is the value. The distinction matters because
the two behave differently under projection — an unresolved value is something
the agent can go and resolve, and a NULL dimension is not something it can look
for.

That sounds like a representational nicety. It is the load-bearing decision in
the chapter, and everything else — routing per body, decoding only where you are
looking, refining resolution per dimension — follows from it.

*(A naming note, because it trips people up: the benchmark family this thread
works in is ARC-AGI, the spatial-reasoning benchmark. This project separately
uses "ARC" as its own internal phase label for the program-synthesis work of
chapter 8. Unrelated.)*

---

## 7.1 Winning is a side effect

The framing the record states directly: **winning is a side effect of
understanding — the true victory is knowledge.**

That is easy to say and normally unfalsifiable, so it was measured. In a world
where stations apply transformations the agent has to work out, two quantities
were tracked as the agent explored: its *surprise* — prediction minus
observation — and the accuracy of its model of which station does what.

Surprise falls from 1.0 to 0.0. Model accuracy rises from near zero to 1.0. And
they move **in lockstep**, with surprise reaching zero exactly at the cycle
where every station has been modelled.

That is what a curiosity-driven world model converging on ground truth looks
like, and it is distinguishable from a policy that has learned to win. A policy
that wins can have any internal state at all. This one's internal state tracks
the world, and the surprise curve is the evidence — because surprise going to
zero *while accuracy is still low* would have been the signature of a system
that had stopped being surprised for the wrong reason.

---

## 7.2 The map is a belief

The reframe, stated as it applies.

**Unknown is a state, not a default value.** When a world hands over its entire
map at load time, that is the *degenerate* case — the case where the belief
happens to be complete — rather than the normal one the representation was
designed around. Most worlds are not like that, and a representation that
assumes they are has to be retrofitted for the ones that are not.

**Absence is representable.** Chapter 2's second unbounded axis appears here in
its most practical form: what the agent holds is the finite observed part *plus
the fact that it does not end*. That second clause is what makes exploration
well-defined — a frontier is the boundary between what is held and what is known
to be missing, and you cannot compute a frontier over a structure that has
already filled its own gaps with zeros.

---

## 7.3 Quanta, and four consequences

Space is decoded into **quanta** — regions — from that belief, by the same loop
chapter 4 describes. The flood does not run per cell; it runs at quanta. Four
consequences follow, each of which is a property the cell-based representation
could not express.

**Decoding is per body.** Quanta are decoded *for the body doing the routing*,
by eroding the belief by that body's shape. A one-by-one agent and a two-by-two
agent route differently over **one underlying belief**, because the erosion
differs. This is the classic configuration-space move, but the direction matters:
the belief is shared and the decoding is per body, rather than each body
maintaining its own map. One observation, many decodings.

**Decoding is foveated.** It happens where the agent is looking, reusing prior
decode work incrementally rather than re-flooding the whole map on every change.
Which is chapter 1's foveation, at a different grain and for the same reason —
the cost of attending everywhere is not affordable and mostly not needed.

**Resolution is per dimension.** A remainder that does not fit a quantum routes
to a finer split *in the dimension that needs it*, not uniformly across all of
them. Quanta are dynamic per dimension. A corridor long in one axis and narrow
in another does not have to be represented at the fine resolution of its narrow
axis everywhere.

**Lifecycle is rules.** Staleness, retirement, multi-source frontier-seeking
exploration, the epoch-gated flood over portals — all of it is graph rules in
the same fixpoint as everything else, not a control loop calling into the
substrate.

---

## 7.4 The comparison that makes it a claim

A new representation that is better on its own examples is a demonstration. What
makes this a claim is that the old one is still there.

Cell-based navigation remains available, and it is **byte-identical to its
pre-change baseline**. Adapters opt into the quanta representation explicitly.
So the comparison is between two live implementations rather than between a new
system and a remembered one — and any regression in the old path would show up
as a difference from a baseline that is checked rather than recalled.

That property is chapter 16's baseline rule applied to an implementation: the
old behaviour is pinned as an artefact, not characterised in prose.

The gates cover partial-map memory, three dimensions, two body shapes, a
per-dimension split, and foveation.

---

## 7.5 The residuals, as recorded

The commit that landed this work recorded what it did not do, and those items
belong here rather than in a footnote, because a chapter reporting only the
capabilities would misrepresent the state of it.

- **Quanta outside the current focus are not retained.** Foveated decoding
  reuses prior work, but what falls outside focus is not preserved across the
  move. This is the most consequential of the four.
- **Projection between resolutions is reserved.** The mechanism that would let a
  detailed local decode fold into a coarse overview exists as a hook, not a
  capability. The latent-dimension machinery of chapter 4 is where it would
  attach.
- **Higher dimensions are unrolled rather than general.** The seed rules handle
  up to three dimensions by enumeration. The Rust decode is N-dimensional; the
  rules that drive it are not.
- **One legacy escape mechanism has not been replaced** by its quanta-native
  equivalent.

And one older piece of the system is called out in the tree's own documentation
as an example to learn from rather than follow: a flood implementation that sits
in the binding layer between host and engine, where logic should not live. It
still works. It is still wrong, and it is labelled as such where a reader will
find it.

---

## 7.6 What would falsify this

- **The understanding claim.** If surprise can be driven to zero on a world the
  agent's model does *not* track — a system that has stopped being surprised
  without having learned — the lockstep in §7.1 is coincidence rather than
  evidence.
- **Absence as a state.** If per-body decoding over one belief can be shown to
  lose information that per-body maps retain, the central representational
  decision is wrong.
- **Foveation.** The unretained out-of-focus quanta of §7.5 are the obvious
  place for this to fail. A task requiring a route through a region the agent
  once decoded and has since looked away from would expose it.

  There is a third state the current implementation does not distinguish, and
  naming it says where the fix goes: **directly resolved ≠ unresolved ≠ occluded
  but inferable.** A region the agent cannot currently see, but whose contents
  are constrained by what surrounds it, is not in the same epistemic position as
  one it has never approached. A blind spot is a limitation of access rather
  than a hole in the world, and a belief that collapses the two loses the
  constraint.
- **Per-dimension resolution.** If uniform refinement matches per-dimension
  splitting on a powered comparison, the added machinery is not earning itself.

One bound on the whole chapter: what is established is that the representation
*expresses* these things and that the gates pass. What is **not** established is
that it outperforms a well-tuned conventional planner on a benchmark either side
would agree to. That comparison has not been run, and per chapter 5's second
standing rule it should not be inferred from the fact that the mechanism works.

---

*Ends. Next: chapter 8, where the same loop is applied to the grain that lets it
write and repair programs — and where execution, not the codebook, gets the
final say.*
