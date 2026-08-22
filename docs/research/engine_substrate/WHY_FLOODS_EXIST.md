# Why floods exist, whether they are the right operation, and what replaces them

**Status: analysis, prompted by the Stage A falsification (`STAGE_A_RESULTS.md` §5f). No code
changed.** Stage A was killed by `mo_flood`: freezing the derivation base slows label
propagation to one hop per pass. The question behind that failure is *is a flood the right
operation at all* — and the answer is narrower than this document first claimed: the flood
computes the **right partition** by a **wrong-shaped representation**. Two claims from the first
draft are retracted in place (§2a, §6), both killed by falsifiers built to test them.

## 0. The three claims

1. **The data is graph-native. The effect algebra is not.** All 13 effect variants are local
   writes; there is no merge or union. A component is a *global* object, so with local writes
   only, its identity can only be replicated into every member and diffused.
2. **The flood does force a transitive closure onto a non-transitive relation** — measured, a
   12-cell gradient chains into one group whose ends differ by 11.0 against a tolerance of 1.5.
   Whether that is a *defect* is domain-dependent and is NOT established here (§2).
3. **Boundary tracing produces the same partition** — measured, so it does not fix chaining
   (§2a). What it changes is the representation, the cost, and the diffusion — which is a real
   argument, but a narrower one than the first draft of this document claimed.

## 1. What a flood compensates for

The effect vocabulary: `AddEdge`, `DelEdge`, `AddNode`, `AddNodeIfAbsent`, `DelNode`,
`SetAttr`, `SetAttrIfDifferent`, `ReplaceValue`, `DefineConcept`, `SetRuleClause`,
`ApplyRulePatch`, `FbSample`, `NetCollapse`. **Every one is a local write. There is no merge.**
A rule cannot say *"these two components are now one."*

So the original suspicion — that flooding works around data that is not graph-native — is right
in substance but one level in from where it was aimed. The *cells* are perfectly graph-native:
`MCell` nodes joined by `neighbour` edges. It is the *components* that are not. In
`vision_motion_group`:

```
mo_mint:  members = Count(Filter(NodesOfType(MCell), z.mlabel == R.mlabel))
```

**Membership is equality of a scalar, not an edge.** A cell belongs to an object because its
number matches. Hence the flood exists to establish that equality, and reading membership back
is an O(N) scan of every cell in the field.

## 2. Chaining is real — measured — but is not by itself a defect

The grouping predicate is `|n.v - R.v| <= R.mtol`, a threshold on a pairwise difference, and a
threshold on a difference is **not transitive**. Built as a falsifier: a 1x12 strip with
`v_x = 0, 1, ..., 11` and `mtol = 1.5`, so every ADJACENT pair agrees (diff 1.0) while the ENDS
disagree by 11.0.

```
distinct mlabels: 1
   label 0.0 -> cells [0,1,2,3,4,5,6,7,8,9,10,11]
largest group spans cells 0..11;  |v[11] - v[0]| = 11.0   (tol 1.5)
```

So the closure does assert a relation the field's own predicate denies for the group's extreme
members. That is single-linkage chaining, and it is measured rather than argued.

**But it does not follow that the answer is wrong.** A smooth velocity gradient is exactly what
a slanted plane produces under parallax, so chaining a gradient into ONE surface is plausibly
the *correct* segmentation for this domain. An earlier draft of this document called chaining
"unfaithful" and said "even an infinitely fast flood would be wrong here". **That is retracted:
it asserted a domain judgement the measurement does not support.** Whether a gradient should be
one surface or many is a question about motion segmentation, not about flooding.

## 2a. RETRACTED: that boundary tracing avoids this

The first draft's central claim was that tracing the boundary sidesteps the transitivity
problem. **It does not, and the check is direct.** Tracing classifies each `neighbour` edge
agree/disagree by the same pairwise predicate; the region it encloses is the connected component
of the agree-graph — the same object the flood reaches by diffusion.

Measured on both a gradient and a genuine two-block jump:

| case | flood | trace | same? |
|---|---|---|---|
| gradient strip (1x12, step 1.0, tol 1.5) | one group `[0..11]` | one group `[0..11]` | **yes** |
| two blocks with a real jump | `[0..5]`, `[6..11]` | `[0..5]`, `[6..11]` | **yes** |

**Chaining is a property of the RELATION, not of the algorithm that closes it.** Any method that
groups by "adjacent and similar" chains identically. Fixing chaining would require a different
relation — comparing each cell against the region's aggregate rather than against its neighbour —
and that is orthogonal to flood-versus-trace.

This correction came from building the falsifier and running it against my own proposal. The
argument for tracing survives, but on narrower grounds than claimed, and those grounds are
below.

## 3. The predicate is already local, and already computed

Two rules in the same seed, both one-pass and both purely local:

```
mo_pair_diff:      pd   = MaxOver(Neighbours(R,"neighbour"), |n.v - R.v|)
mo_tol_broadcast:  mtol = field.mtol
```

So the pairwise agree/disagree test is **available before the flood runs**. Everything the flood
adds is closure. Nothing about the *evidence* requires diffusion — only the decision to treat
the evidence as an equivalence relation does.

## 4. Trace the boundary, mint the shape

The alternative, in the existing algebra:

1. **Classify each `neighbour` edge** agree/disagree by the pairwise test. One pass, local, no
   closure. (Already effectively computed by `mo_pair_diff`.)
2. **The boundary is the set of disagree edges** plus the field border. Locally detectable —
   a cell is on a boundary iff some incident edge disagrees. **No diffusion.**
3. **Link consecutive boundary edges into a cycle.** At a boundary cell, the next boundary edge
   in rotational order is determined by that cell's own neighbours — local again. Mint
   `next_boundary` edges (`AddEdge` already exists).
4. **The cycle IS the shape.** Following it is a read-time traversal, not a fixpoint.

### And the cost is not O(perimeter) either — it is O(vertices)

A contour does not have to be exact, only close enough, and straight runs collapse to a single
segment. So the cost is set by **curvature**, not extent. Measured on the same parallax scene the
vision tests use (18x18 field, tolerance 1.0, Ramer-Douglas-Peucker at several epsilons):

| region | area (cells) | perimeter (cells) | vertices @0 | @0.5 | @1.0 | @2.0 |
|---|---|---|---|---|---|---|
| 0 | 115 | 44 | 17 | 16 | **5** | 5 |
| 1 | 108 | 45 | 5 | 5 | **5** | 5 |
| 2 | 91 | 44 | 6 | 6 | **5** | 5 |

A 115-cell region is **five vertices**. Against the label field's 324 numbers, the five largest
regions cost 17 vertices — **19x fewer**.

Two things in that table matter more than the ratio:

- **The fidelity axis exists at all.** Region 0 needs 17 vertices at eps=0 and 5 at eps=1.0, so
  12 of those 17 were grid-quantisation noise rather than structure. Approximating *removed*
  noise instead of losing information. **A label field has no such axis — there is no approximate
  label.** That is the qualitative difference, not the constant factor: a shape can be held
  coarsely and refined where the residual demands it, which is the sd loop's own
  decode -> residual -> refine ladder and the quanta rung's *"a remainder goes to more detail"*.
- **All three large regions reduce to 5 vertices**, consistent with the scene's three depth
  planes being quadrilaterals differing by pose. That is the shape the sd loop is built to
  exploit — one held signature plus a per-region transform, rather than three unrelated integers.
  **Not established:** that decoding them against the held codebook actually recognises them as
  one shape under transform. That is the next measurement and it is unbuilt.

### Why a contour is the right output for THIS substrate specifically

A traced boundary is a path, and this repo already has the machinery that turns a path into a
first-class shape: `StrokeQuantize` quantizes a pen path into `seg` relations — signed
relative-turn and normalized-length quanta, rotation/translation/scale invariant — with pose as
separate single-slot relations. That is the sd loop's own input format. A traced region boundary
could therefore be **recognised against the held codebook, transformed at rung 1, dimension-
inferred at rung 3, and minted at rung 4**, exactly like ink.

A label field is recognisable as nothing. It supports one query — "same number?" — by scanning
every cell.

The project already made this move once and wrote it down: *"flood does not occur per pixel, it
occurs at quanta; a remainder goes to more detail"* (quanta navigation). Vision grouping is the
per-pixel version that predates it. Ink went the path-and-shape way and the whole Omniglot arc
followed from it; vision grouping went the label way and produced a scan.

## 5. Where relaxation IS correct, and stays

None of this touches `qf_relax` / `mv_relax`. Those relax a **metric over paths** — a
shortest-path field genuinely requires iterative relaxation, and Bellman-Ford compensates for
nothing. **You cannot one-hop a shortest path.** The distinction is:

| propagating | closure over | verdict |
|---|---|---|
| an **identity** (label, group, owner) | a similarity relation | right partition, wrong representation — the contour is the shape |
| a **metric** (distance, cost) | a genuine additive path measure | right operation — keep relaxing |

The one that killed Stage A is from the first row.

## 6. RETRACTED: the corpus flood count

An earlier version of this document reported "119 flood rules across 60 seeds", then "36 rules /
56 effects" after tightening. **Both numbers are withdrawn.** Three successive static classifiers
were built; each had different false positives or negatives:

- v1 matched a traversal and a key-read anywhere in the same term, without requiring them to
  compose — swept in one-shot aggregates;
- v2 required the read to come through a traversal term, which **missed `qf_relax` entirely**,
  because its traversal is in the *match* (`[Q, portal, R]`), not the term;
- v3 accepted either idiom but could not tell whether the two vars range over the **same node
  population**, so it still counted one-shot initialisations like
  `ha_initialize_support_phase_action_model` as floods.

Distinguishing a flood from a copy requires knowing that both ends of the relation are the same
kind of node, which the seed JSON does not carry. **"Is this a flood" is not reliably decidable
statically**, and a number that cannot be defended should not be quoted — this repo's own
retracted-baseline lesson. What survives is hand-verified: `mo_flood` and `bo_label` propagate
identity; `qf_relax` and `mv_relax` propagate a metric.

The honest way to get the population is runtime: a true flood fires across many passes of one
fixpoint, a copy fires once per target. That measurement has not been run.

## 6a. BUILT: `seeds/vision_boundary_trace.json`

Three rules, no new Rust, no new constant, `depends_on: vision_motion_group` and inert until
`marm` is raised:

```
bt_disagree      [R neighbour n]  |n.v - R.v| > R.mtol   ->  add_edge R cuts n
bt_boundary_cell [R cuts n]                              ->  set_attr R on_rim 1
bt_rim_link      [R neighbour n]  both on_rim, they AGREE ->  add_edge R rim_next n
```

The rim is a **subgraph**, not a label field: `cuts` marks boundary crossings, `rim_next` chains
consecutive rim cells of one region, and a reader traverses `rim_next` to emit a contour.
Membership is read as components of the graph MINUS `cuts` — no scan of every cell, no label.

### Measured

**The partition is unchanged** (as §2a requires — this is a representation change, not a
different grouping), on 1xN strips and on the real 18x18 parallax field: 13 regions, identical
sets.

**Cost does not track region size**, and — the property that matters — **it does not depend on
the derivation mode**:

| n (strip) | flood, committed | flood, Stage A | rim, either |
|---|---|---|---|
| 8 | 4 | 6 | **3** |
| 32 | 4 | 18 | **3** |
| 64 | 4 | 34 | **3** |
| 128 | 4 | **66** | **3** |

Real 18x18 parallax field: flood 5 sweeps committed / **25** under Stage A; rim **4 in both**,
with bit-identical output (98 on_rim, 120 cuts, 142 rim_next).

That table also explains the Stage A falsification exactly. **The flood's speed on the committed
engine rests entirely on same-round visibility** — later bindings of `mo_flood` reading labels
earlier bindings just wrote. Remove it and the flood degrades to one hop per pass, which is why a
108-cell object minted as 3. The rim never reads what a sibling binding wrote, so it is
indifferent.

### Gate

`tests/test_vision_boundary_trace_migrated.py`, 4 tests: partition equality, cost independent of
size, **output invariant under `stage_a_enable`**, and the no-new-constant check. Mutation-tested
— inverting the boundary predicate fails the partition test, so the gate bites.

## 7. What this does not establish

- **The chain now RUNS, and is only partly successful.** rim -> ordered contour ->
  `StrokeQuantize` -> signature works end to end: the largest region traces a 44-point ring and
  quantises to a signature with real turns (`(seg,1,2,0) (seg,4,2,0) (seg,5,2,0)`). Two of the
  three large regions still dead-end after 5-6 points despite carrying 43 rim cells each. The
  failure is in the rim subgraph itself, and the first diagnosis of it was wrong — see below.

### The walk's direction is a magic number, and it was NOT the blocker

The traversal picked its next cell by "most clockwise turn from the incoming heading", with an
arbitrary start cell and an arbitrary initial heading. Three conventions, none derived from
anything — the same defect `TIE_CONSEQUENTIALITY_RESULTS.md` names as *enumeration order
silently implementing a policy nobody wrote*, reappearing in my own adapter.

But measured, on the same scene, it is also nearly **inert**:

```
rim cells: 140
   degree 0:  14   <- dead end
   degree 1:  11   <- dead end
   degree 2: 114
   degree 3:   1   <- ambiguous, the convention decides
```

**One cell in 140 is ambiguous.** The convention is real magic and decided a single case, while
being blamed for the whole failure. The actual blocker is the 25 cells of degree < 2: a closed
curve has every cell at degree 2, so the rim is not a curve.

Breaking those down by the region they belong to: **10** are the ten single-cell regions, which
is correct by construction — a 1-cell region has no rim curve. **14** are in the 115-cell region
whose walk stopped after 5 points, and **1** in the 91-cell region.

The cause is structural, not a tuning problem. Every adjacent pair INSIDE a region agrees by
construction — that is what made it one region — so `bt_rim_link`'s predicate cannot be what
fails. It fails because **a boundary turns diagonally and `neighbour` is 4-connected**: the next
cell along a staircase rim is diagonal, and no 4-connected edge can chain it.

**The principled fix is not a better convention, it is the right element.** A boundary is
BETWEEN cells, not on them: the 60 `cuts` crossings are the boundary, and there are fewer of
them than the 140 rim cells that approximate it (2.33 rim cells per crossing).

### BUILT: the crossings. NOT built: their successor, and the reason is measured

`bt_mint_crossing` (v1.2.0) reifies each disagreement as a `Crossing` node with `separates`
edges to both cells. `cuts` is symmetric because the predicate is, so the naive mint emits two
nodes per boundary; a `Lt(R.cid, n.cid)` guard makes one ordering canonical and
`add_node_if_absent` keyed on `(lo, hi)` makes re-firing a no-op. **60 crossings for 60
disagreeing pairs, exact and idempotent**, gated.

The successor relation was then written the obvious way — *two crossings that share a cell are
consecutive*, an ordinary match with no angle sort anywhere — run, measured, and **removed**:

```
next_crossing degree:  0:34   1:5   2:12   3:5   4:4
degree-2 fraction: 12/60 = 20%      (the rim-cell version it replaced: 81%)
crossings per cell:  1: 84 cells    2: 6    3: 8
```

Worse than what it replaced, and the census says why: **84 boundary cells carry exactly ONE
crossing.** A cell on a straight boundary has a single disagreeing neighbour, so consecutive
cracks along that boundary lie between DIFFERENT pairs of cells and share no cell at all. They
share a **corner**.

The corner turned out NOT to need reifying, and no coordinate arithmetic was required. Two
collinear cracks `x = (A|B)` and `y = (C|D)` are consecutive exactly when the cells correspond
ACROSS them — `A neighbour C` and `B neighbour D` — which is pure adjacency: no lattice index, no
doubled grid, no bare `2`, no angle sort. The corner is IMPLIED by the correspondence. Cracks
that turn a corner share the cell they turn around, which is what the removed rule got right;
its failure was being the only rule, so the collinear majority went unlinked.

`bt_chain_collinear` + `bt_chain_perpendicular` (v1.3.0):

| | degree-2 | isolated | saddles (deg>2) |
|---|---|---|---|
| share-a-cell only (removed) | 12/60 = 20% | **34** | 9 |
| both rules | **39/60 = 65%** | **0** | 15 |

Zero isolated crossings, and the residual degree-3/4 are genuine saddles left VISIBLE as degree
rather than resolved by a hidden convention. Filtered to a single region's boundary they vanish
entirely — the branches are between regions.

### The contour closes, and the shape is recognised

Walking `next_crossing` per region: a 3x3 interior blob yields a **closed 12-crossing contour**,
exactly its perimeter, with no start convention, no heading and no turn preference anywhere in
the walk.

### Open contours at the field edge are CORRECT, and were nearly "fixed"

Regions touching the field edge yield OPEN arcs, because `bt_disagree` needs a `neighbour` edge
and a field-edge cell has none. The obvious next move is to mint a virtual `Outside` and join
the border cells to it, closing every contour. **That would be wrong**, and it is this repo's own
principle that says so: *unknown = absence, first-class*. A region running off the observed field
is genuinely unbounded IN THAT OBSERVATION; closing its contour manufactures a boundary nothing
observed, and lets a partial view assert it has seen a whole object.

What must hold instead is that a partial view produces a RESIDUAL. Measured — the same 3x3
square, once interior and once clipped by the top edge:

```
interior  : 12-pt CLOSED contour  ->  covered (16, 'closed_square')
clipped   :  9-pt OPEN   contour  ->  covered (7,  None)
```

**The clipped region declines to claim it is the square.** It covers partially and is recognised
as nothing — which is exactly the residual the ladder acts on, whether by refining or by minting.
So the open contour is not a gap in the representation; it is the representation being honest
about the extent of the observation, and the "fix" was measured out rather than built.

And the §4 claim is now established rather than asserted. Two identical 3x3 squares at different
positions, plus a 3x6 rectangle, quantised through `StrokeQuantize` with `invariant_only`:

```
square A  12 pts  bbox 3x3  sig (0,0)(1,0)(2,1)(3,0)(4,1)(5,0)(6,1)(7,0)
square B  12 pts  bbox 3x3  sig (0,0)(1,0)(2,1)(3,0)(4,1)(5,0)(6,1)(7,0)   <- identical
rectangle 18 pts  bbox 6x3  sig (0,0)(1,0)(2,1)(3,2)(4,2)(5,0)(6,0)(7,2)   <- differs
```

**Same shape, one signature, differing only by pose; different shape, different signature.**
That is the thing a label field cannot express at all — three regions under `mo_flood` are three
unrelated integers. Both halves are gated, and the bbox is asserted non-degenerate, because an
equality assertion alone cannot distinguish this from the three straight lines that matched
vacuously earlier in this section.

### And the contour reaches the substrate's own codebook

Signature equality is weaker than recognition. Run through `grow_stroke_quantum` and
`ShapeDecode` — the sd loop's actual machinery, not a comparison:

```
square B before any mint  : covered = (0,  None)          <- nothing held, nothing recognised
mint from square A        : node installed, 16 signature relations
square B after the mint   : covered = (16, 'region_square')   <- a DIFFERENT region, recognised by name
rectangle after the mint  : covered = (9,  None)          <- partial: a residual, unnamed
```

A region boundary is therefore an ordinary citizen of the codebook: recognised when it matches
a held quantum, and producing exactly the partial-coverage residual `sd_mint_quantum` fires on
when it does not.

### But the ink ladder does NOT transfer unchanged — measured

An earlier version of this section said the ladder built for ink "applies to a contour
unchanged". **That is too strong and is corrected here.** Translation transfers; rotation and
scale do not, and the two fail for different reasons:

```
3x6 rectangle (minted)      -> (16, 'rect_3x6')   control
the same rotated 90 degrees -> ( 8,  None)        NOT recognised
3x3 square (minted)         -> (16, 'square_3x3') control
the same at 2x scale (6x6)  -> (11,  None)        NOT recognised
```

**Rotation fails because a loop has no canonical start.** The rotated rectangle carries the
SAME MULTISET of turn quanta as the original — the shape content is identical — but no cyclic
shift aligns the two sequences, because the walk begins at a different corner and may run the
opposite way round. `StrokeQuantize` was built for STROKES, which have a pen-down start and a
direction; a closed region boundary has neither. A signature that is a sequence needs a
canonical origin, and for a loop that has to be *derived* (extremal turn, say) rather than
inherited from the writing order. This is a real structural difference between a stroke and a
contour, and it is not a wiring mistake.

**Scale fails for an unrelated and less fixable reason.** The 3x3 and 6x6 squares differ even in
their turn MULTISET (bins `2` versus `3`): a small square's corners are proportionally blunter
on a discrete grid than a large one's, so the quantised turn profile genuinely differs. That is
observation-resolution, not canonicalisation, and no re-indexing of the sequence recovers it —
it is the same *"pin a continuous parameter only to observational resolution"* limit this repo's
frame/continuum rule already states.

### The grid is not a property of the boundary, and the continuous verdict shows it

The scale failure above is a GRID artifact, not a fact about the shapes: a small square's
corners quantise blunter than a large one's because the sampling lattice is coarser relative to
the object, and a human looking at the same two squares does not see a lattice at all. This
repo's frame/continuum rule already says where that belongs — **in-frame is integer, non-integer
math is CROSS-FRAME** — so comparing a shape to a rescaled or rotated one is a comparison
BETWEEN frames, and settling it with an integer signature computed INSIDE one grid frame is
using the wrong instrument. Run 16 measured the same thing on Omniglot (26.8% -> 73.5%) and
named it: **bins propose, continuous decides.** The rotation/scale failure above is that lesson
recurring, with me on the wrong side of it.

Measured on the same four contours, with the held continuous comparators:

| | `ScTpsDist` | `PointSetDist` |
|---|---|---|
| A vs A (identity) | 0.0000 | 0.0000 |
| C vs D (**same**, 2x scale) | **0.0885** | 10.2183 |
| A vs C (different) | 0.2587 | 8.7107 |
| B vs D (different) | 0.2450 | 7.3164 |
| A vs B (**same**, rotated 90) | **0.4463** | 7.0127 |

**Scale is recovered.** SC+TPS puts the 2x-scaled square nearly 3x closer than either genuinely
different pair — the grid artifact that defeated the integer signature dissolves under a
cross-frame comparison, which is precisely what the rule predicts. `PointSetDist` separates
nothing, as expected of a raw point distance with no normalisation; the descriptor is doing the
work, not the continuity alone.

**Rotation is recovered by neither, and is worse than unhandled**: a rotated SAME shape scores
FURTHER (0.4463) than two genuinely different shapes (0.25). Shape contexts normalise scale but
not orientation. So rotation is not a comparator problem to be fixed by a better distance — it
is a POSE dimension, which is exactly how the sd loop already treats it (`StrokeQuantize` stores
`pose_o` as a separate single-slot relation, codebook entries held at `canonical_pose`). A
rotated contour should present as one held shape plus a `pose_o` delta — rung 1 — and the
missing piece is a canonical orientation for a loop, which for a stroke comes free from the
writing direction.

So the scorecard, measured rather than assumed:

| transform | integer signature (in-frame) | continuous verdict (cross-frame) |
|---|---|---|
| translation | recognised | recognised |
| scale | **fails** (grid quantisation) | **recovered** |
| rotation | fails (no canonical loop origin) | fails (no orientation normalisation) |

Rung 0 is demonstrated. Scale belongs to the verdict layer and works there.

### Rotation is TWO failures, and one of them no comparator can fix

The rotation result above used a 3x6 and a 6x3 rectangle — a 90-degree rotation, which is EXACT
on a lattice. So that failure was the comparator, not the grid. The sharper claim is the general
one: **on a grid, rotating a shape changes the shape.** Measured — one 9 x 4.5 rectangle
rasterised at five angles:

| deg | cells | contour pts | perimeter / sqrt(area) |
|---|---|---|---|
| 0 | 45 | 28 | 4.17 |
| 15 | 41 | 32 | 5.00 |
| 30 | 41 | 32 | 5.00 |
| 45 | 45 | 36 | **5.37** |
| 90 | 45 | 28 | 4.17 |

The same rectangle occupies a **different number of cells** (45 vs 41, ~9%) and its contour needs
**29% more sample points** at 45 degrees, where the staircase is maximal. **Correction:** an
earlier version of this paragraph called that a 29% *perimeter* inflation. It is not — that
column is contour POINT COUNT over sqrt(area). Measured as actual polygon perimeter the figure is
stable, 3.97 to 4.27 (about +/-4%): the staircase adds samples, not length. The grid damage to
this shape is real but smaller than first reported. 0 and 90 are identical, confirming
that axis-aligned rotations are exact and the grid is blameless for those. **So the input to any
comparator is not rotation-covariant**, and no distance function operating on grid-extracted
contours can be rotation-invariant, because the thing it is given has already changed.

The distances then separate the two effects, and the ordering is the informative part:

```
ScTpsDist against the 0-degree contour:
   15 deg  0.0794      30 deg  0.1127      45 deg  0.2592      90 deg  0.3922
```

**90 degrees scores WORST — with a pixel-identical footprint to 0 degrees.** The grid did nothing
to it; the comparator simply cannot see through orientation. So both failures are real and they
are independent:

- a **representation** failure, irreducible by better comparison: 15/30/45 degrees are genuinely
  different rasters of one rectangle;
- a **comparator** failure, currently the LARGER of the two: 90 degrees is the same raster and
  scores furthest of all.

Fixing either alone leaves the other. And the representation half is the one that says the grid
is the wrong object: a boundary is a curve, the lattice is the apparatus that sampled it, and a
contour read off cell centres is a rendering artifact being compared to another rendering
artifact. The de-gridding step already appeared once in this document without being named as
one — simplifying region 0 from 17 vertices to 5 discarded exactly the staircase, and the note
there was that 12 of the 17 were "grid quantisation noise". Fitting the boundary as a continuous
curve at sub-cell resolution, rather than reading it off cell centres, is what that implies.

### Sub-cell fitting, built — and it cannot recover what sampling threw away

Every crossing so far sat at `t = 0.5` between two cell centres: a magic number, and the
staircase's direct cause. The position is derivable instead — the boundary is where deviation
from the region's own motion reaches `mtol`, and linear interpolation between two samples locates
that level, giving a real `t` in (0,1). That is exactly the sort of non-integer quantity the
frame rule permits: it lives in the map from the observation lattice to the boundary, not inside
the lattice.

Measured on the same five angles, `ScTpsDist` against the 0-degree contour:

| deg | hard mask: midpoint -> sub-cell | soft edge: midpoint -> sub-cell |
|---|---|---|
| 15 | 0.0794 -> 0.0757 | 0.1437 -> **0.1300** |
| 30 | 0.1127 -> 0.1189 | 0.1960 -> **0.1412** (−28%) |
| 45 | 0.2592 -> 0.2777 | 0.3004 -> 0.3220 |
| 90 | 0.3922 -> 0.4403 | 0.6323 -> **0.5266** |

**On a hard mask it does nothing**, and the reason is the point. With a binary field
(`0` or `9`, no gradient) the interpolation is degenerate: `d_in = 0`, `d_out = 9`, so `t = 1/9`
at EVERY crossing — a uniform inward shift, an ~8% smaller perimeter, and not one step of the
staircase removed. **A hard mask contains no sub-cell information**, so no fitting can recover
where in the cell the edge actually lay. That is an information limit, not an implementation gap.

**On a soft edge it helps**, modestly and unevenly: supersampling gives cells straddling the
boundary partial coverage — the sub-cell information a blurred or anti-aliased observation
carries — and the fit then improves 3 of 4 angles, best 28% at 30 degrees, while worsening 45.

So the sharpened version of "the grid is the wrong thing": **the damage is done at SAMPLING time,
not at contour-extraction time.** You cannot de-grid afterwards if the sampling already discarded
the sub-cell evidence. Where the observation retains it, fitting recovers part of the loss; where
it does not, the staircase is the honest answer and the contour should not pretend otherwise.

And sub-cell fitting is not a rotation fix. **Not landed as a default**: nothing in the tree
emits contours in production yet, and a mixed result should not become the committed geometry on
the strength of one synthetic.

### FIXED: factoring pose out, rather than asking the distance to absorb it

The dominant term throughout was the comparator, not the grid — 90 degrees, whose raster is
pixel-identical to 0, scored worst in every column above. `ScTpsDist` normalises scale but not
orientation, and asking for a rotation-invariant *distance* is the wrong request: **orientation is
a POSE dimension**, which is exactly how the sd loop already treats it (`pose_o` as its own
single-slot relation, codebook entries at `canonical_pose`). A stroke inherits its orientation
from the writing direction; a closed contour must DERIVE one.

Principal axis supplies it, up to the residue a second moment cannot fix — the axis is defined
only up to sign, and reflection not at all. That residue is four discrete candidates, so the
verdict is an `Argmin` over them and **the winning candidate IS the pose delta**: one held shape
plus a transform, rung 1, not a fudge factor. Bins propose the candidate poses; the continuous
distance decides among them.

| deg | raw | pose-aligned |
|---|---|---|
| 15 | 0.0794 | 0.0680 |
| 30 | 0.1127 | 0.1127 |
| 45 | 0.2592 | **0.0234** |
| 90 | 0.3922 | **0.0053** |

90 degrees improves **74x** and 45 degrees **11x**. More importantly the ordering is repaired:

```
worst SAME-shape, aligned : 0.1127
DIFFERENT shape, aligned  : 0.1486     -> separates
```

Before alignment the 90-degree SAME shape (0.3922) ranked worse than a genuinely different one
(0.1486) — actively misleading, not merely blind.

Two honest limits. **The margin is thin**: 0.1127 against 0.1486 is 1.3x, on one synthetic pair.
And **the residual IS the grid damage** — after orientation is removed, the worst same-shape
distance is the 30-degree case, whose raster genuinely differs (41 cells against 45). That is the
irreducible half of the earlier decomposition, now isolated rather than confounded with the
comparator.

The Python here is the demonstration. The graph-native form is an `Argmin` over held pose
candidates with `ScTpsDist` as the value — every piece of which already exists as a Term — and
that is unbuilt.

The test uses `teach`'s own `OZMA_SEED_PERSIST_DISABLED` guard, which keeps the live-graph
install and skips only the seed-dir write. Stubbing `teach` instead — the first attempt — also
removes the node `ShapeDecode` has to read, and the probe then reported `covered=(0, None)`
everywhere while looking like a clean negative result.
- **A defect this chain caught, recorded because it nearly passed as a success.** Before
  `bt_border_rim` (v1.1.0), a region running off the edge of the field had an OPEN rim:
  `bt_disagree` can only mark a crossing where a `neighbour` edge exists, and border cells have
  no neighbour beyond the edge. All three regions then traced as straight vertical lines of zero
  width, and their signatures came back **identical** — which reads exactly like the hoped-for
  result ("one shape under three poses") and is in fact three degenerate lines matching
  vacuously. It was caught only by printing the contour geometry instead of trusting the
  comparison. With the border rule the same test reports 2 distinct signatures of 3, and the two
  that still match are precisely the two whose walk fails.
- **Nothing has been decoded against the codebook.** `ShapeDecode` has not been run on these
  signatures, so the §4 claim — that the three regions are one shape under transform — remains
  unestablished. The vertex measurements in §4 were made in Python, off-graph.
- **Nothing replaces `mo_flood`.** The seed derives the rim ALONGSIDE the label field; no rule
  was removed and `mo_mint` still counts members by scanning on `mlabel`.
- **`bt_rim_link` links rim cells pairwise, which is not the same as an ordered cycle.** Holes,
  nesting, orientation, and rim cells with more than two rim neighbours (junctions) are all
  unhandled — the subgraph is correct, a canonical traversal order of it is not defined.
- **Contour tracing has its own obligations**: orientation (outer vs inner boundary), nested
  holes, and open regions clipped by the field border. All standard, none free.
- **Area, if still needed, is a separate read-off** — the shoelace formula over the contour is a
  cross-frame numeric computation, which is admissible under this repo's frame/continuum rule
  but is not the same object as `Count(members)`.
- **Nothing here rescues Stage A.** The metric relaxations of §5 still propagate one hop per
  pass, and freezing the base still slows them. Stage A remains falsified.
