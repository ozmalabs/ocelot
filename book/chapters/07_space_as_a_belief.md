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

The map here is a *belief*, and in a belief, **not-yet-observed is a state in
its own right** — distinct from empty and distinct from occupied. The agent does not
hold a grid with unknowns filled in; it holds what it has observed, plus the
fact that this is not everything.

The theory's own vocabulary makes a three-way distinction here, and it is worth
having before the chapter uses it:

> **NULL ≠ undetermined ≠ undisclosed ≠ resolved.** *NULL*: the dimension is
> absent, not instantiated at all. *Undetermined*: instantiated, and **no value
> has been realised** — the collapse that would produce one has not happened.
> *Undisclosed*: a value has been realised and this frame does not hold it.
> *Resolved*: realised, and held.

An unvisited cell is **undisclosed**. The spatial dimensions are instantiated,
the cell's contents are already determined — the world has them — and what is
missing is this agent's access. That is why exploration works at all: the agent
can go and get it.

The distinction from *undetermined* is the one that matters for what a map is
for. An undisclosed value can be obtained — by going there, by being told, or by
inference from what surrounds it. An undetermined value cannot be obtained by
any of those, because there is nothing yet to obtain; only a collapse settles
it. A map is a store of the first kind. A projection of where the agent might
go next is a store of the second. Conflating them produces either a map that
can never be completed or a plan that observation could somehow resolve.

And **NULL** is neither: not something the agent can look for.

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

That is easy to say and normally unfalsifiable, so it was measured. Two
quantities were tracked as the agent explored a world whose stations apply
transformations it has to work out: its *surprise* — prediction minus
observation — and the accuracy of its model against ground truth [SPACE-1].

The two have **different shapes**, and that is the first thing worth noticing.
Model accuracy **ramps**: 0.17, 0.33, 0.50, 0.67, 0.83, 1.0, one more station
modelled each cycle. Surprise **steps**: it sits at 1.0 until *every* station is
modelled and then drops to zero and stays there. Six stations, six cycles to
cover them, and the run is deterministic — zero variance across 25 episodes,
because the underlying recognition is.

So this is a curiosity-driven world model converging on ground truth, and it is
distinguishable from a policy that has learned to win. A policy that wins can
have any internal state at all.

**And then the part that makes it evidence rather than a curve.** The obvious
worry about a surprise metric is that a system could stop being surprised for
the wrong reason — by confidently re-predicting its own mistake. That is not a
hypothetical here. It was measured. Degrade the perception badly enough and
**accuracy goes to zero while surprise still converges to zero**: the agent
learns nothing, re-predicts its own wrong recognition, and reports no surprise
at all.

A surprise-only gate passes that run. The accuracy gate catches it. Which means
the clean result above is trustworthy *because* its instrument has been shown
failing — chapter 16's positive-control discipline, arriving in a chapter about
navigation.

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

- **The understanding claim.** The failure mode is not hypothetical — §7.1
  reports it under heavy noise. What would falsify the claim is the *clean* case
  behaving the same way: model accuracy that does not track the stations
  actually modelled, or a surprise step that arrives before the model is
  complete.
- **Absence as a state.** If per-body decoding over one belief can be shown to
  lose information that per-body maps retain, the central representational
  decision is wrong.
- **Foveation.** The unretained out-of-focus quanta of §7.5 are the obvious
  place for this to fail. A task requiring a route through a region the agent
  once decoded and has since looked away from would expose it.

  There is a third state the current implementation does not distinguish, and
  naming it says where the fix goes: **directly resolved ≠ undisclosed ≠
  occluded but inferable.** A region the agent cannot currently see, but whose
  contents are constrained by what surrounds it, is not in the same epistemic
  position as one it has never approached. All three concern the *undisclosed* —
  in each case a value exists and the question is only how much of it this frame
  can reach. A blind spot is a limitation of access rather than a hole in the
  world, and a belief that collapses the three loses the constraint.
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
