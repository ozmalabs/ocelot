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

## What is not settled

- Whether frames and dimensions are the *same* edge type or two, related by scale. The four shared
  properties argue for one; the fact that a frame runs rules and a dimension is not obviously said to
  argue for two — though a dimension does carry admissibility over its values, which is Γ, so this may
  dissolve on inspection. **Not resolved here.**
- Whether anything in the corpus depends on frames being subgraphs in a way this breaks. The papers
  should be swept for it before the definitions change.
- Whether the engine's own typed graph (`substrate.rs`) already implements it this way, which would
  make the papers the thing out of step rather than the code.

## Where it goes if it survives

A numbered section in paper 01, near `Definition (World boundary)` and `def:states`, which are the
two definitions it unifies. Not the conclusion.
