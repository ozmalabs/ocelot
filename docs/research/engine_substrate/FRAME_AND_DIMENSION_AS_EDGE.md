# Frames and dimensions are edge types

**Status: design note, not built, not yet in the papers.** Written 2026-08-28 while paper 01's
conclusion was under review; deliberately kept out of that file. The claim is about the substrate's
primitives, so it belongs in a numbered body section if it survives, never in a conclusion.

## The claim

A **frame** and a **dimension** are both *edge types*. Their instantiations are edges. The two
parallel machineries the corpus currently maintains for them are one machinery.

## It is already half-written

Paper 01 does not treat the frame boundary as a subgraph. `Definition (World boundary)`:

> A boundary `B_{W:G}` is **the relation** through which containing frame `W` can alter situated
> graph `G` and through which graph-originated deformation can participate in interactions
> represented by `W`.

A relation is an edge. So the boundary was typed as an edge from the start; what was missing was the
consequence, which today's conclusion reached from the other direction — *a frame is its boundary, not
its contents; to individuate is to draw the boundary.* The definition and the conclusion are the same
statement, arrived at eleven sections apart and never connected.

The same definition already says the subgraph is not the frame: *"a situated graph is a subset of `W`,
not a thing separate from it: the boundary demarcates which subset is the graph."* The subgraph is a
**relatum**. The frame is the **relation**.

## Dimensions have edge states, not node states

`def:states` gives a dimension exactly four states for a frame:

| state | meaning | as an edge |
|---|---|---|
| NULL | not instantiated; nothing to have a value | the edge does not exist |
| undetermined | instantiated, no value realised | admissible, not collapsed |
| undisclosed | realised, not held by this frame | collapsed, outside this frame's aperture |
| resolved | realised and held | collapsed, in frame |

That is an edge's life cycle, not a node's. A node does not have an "admissible but uncollapsed"
state; an edge does, and it is exactly what `Definition (Admissible continuation)` is about. NULL ≠
zero is then not a special rule for dimensions — it is the ordinary difference between an absent edge
and an edge carrying the value 0.

## Four parallels that stop being coincidences

Frames and dimensions currently share, in separate prose:

1. instantiated-or-not, with the absent case sharply distinguished from a zero value;
2. per-frame relativity — neither has an observer-free version;
3. a grain or resolution, set per frame and (paper 02) per dimension independently;
4. an outside that is *absent* rather than *residual* — sub-aperture for frames, NULL for dimensions.

Four parallels between two allegedly distinct primitives is the signature of one primitive described
twice. Under the unification each is a property of edges: existence, endpoint-relativity, grain, and
the absent/residual gate.

## Resolving the type/instance question

The natural objection is that "dimension" sounds like a class (*height*) while "edge" is an instance.
Both, and the corpus already commits to the resolution: `def:states` is stated *for a frame*, and a
dimension has one state per frame. So

- **type**: `height` is an edge type — a way of relating that may be instantiated;
- **instance**: `a --height--> 3` is an edge, and the four states are states of the instantiation.

A frame is the same shape with containment as the type. What the corpus calls *instantiating a
dimension* and what it calls *drawing a boundary* are one operation: adding an edge of a given type.

## The apparent conflict with "the rules define the frame"

Paper 01's dependency order is `nodes → relations → rules → delta → grammar`, which puts relations
*before* rules — while today's conclusion says the rules define the frame. These do not conflict, and
saying why is load-bearing: relations are the **material**, rules are the **selection**. Rules
determine *which* boundary is drawn and where; they do not supply the kind of thing a boundary is. A
substrate with relations and no rules has boundaries available and none chosen.

## What it would buy

- One primitive instead of two, with the four parallels above becoming theorems rather than
  observations.
- `NULL ≠ zero` derived rather than stipulated.
- The frame regress and the dimension regress become one regress.
- A dimension of dimensions (paper 01a's `LatentDimension`, minted by rung 3 of the sd loop) stops
  being a special construction: an edge type over edge types is ordinary.

## The discriminator test: what does a frame NEED to do that a dimension does not?

Two things are different types only if something needs them to be. Below, every function the corpus
assigns to a frame, tested against a dimension. The test is not whether the corpus *says* a dimension
does it, but whether a dimension *can*.

| a frame … | can a dimension? | why |
|---|---|---|
| runs rules | **yes** | a dimension carries admissibility over its values — which value may follow which is a rule, and an ordered dimension has succession rules |
| has an aperture (Γ_a) | **yes** | its resolution *is* its aperture; below the grain is absent, not residual |
| has a change grammar (Γ_c), emits residual | **yes** | a value arriving that will not fit the admissible set is exactly the sd loop's residual, and is what drives a mint |
| individuates | **yes** | it distinguishes values, and distinguishing is individuating |
| holds standing structure | **yes** | its current value persists until written over — momentum at the dimension grain |
| instantiates dimensions | **yes** | per-dimension resolution splits and refinement depth (paper 02) are dimensions within a dimension |
| collapses | **yes** | undetermined → resolved *is* a collapse; `def:states` says so in those words |
| has a runner it cannot see | **yes** | nothing about a dimension knows what steps it |

Eight for eight. The reverse direction finds nothing either: minting, values, and frame-relativity all
have frame analogues.

### Three attempts to break it

1. **Endpoint cardinality.** A dimension relates a subject to a position; a frame relates a subgraph
   to its container. Both binary. No difference.
2. **Containment.** A frame contains dimensions; a dimension does not obviously contain frames. But a
   superframe's dimension *is* a correlation among subframes (paper 01a), so a dimension is at least
   *about* frames; and containment is a relation between two edges, not a property distinguishing
   their types.
3. **Direction of individuation.** A frame individuates its dimensions; a dimension is one of the
   things a frame individuates. This is the strongest attempt and it fails for the same reason as the
   second: a dimension individuates *its* values, and a frame is individuated by *its* container.
   Both are individuator-of-something and individuated-by-something-else. The asymmetry is
   **positional, not typal** — the same asymmetry as parent and child, which does not make parents
   and children different kinds of thing.

### The answer: one type, two roles

No needed difference was found. The distinction is relative position in a nesting:

> **A frame is a dimension of its container. A dimension is a frame to its values.**

Which is the substrate's own recursion restated at this grain — *a runner is the same kind of thing
it runs*, and each level *is* the structure rather than describing it. That the frame/dimension
distinction turned out to be the runner/runnee distinction one level down is a consistency check the
account passes.

**Keep both words, drop the claim that they are different kinds.** They name roles an edge plays
relative to another edge, and the ergonomic value of two words is real — collapsing the vocabulary
would make the papers much harder to read for no gain. What should go is the implication that
`frame` and `dimension` are separate primitives requiring separate machinery.

**Honest limit on this finding.** The table above was produced by inspection in one pass, not by
sweeping the corpus for places that depend on the distinction. That sweep is what would settle it,
and it has not been done. A single site that genuinely requires them to be different kinds refutes
this.

## What is not settled
- Whether anything in the corpus depends on frames being subgraphs in a way this breaks. The papers
  should be swept for it before the definitions change.
- Whether the engine's own typed graph (`substrate.rs`) already implements it this way, which would
  make the papers the thing out of step rather than the code.

## Where it goes if it survives

A numbered section in paper 01, near `Definition (World boundary)` and `def:states`, which are the
two definitions it unifies. Not the conclusion.
