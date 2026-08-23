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

## 6c. Against the eye: the two pipelines are complements

`seeds/vision_border_ownership.json` is the same problem solved the other way round, and the
comparison is exact:

| | eye (`vision_border_ownership`) | crossings (this work) |
|---|---|---|
| region identity | `bo_label` — an identity flood | components via `cuts`, no diffusion |
| surroundedness | `bo_bgflood` — floods inward from the frame along equal-value adjacency, O(diameter) | "does this component contain a frame cell" — one read |
| perimeter | `bo_rim` — `Count(Filter(NodesOfType(Cell), …))`, an O(N) scan **per cell** | count the component's crossings, one hop |
| **figure/ground polarity** | **`bo_own` — a DIRECTED boundary owning its figure** | **absent** |

So the eye has the one thing this work lacks, and pays for it with two floods and a scan. But
**surroundedness is just "does this component touch the frame"**, which the crossing construction
already answers without diffusion — so `bo_own`'s polarity is SEPARABLE from the flood that
currently pays for it. That is the synthesis: crossings for the boundary, ownership for the
polarity, neither flood.

> **CORRECTION to the table above.** It claims "components via `cuts`, no diffusion". The
> components in question were computed by **union-find in Python** — a closure over cells, O(area),
> moved out of the graph rather than avoided. Nothing in the seed computes them. Connected
> components genuinely need closure, as this document establishes early on, so that column was not
> a fair win as written.
>
> **But polarity does not need them.** The crossing graph has degree 2 everywhere, so its connected
> components ARE the boundary cycles and finding them is a walk of O(perimeter), not a flood over
> O(area). Orient each cycle locally — at any one crossing, walk so the brighter of its two cells
> is on the left — and the cycle's total turning then gives its polarity:
>
> ```
> disc            76 crossings   +6.28  -> figure
> annulus outer   92 crossings   +6.28  -> figure
> annulus inner   44 crossings   -6.28  -> hole
> two discs       36, 36         +6.28  -> figure (both)
> ```
>
> Correct in every case, with no flood, no cell components and no frame-contact test. A first
> attempt read the turning sign WITHOUT the local orientation step and got -6.28 for everything,
> including a disc's outer boundary — the sign was reporting the walk direction, which the
> lowest-node-id tie-break had made arbitrary.
>
> **The limitation is exactly where the eye earns its cost.** This works because the scene has two
> values and the figure is the brighter one. Genuine figure-ground ambiguity is CONTEXTUAL — the
> von der Heydt result the seed is built on is that an IDENTICAL local edge flips ownership with
> the global figure — and no local rule can settle that. So `bo_bgflood` is not redundant; it is
> buying the contextual case specifically, and the local construction covers the unambiguous one
> for free.

Polarity is worth having on its own terms — it distinguishes a figure from a hole and makes the
boundary directed. **What it did NOT buy was the speedup I expected.** Orienting each contour so
the owned side is consistently on the left, then dropping the reversal search from the turning
metric:

| | error |
|---|---|
| plain contour, reversal searched | **6.6%** |
| plain contour, no reversal search | 7.7% |
| ownership-oriented, no reversal search | 7.7% |

The mechanism engaged — 9 of 35 contours were flipped to a consistent sense — so this is not an
inert instrument. The reason it does not substitute is that **the reversal search is not fixing
orientation, it is supplying REFLECTION invariance**, which is a separate axis: 58 of 105
within-shape pairs match better reversed, far too many to be traversal inconsistency, and
explained instead by these shapes being mirror-symmetric themselves so the two senses tie. Losing
that invariance costs 1.1pp.

## 6d. The other way round: a region as a WIDE STROKE

Everything above describes a region by its OUTLINE. The dual describes it by a CENTRELINE plus a
WIDTH -- Blum's medial axis (1967) -- and for anything elongated that is far more compact. It
also lands in machinery that already exists: `StrokeQuantize` consumes strokes, and a wide stroke
is a stroke with a width profile.

No flood is involved: the crossings are already reified, so distance-to-boundary is computed
against them rather than grown inward by a grassfire.

| shape | cells | boundary points | **medial points** | width |
|---|---|---|---|---|
| disc r=9 | 253 | 76 | **5** | 14.9-17.1 |
| bar 18x5 | 95 | 48 | 15 | 5.0 constant |
| ell | 155 | 72 | 26 | 5.0-6.4 |
| square 16 | 289 | 68 | 21 | 7.0-17.0 |

**A disc is five points — one point up to grid resolution — with a radius.** That is the literal
form of "a circle has one point": as an outline it is 76 boundary samples or one arc; as a stroke
it is a POINT and a thickness. The bar is a centreline of constant width 5.0, the square is its X
of diagonals with width rising from corner to centre, the ell is an L thickened at the corner.
The stroke beats the outline on size for every shape here — 15x for the disc, about 3x for the
rest.

**Three criteria were tried and discarded before one worked**, each caught by a control rather
than by reading the code:

- **local maxima of the distance field** — finds only the maximal-disc centre. Along a square's
  diagonal the distance RISES toward the middle, so a square came back as ONE point instead of an
  X;
- **two nearest boundary points, separated in absolute distance** — scale-dependent and far too
  weak. Adjacent crossings on a discrete boundary sit about one cell apart, so a threshold of 2
  admitted 289 of 289 cells;
- **object angle alone** (the standard criterion: the two nearest boundary points must lie on
  opposite sides as seen from the point) — still admits a point pressed hard against a straight
  edge, where two ADJACENT crossings straddle it and look opposite from close range. A disc came
  back with 57 medial points.

What works is object angle **plus geodesic separation**: the two generating boundary points must
also be far apart ALONG the contour, which the crossing chain already provides. That is the
standard pruning for a discrete medial axis, and it is available here for free precisely because
the boundary was reified as an ordered structure rather than a set of pixels.


## 6e. COST AUDIT — it should be cheap, and where it is not, it was done wrong

Measured rather than assumed, on discs at four field sizes (cells x5.8, crossings x2.6 from the
smallest to the largest):

| stage | n=17 | n=41 | growth | verdict |
|---|---|---|---|---|
| crossing walk | 0.015 ms | **0.043 ms** | x2.9 | **O(perimeter)** — correct |
| turning function psi | 0.24 ms | 0.41 ms | x1.7 | fixed resample — correct |
| psi comparison | 2.15 ms | **2.16 ms** | **x1.0** | flat in shape size — correct |
| cell components (union-find) | 0.79 ms | 4.81 ms | x6.1 | **O(area)** — WRONG |
| medial, per-cell distance | 1.3 ms | 8.5 ms | x6.5 | **O(area x perimeter)** — WRONG |
| `ScTpsDist` | 0.62 ms | 4.36 ms | x7.0 | superlinear in boundary points |
| substrate settle | 41 ms | 77 ms | x1.9 | sublinear — and it DOMINATES |

**The boundary pipeline is cheap: 43 microseconds, scaling with perimeter.** The comparison is
flat. Two stages are not, and both fail the same way — they work over the AREA when the whole
point of reifying the boundary was that they need not:

- **cell components** cost 110x the walk at n=41 and grow with area. This is the union-find
  already flagged as "moved to Python, not avoided" — and §6c showed polarity does not need it at
  all, since crossing cycles plus local ownership give figure/hole directly. It is pure waste.
- **the medial axis** is computed as a distance from every interior cell to every crossing. The
  medial axis is a subset of the VORONOI diagram of the boundary, which is O(perimeter); touching
  every cell to find it is the same mistake one level on.

And the honest headline: **the substrate settle dominates everything by 10-40x.** Every geometric
stage together is under 15 ms at n=41 against 77 ms for the rule engine. So arguing about the
geometry's constant factors is arguing about the wrong term — which is itself the answer to "why
does this need to be cheap": it already is, and the cost that remains is the engine's.


## 6f. THE TWO EXPENSIVE STAGES, FIXED — and the medial axis turns out to belong to the PROGRAM

§6e measured two stages working over the AREA when the point of reifying the boundary was that
they need not. Both are now fixed, and the second fix landed somewhere more interesting than
expected.

**The contour: O(area) -> O(perimeter), byte-identical output.** The union-find was doing three
jobs, and none of them needs a cell: orientation comes from `owns_figure` (minted locally by
`bt_own`); the regions are the CYCLES of the `next_crossing` graph; and the region SIZE is the
cycle's own shoelace area plus a correction that is the same for every shape — the midpoint
contour cuts each convex corner by 1/8 and fills each reflex corner by 1/8, and a simple
rectilinear polygon has exactly four more convex corners than reflex ones, so the total is always
4 x 1/8 = 1/2 however involved the outline. `cells = shoelace + 0.5`, read off the boundary.

| n | cells | crossings | union-find | cycles | speedup |
|---|---|---|---|---|---|
| 17 | 289 | 44 | 1.66 ms | 0.258 ms | 6x |
| 41 | 1681 | 116 | 9.11 ms | 0.678 ms | 13x |
| 57 | 3249 | 156 | 17.50 ms | **0.891 ms** | **20x** |

Scaling, from the smallest to the largest: cells x11.2, crossings x3.5, **union-find x10.5,
cycles x3.5**. Exactly the boundary's own growth rate, and contours identical at every angle
tested (max deviation 0.00e+00 at 0/15/30/45/90 degrees). Gated by
`test_the_contour_needs_no_field_scan_and_agrees_with_the_one_that_does` and
`test_the_contour_cost_follows_the_perimeter_not_the_area`; `_crossing_contours` is retained as
the ORACLE the fast path is checked against, so its O(area) cost is now deliberate.

**The medial axis: the cost fix worked, and then located a deeper error.** Blum defined the medial
axis as the centres of maximal inscribed circles, and every such circle is tangent to the
boundary — so it needs no field either. Closed form, no iteration: for boundary point p_i with
inward normal n_i, a circle tangent at p_i touching p_j has `r = |d|^2 / (2 d.n_i)` with
`d = p_j - p_i`, and the maximal inscribed circle is the SMALLEST such r. One vectorised pass.
Measured: **106x faster at n=57**, growing x3.6 against crossings x3.5 — linear, as intended.

But the ANSWER was wrong: the disc read r = 10.19 against a true 14.35. Three measurements
located it, and the third is the point:

  * an ANALYTIC circle returns r = 14.35 with spread 0.00 — the formula is exact;
  * the error is entirely the STAIRCASE contour;
  * widening the normal stencil saturates at 12.96 and makes the spread WORSE (12.52 -> 14.20).
    Local repair does not recover it.

This is the textbook instability of the medial axis to boundary noise — the reason the pruning
literature (lambda-medial axis, scale axis) exists at all. And the observation's medial does not
merely err, it **fails to converge**: its smear GROWS with resolution, 6.65 -> 9.56 -> 12.52 ->
18.05 across n = 25/33/41/57.

The fix is this arc's own thesis, "a circle has one point," applied one level on. Fit the contour
to its program — one closed-form algebraic least squares, linear in (D,E,F), no seed and nothing
to tune — and take the medial of the PROGRAM:

| n | observed r | observed spread | program r | program spread | fit residual | true R |
|---|---|---|---|---|---|---|
| 25 | 5.75 | 6.65 | 8.77 | **0.00** | 0.27 | 8.75 |
| 41 | 10.19 | 12.52 | 14.45 | **0.00** | 0.45 | 14.35 |
| 57 | 12.77 | 18.05 | 19.92 | **0.00** | 0.48 | 19.95 |

One point at every size, radius correct to 0.03, from a fit whose residual is sub-cell throughout.
**The medial axis of the observation is noise; the medial axis of the recognised shape is exact** —
so the noise was never there to be pruned, and the whole pruning apparatus is answering a question
that the program layer dissolves. The observed-vs-program split here is the same one already
measured for the verdict comparator ("bins propose, continuous decides"): the raster is what you
match against, never what you compute structure from.

**Honest residual:** the sub-cell contour was tested here and is INERT on these fixtures, not a
result — the synthetic raster is a hard mask, so both cells give t = 0.5 and it reduces exactly to
the midpoint placement. It needs the supersampled raster to say anything, and that was not run.

## 6g. WHAT THE SETTLE ACTUALLY IS — one irreducible read, and the flood's iteration on top

§6e's honest headline was that the settle dominates every geometric stage by 10-40x, which made
the geometry's constant factors the wrong thing to argue about. Measured, on one scene at five
sizes, in three configurations:

| n | cells | flood only | rim only | both | rim/flood |
|---|---|---|---|---|---|
| 16 | 256 | 4.3 ms | 3.9 ms | 6.4 ms | 0.89 |
| 32 | 1024 | 17.4 ms | 9.5 ms | 20.1 ms | 0.55 |
| 60 | 3600 | 58.9 ms | **28.9 ms** | 69.0 ms | **0.49** |

Scaling from n=16 to n=60, cells x14.1: **flood x13.6, rim x7.5.**

So the flood is O(area), and the rim is not O(perimeter) either — nor could it be. `bt_disagree`
has to test every `neighbour` edge in the field, because **you cannot find a boundary without
reading the observation at least once**, and that read is O(area) by definition. That cost is
irreducible and it is not a defect: it is what observing IS.

What separates the two is everything on top of that read. The flood iterates to fixpoint, so it
pays the area cost once PER PASS — O(area x iterations), and the iteration count is the region's
diameter. The rim pays it exactly once. Hence the ratio falling 0.89 -> 0.49 as the field grows,
and hence the rim's x7.5 against the flood's x13.6: the diffusion factor is what the boundary
representation removes, and the residual O(area) term is the one nobody can remove.

**The cost claim, stated completely, for the pipeline as it now stands:**

  * ONE O(area) pass to read the observation — irreducible;
  * everything structural after it is O(perimeter): contour cycles x3.5 against crossings x3.5,
    turning function flat, comparison flat at 2.15 -> 2.16 ms;
  * the medial axis is O(perimeter) too, and belongs to the fitted program rather than the raster
    (§6f).

**And a measured argument for finishing a job this arc left open.** Running the boundary rules
ALONGSIDE the flood costs 69.0 ms against the flood's own 58.9 — strictly worse than either path
alone, because the field gets scanned for both. `mo_flood` being "derived alongside, not replaced"
has been recorded as an architectural residual; it is now also a 2.4x cost against the rim path
with `mflood=0`. The tests already take the rim path (`_rim_run` sets `mflood=0.0`); production
callers still do not.

## 6h. THE ANTI-ALIASED EDGE — a threshold that provably does not exist, and why the CELL is the wrong carrier

§6f closed with an honest residual: the sub-cell contour had been tested only on a HARD MASK,
where both cells give t = 0.5 and it reduces exactly to midpoint placement, so it was inert and
"the medial belongs to the program" was concluded without it. Running the case it needed — a
supersampled raster, the partial coverage a real blurred observation carries — produced something
more interesting than a placement tweak.

**First, a correction to my own reading.** I initially reported the crossings COLLAPSING
116 -> 66 -> 43 under supersampling and read it as the soft edge going undetected. That was a
misread column: those were contour points on the largest cycle, not crossings. Measured properly,
the crossings go **UP**, 116 -> 212 -> 224 -> 220, which is what the gradient argument predicts.
What actually changes is the PARTITION:

| raster | crossings | regions | largest | 2nd | remainder |
|---|---|---|---|---|---|
| hard mask | 116 | **2** | 1024 | 657 | — |
| super x2 | 212 | 46 | 1008 | 621 | ~52 cells over 44 regions |
| super x4 | 224 | **50** | 1008 | 609 | ~64 cells over 48 regions |
| super x8 | 220 | 46 | 1008 | 629 | ~44 cells over 44 regions |

The disc never merges with the background, so this is NOT the single-linkage chaining already
retracted in §2a. It is a ring of **slivers averaging 1.2 cells each**.

**Second, and this is the load-bearing result: no single threshold exists.** Swept on the super x4
disc:

| mtol | regions | largest | 2nd | verdict |
|---|---|---|---|---|
| 0.5 | 82 | 992 | 593 | 80 sliver regions |
| 1.5 | 50 | 1008 | 609 | 48 sliver regions |
| 2.5 | 26 | 1008 | 649 | 24 sliver regions |
| 3.5 | 17 | **1665** | 1 | disc lost — merged |
| 4.5+ | 1 | **1681** | 0 | disc lost — merged |

Below 3.5 the disc separates but carries slivers; at 3.5 and above the slivers go and the disc goes
with them. **There is no value that yields two clean regions.** So this is not a badly chosen
number, and the seed's own Otsu derivation (`mo_tol_otsu`) cannot rescue it either — deriving a
threshold better does not help when the threshold being sought does not exist.

**Third, the mechanism, which says what to do instead.** The ramp is only ONE cell wide (measured;
max adjacent step stays 8.44 at x4 and 8.02 at x8, so the signal is not smeared away). A
partially-covered edge cell differs from the interior by more than `mtol` AND from the exterior by
more than `mtol` — so it is cut from BOTH sides. Its coverage varies around the circumference, so
no single threshold cuts it from exactly one side everywhere.

Which means the sliver is an artifact of demanding a **total partition of CELLS**. Every cell must
belong to some region, so a cell that is genuinely *on the boundary* has to have a region invented
for it. The crossing representation never required that — and the sub-cell parameter `t` is
precisely the quantity that says where WITHIN the cell the boundary falls. So sub-cell placement is
not the ~3% cosmetic rms improvement it measured as on a hard mask (0.403 -> 0.392 at x4,
0.386 -> 0.357 at x8); on a real observation it is **structurally what makes the edge cell
representable at all**.

This is §6f's finding one level down, and the same shape as it: **the observation alone
underdetermines, and the carrier decides what can be said.** A cell partition cannot express "the
boundary runs through here"; a crossing with a sub-cell `t` can. The number that was being sought
(one tolerance separating ramp from object) provably does not exist, which is this tree's standing
defect shape stated as strongly as it can be stated — a number standing where a shape belongs, and
measured to be impossible rather than merely awkward.

**Status when written:** measured and recorded, NOT built. **Since built** — §6i/§6j add
`bt_true_boundary` and `bt_subcell_t`, which discard the doubled chain and read the partial coverage
that a threshold cannot. `bt_disagree` is still a pairwise threshold and the adapters still take a
total cell partition; what changed is that neither is now load-bearing for accuracy on a soft edge.

## 6i. THE FIX §6h SAID WAS NEEDED — and anti-aliasing turns out to be INFORMATION

§6h established that no single threshold separates a soft edge, and that the sliver is an artifact
of demanding a total partition of CELLS. Both halves of the repair follow from that, and both are
measured. Neither introduces a number.

**Telling a region from a boundary band, structurally.** A real region contains at least one
INTERIOR cell — one with no `cuts` edge at all, agreeing with every neighbour. A one-cell-wide band
contains none, because every cell in it is cut on both sides. Measured across two shapes and four
raster levels, this finds **exactly 2 regions with an interior in all 8 configurations** (disc and
rectangle, hard through super x8), with the 8-48 remaining fragments having none.

*A correction made in passing, because it is this section's own defect shape appearing inside the
check for it:* the first verdict function demanded that slivers be <= 2 cells, which is a magic
number, and it failed an 11-cell band that is still one cell wide with no interior. The predicate
was right and my test of it was wrong. Region-versus-band is about HAVING an interior, not about
size.

**Recovering the true boundary without reinstating the flood.** An anti-aliased edge gives two
parallel crossing chains bracketing the band: `(interior | band)` and `(band | exterior)`. Only one
is the object's boundary, and choosing between them must not ask "which region is this cell in" —
that is the O(area x iterations) question the rim exists to remove. A LOCAL 2-hop predicate
suffices: a crossing is a true boundary iff its figure-side cell is interior, or is a `neighbour`
of an interior cell with no `cuts` between them.

| raster | crossings | true (2-hop) | dropped |
|---|---|---|---|
| hard mask | 116 | **116** | **0** |
| super x2 | 212 | **116** | 96 |
| super x4 | 224 | 108 | 116 |
| super x8 | 220 | 108 | 112 |

**Inert on a hard mask** (116 -> 116, nothing dropped), and it recovers the hard mask's own
crossing count from the doubled soft-edge set.

**And then the result that inverts the framing.** Placing the surviving crossing sub-cell gives a
boundary MORE accurate than the hard mask ever was:

| raster | placement | radial rms |
|---|---|---|
| hard mask | midpoint | 0.250 |
| super x2 | sub-cell | **0.140** |
| super x4 | sub-cell | **0.147** |
| super x8 | sub-cell | **0.135** |

**Anti-aliasing is INFORMATION, not noise** — ~1.8x more accurate than a hard mask, because partial
coverage says where inside the cell the edge falls and a hard mask has thrown that away.

*The anchor had to be corrected first, and the error is worth keeping.* The sub-cell formula
inherited from the earlier probe solves for the point where deviation reaches `mtol` — but `mtol` is
a DETECTION threshold, and using it as a LOCATION puts the edge at value 7.5, well inside the
object. It made the rms WORSE at every level (0.388 -> 0.470, 0.478 -> 0.504, 0.458 -> 0.486). The
edge is where the observation is halfway between the two levels it runs between, and both levels
are OBSERVED (the field's own extremes), not declared. Same defect shape as §6h, found inside the
fix for §6h.

**This QUALIFIES §6f, which is a committed claim and must not stand unamended.** §6f concluded "the
medial axis of the observation is noise; the medial axis of the recognised shape is exact" — but it
concluded that from a STAIRCASE contour, rms 0.250. On the accurate contour:

| contour | rms | medial r (true 14.35) | spread |
|---|---|---|---|
| hard, midpoint | 0.250 | 10.19 | 12.52 |
| super x4, midpoint | 0.478 | 9.25 | 12.02 |
| super x4, **sub-cell** | **0.147** | **13.22** | **4.34** |
| fitted program | — | 14.45 | **0.00** |

The observation's medial was not hopeless — it was reading a bad contour. A 3x better contour takes
it from 71% to 92% of the true radius and tightens the axis 2.9x. **§6f's direction holds — the
program is still markedly better, and only the program collapses the disc to a single point — but
its strength does not.** The honest statement is that the medial axis is highly sensitive to
boundary accuracy, not that the observation cannot support one.

**BUILT (v1.6.0): `bt_true_boundary`.** The discriminator is now a rule, not a probe:

```
[x owns_figure a], [a neighbour n],  Count(Neighbours(n, cuts)) < 1
  ->  set_attr x true_boundary 1.0
```

Two simplifications fell out of stating it as graph data. A crossing's figure cell ALWAYS has a cut
— that is what a crossing is — so it can never itself be interior, and the direct clause is dead;
the whole predicate is "does the figure cell have an interior NEIGHBOUR." And `cuts` is symmetric,
so a neighbour with zero cuts cannot be cut from `a` either, which retires the second guard. The
rule reproduces the Python probe's verdict EXACTLY at every raster level (116/116, 116/116,
108/108, 108/108 — set equality, not just counts).

Gated by three tests: inert on a hard mask (nothing dropped), the doubling-and-halving on a soft
edge asserted as a RATIO against the same disc's hard mask so it cannot go stale, and a structural
check that the rule stays 2-hop — its match binds only `owns_figure` and `neighbour`, it reads no
`mlabel`, and it expands `Neighbours` exactly once. 21/21 green. It adds no literal outside the
`{0.0, 0.5, 1.0}` set the seed's own no-new-constant gate already enforces.

**The sub-cell anchor was taken to the edge of shipping and STOPPED, on measurement.** It is the
other half of §6i's win, so it was sized properly rather than assumed, and two findings came out.

*The global anchor is a two-level assumption that degrades BELOW baseline.* Anchoring at the
halfway point between the field's global extremes is exactly right for one object on one
background and wrong the moment there are two objects at different values, because each boundary
runs between a DIFFERENT pair of plateaus and the global midpoint belongs to neither:

| scene | midpoint | global anchor | local anchor |
|---|---|---|---|
| one disc on 0.0 | 0.274 | **0.065** | **0.065** |
| two discs, 9.0 and 4.5, on 0.0 | 0.274 | **0.456** — worse than doing nothing | **0.065** |
| one disc on a RAISED 3.0 background | 0.274 | 0.065 | 0.069 |

Building the global version into a seed would have shipped a two-level assumption that silently
falls below the placement it replaced on any multi-object scene.

*And the "local" anchor is not local.* It scored 0.065, but replacing only its FALLBACK — the value
used when no far plateau is in reach — collapsed it to 0.271, barely better than the midpoint. That
gap says the fallback is the common path, not an edge case. Counted directly: **on a 0.0
background, 44 of 52 true crossings (85%) fall back**; on a raised background, 20 of 52 (38%). So
the formula was overwhelmingly returning a hard-coded 0.0, and its good score was a fact about
these fixtures' background being zero.

The structural reason is exact, and it is the same fact that makes `bt_true_boundary` work: the far
cell of a TRUE crossing IS the band cell, and a band cell's agreeing neighbours are other band
cells, which are never interior.

**CORRECTED BY §6j BELOW — the conclusion drawn here was wrong, and worth leaving visible.** This
went on to say the far plateau was therefore "3 hops away, through the band," and stopped. It is 2
hops: the search looked only among the band cell's AGREEING neighbours, and missed that the band
cell also has a CUT neighbour on the far side — the very crossing `bt_true_boundary` discards.
Searching one relation and concluding about reachability in general is its own error, distinct from
the anchor errors above. `bt_subcell_t` is built.

This is this document's own defect shape for the third time in one stretch — a number standing
where a shape belongs — found on this occasion inside a candidate fix for the previous two. Which is
the argument for the sizing step, not against the anchor: the measured 1.8x accuracy is real and
still on the table.

### 6j. BUILT AFTER ALL — the far plateau is 2 hops across the band, not 3 around it

The sizing above concluded the far plateau was 3 hops away and stopped. That was wrong in a useful
way: it searched among the band cell's AGREEING neighbours, which are other band cells. But the
band cell also has a CUT neighbour on the far side — precisely the crossing `bt_true_boundary`
discards. **The discarded chain is what locates the edge on the kept one.**

```
I --cut-- P --cut-- E        a = I (figure), b = P (band), e = E (far plateau)
```

One case remains: where the band has drifted close enough to the far side that no crossing forms
there, the far plateau is reached over AGREEMENT instead. The two cases are complementary, and
since ownership is by magnitude — so `a` is always the higher side — the far plateau is always the
LOWEST-magnitude lattice neighbour of `b` other than `a`. That covers both without distinguishing
them, and needs no union, no fallback, and no background:

| scene | midpoint | global anchor | crosscut only | **neighbour minimum** |
|---|---|---|---|---|
| one disc on 0.0 | 0.274 | 0.065 | **0.061** | 0.084 |
| two discs, 9.0 and 4.5 | 0.274 | 0.456 | 0.189 | **0.084** |
| disc on a raised 3.0 background | 0.274 | 0.065 | 0.260 | **0.084** |
| fallbacks needed | — | — | 16–31% | **0 everywhere** |

**0.084 on all three, identical** — the constancy is itself the evidence, since it says the residual
is the quantization floor rather than a fit to any scene. It gives up 0.023 against `crosscut` on
the easiest case and is the only anchor with nothing assumed.

**`bt_subcell_t` (v1.7.0):** `t = 0.5 * (|a| - far) / (|a| - |b|)`, over `MinOver` of `b`'s lattice
neighbours excluding `a`. Verified to reproduce the probe from the graph — 0.084 on all three
scenes, `subcell_t` present on every true crossing, `t` in [0.50, 1.00].

*The seed's own no-new-constant gate caught the first draft*, which wrote the halfway factor as a
bare `2.0`. The quantity is algebraically `0.5 * (|a| - far) / (|a| - |b|)`, which keeps the seed's
only literals the `{0.0, 0.5, 1.0}` it admits. A gate earning its keep on the rung that added it.

Gated by three tests: `t` written on every true crossing and inside [0,1]; sub-cell beating the
midpoint by better than 2x, asserted as a RATIO so it cannot go stale; and — the one that matters —
**accuracy holding on a raised background AND beside a second object at a different value**, which
is exactly what the three discarded anchors failed. 24/24 green.

### 6k. `bt_true_boundary` HAD THE WRONG DISCRIMINATOR — measured on hard masks, fixed, and the gate that missed it replaced

The rule as first built (v1.6.0) asked whether the figure cell had a fully-INTERIOR neighbour — one
with no `cuts` at all — as a proxy for "is a plateau". That is right for large smooth shapes and
wrong for anything thin, because `neighbour` is 4-connected and a block's corner cell is DIAGONAL
to its interior. Measured on HARD MASKS, where nothing should ever be discarded:

| object | crossings | kept (v1.6.0) | dropped |
|---|---|---|---|
| 1x1 | 4 | **0** | **all** |
| 2x2 | 8 | **0** | **all** |
| 1x9 bar | 20 | **0** | **all** |
| 2x9 bar | 22 | **0** | **all** |
| 3x3 | 12 | 4 | 8 |
| 5x5 | 20 | 12 | 8 |
| 13x13 | 52 | 44 | 8 |

**Any object under three cells thick was deleted outright**, and four corners were lost from every
rectilinear shape at every size (the constant 8 is the four corners' two crossings each).

*The gate that shipped it was too weak, and the reason is instructive.*
`test_the_true_boundary_rule_is_inert_on_a_hard_mask` used a large DISC, and every figure cell of a
disc DOES have an interior neighbour — so the fixture could not fail. A gate that only exercises the
regime a rule was designed in cannot find the regime it breaks in.

**The right discriminator is the VALUE, and it is one hop, not two.** The figure cell of a crossing
is by definition the higher of its two sides (`bt_own` owns the stronger). So if anything ELSE cuts
that cell from ABOVE, it is not a plateau — it is a middle layer, a band, and its outward crossing
is the spurious chain:

```
(interior | band): figure is the interior cell; nothing cuts it from above  -> TRUE
(band | exterior): figure is the band cell, cut from above by the interior  -> FALSE
```

One `MaxOver` over the figure cell's own `cuts`, no pair enumeration, no interior concept, and the
match dropped from two hops to one. Measured: **100% kept on every hard-mask object above**,
1x1 and thin bars included, and **byte-identical to the interior test on the soft-edge cases the
rule exists for** — 116/116 at x2, 108/108 at x4 and x8. The fixtures elsewhere in the gate recover
their full boundaries too (three blocks 18 -> 42 crossings, corner contact 16 -> 32, hard annulus
48 -> 56). Strictly dominant; there is no case where the interior test was better.

An intermediate predicate was also measured and is worth naming as unnecessary: "the cell's value
lies strictly BETWEEN two OPPOSING cut-neighbours", opposing in the sense `bt_chain_perpendicular`
already uses (their only common neighbour is the cell itself). It gives identical verdicts in every
case tested, and the simpler one-hop test is preferred precisely because it needs no pair
enumeration and no opposing test.

Gated by `test_no_object_loses_its_boundary_however_thin_it_is`, which sweeps 1x1 through 13x13 plus
the two thin bars — the test that would have caught this. **v1.8.0, 26/26 green.**

**And a property worth having, now gated:** `subcell_t` is EXACTLY 0.5 on a hard mask, not
approximately — with no band, `b` IS the far plateau, so `far == |b|` and
`t = 0.5(|a|-|b|)/(|a|-|b|)`. Verified as equality (deviation 0.00e+00) across five hard-mask
scenes including a three-level annulus. Every existing fixture in this tree is a hard mask, so a
consumer can adopt `subcell_t` unconditionally and get bit-for-bit the midpoint it had before, with
the accuracy appearing only where there is partial coverage to read.

### The chain-after-filter residual, narrowed — and one repair refuted

The residual recorded as "at super x8 only 26 of 108 surviving crossings chain into one cycle" is
real but much narrower than that phrasing suggests. Measured across raster levels, on the true
crossings only:

| raster | true | deg 0 | deg 1 | deg 2 | deg >2 | components | largest |
|---|---|---|---|---|---|---|---|
| hard mask | 116 | 0 | 0 | **116** | 0 | **1** | 116 |
| super x2 | 116 | 0 | 0 | **116** | 0 | **1** | 116 |
| super x4 | 108 | 0 | 0 | **108** | 0 | **1** | 108 |
| super x8 | 108 | 4 | 8 | 96 | 0 | 8 | 26 |

**Hard, x2 and x4 are perfect** — 100% degree-2, a single cycle, nothing to repair. Only x8 breaks,
and there 12 of 108 crossings (11%) are under-connected.

**The cause first recorded here — "some segments have a TWO-cell band" — is WRONG, and the real one
is more interesting.** Every under-connected crossing was inspected: all twelve sit on a ONE-cell
band, and all twelve are at the four CARDINAL points of the disc, where the boundary is tangent to
the lattice and the partial cell's coverage is therefore highest. Reading the column strip across
the disc's top, with `mtol` 1.5 so a partial cell agrees with a 9.0 interior once its value exceeds
7.5:

| col | v(partial) | cut 5\|6 | cut 6\|7 | the partial cell is | TRUE boundary at |
|---|---|---|---|---|---|
| 18 | 6.3 | yes | yes | a BAND | rows 6\|7 |
| 19 | 7.3 | yes | yes | a BAND | rows 6\|7 |
| **20** | **7.9** | yes | **no** | **part of the figure** | **rows 5\|6** |
| 21 | 7.3 | yes | yes | a BAND | rows 6\|7 |
| 22 | 6.3 | yes | yes | a BAND | rows 6\|7 |

At the exact top of the disc the partial cell is 88% covered, so it AGREES with the interior and is
absorbed into the figure — and the detected boundary steps one cell outward for that single column.
Its neighbours either side have the boundary a row further in. No chaining rule links two crossings
that are a row apart, share no cell, and have no corresponding pair. Four cardinal points give 4
isolated crossings, each costing its two neighbours a link: 4 + 8 = the 12 observed, exactly.

**So this is not a chaining defect, and repairing it in the chaining rules is treating a symptom.**
It is the pairwise threshold in `bt_disagree` — §6h's "no single threshold works" appearing as a
chain break rather than as slivers. Whether the partial cell counts as figure or as band flips as
its coverage crosses `9 - mtol`, and the boundary moves a whole cell when it does. `bt_true_boundary`
is doing the right thing with the cuts it is handed; the cuts are what is wrong. This residual
therefore belongs to the one piece this arc has consistently named as unbuilt, and closes only when
that does.

**A repair was proposed, measured, and REFUTED.** Link two true crossings whose FIGURE cells are
lattice neighbours — weaker than cell-pair correspondence, so it should still link across a 2-cell
band. It fails both ways at once:

| raster | | deg 2 | deg >2 | components |
|---|---|---|---|---|
| hard mask | as-is | **116** | 0 | 1 |
| hard mask | with repair | 68 | **48** | 1 |
| super x8 | as-is | 96 | 0 | 8 |
| super x8 | with repair | 64 | 32 | **8** |

It OVER-links where the chain was already perfect — a hard mask loses 48 crossings to degree > 2,
destroying exactly the unambiguous-successor property the two chaining rules were built to give —
and it does not reach the broken crossings at all: the isolated ones stay isolated and the component
count does not move. Figure-cell adjacency is both too permissive and insufficient. Not built, and
recorded so the next attempt does not retry it.

**Still not built:** `bt_disagree` remains a pairwise threshold. Two residuals stand: at super x8 only 26 of the 108 surviving crossings chain into one cycle
(the chaining rules link true crossings to dropped ones, and the chain is not re-derived among the
survivors), and the rectangle's cell count drops 65 -> 33 under supersampling because the boundary
band is excluded from the region — the extent has to come from the sub-cell contour, not from
counting cells.

## 6b. PRIOR ART
## 6b. PRIOR ART — nearly all of this is textbook, and one match is exact

Recorded because the document above reads like discovery and mostly is not. Each mechanism, with
its actual name:

| used here | known as |
|---|---|
| turning function psi(s), compared over cyclic shift and constant offset | **Arkin, Chew, Huttenlocher, Kedem & Mitchell (1991)**, *An Efficiently Computable Metric for Comparing Polygonal Shapes*, IEEE TPAMI 13(3) — the L2 distance between turning functions, invariant to translation, rotation and scale, O(mn log mn). This is not an analogue of what I built; it **is** what I built. |
| boundary as `cuts` between cells, chained into a contour | crack following / Moore boundary tracing / Freeman chain codes — standard contour extraction |
| RDP polyline simplification | Ramer (1972), Douglas & Peucker (1973) |
| `ScTpsDist` | shape contexts + TPS, Belongie, Malik & Puzicha (2002) — already a Term in this substrate |
| render the hypothesis through the same sampling, compare | analysis-by-synthesis / render-and-compare / vision as inverse graphics; also this repo's own AbS rung |
| holding a generator and recognising orbit membership | group-equivariant recognition; orbits under a transform group |
| fold order from self-similarity of the turning function | symmetry detection by autocorrelation of a shape signature |
| dead ends as hairpins; solving by collapsing them | **dead-end filling**, a standard maze algorithm; and wall-following |

Two specifics worth flagging rather than glossing:

- **The maze failure was a known precondition, not a bug.** Wall-following is guaranteed only when
  the maze is *simply connected* — all walls joined to each other or to the outer boundary. My test
  maze had free-floating interior blocks, so its free space was multiply connected, its boundary was
  several cycles, and one trace covered 36 of 72 crossings. That is the documented limit of the
  method, arrived at the slow way.
- **The Wikipedia maze-solving article states the boundary result directly**: *"By grouping together
  connected components of the maze walls, the boundaries between these are precisely the
  solutions."* That is the same claim as this document's crossing-boundary construction, in one
  sentence.

**What is NOT inherited from that literature** is the part specific to this substrate, and it is
the part worth keeping: which of these primitives the engine already held and had never composed
(`ScTpsDist`, `DtwTo`, `StrokeQuantize`, the sd loop); that `mo_flood` diffuses a label where a
boundary would do, with pass counts measured both ways; that Stage A dies on exactly that flood;
the coverage figures for generator-vs-exemplar on this engine; and the chaining defect that only a
turning boundary exposes. The mechanisms are borrowed. The measurements are not.

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
| both rules, v1.3.0 | 39/60 = 65% | **0** | 15 |
| both rules, **v1.5.0 (current)** | **41/60 = 68%** | **0** | **6** |

Zero isolated crossings, and the residual degree-3/4 are genuine saddles left VISIBLE as degree
rather than resolved by a hidden convention. Filtered to a single region's boundary they vanish
entirely — the branches are between regions.

**UPDATED 2026-08-23, and the "15 saddles" figure quoted downstream is stale.** The v1.3.0 row was
measured before `bt_chain_perpendicular` was corrected to link only ADJACENT sides at a shared
cell (it had been linking all pairs there, including opposite sides — a chord straight across the
rim, invisible on axis-aligned shapes). Re-running the same parallax fixture on the current seed:
**saddles 15 -> 6**, degree-2 65% -> 68%. The remaining 13 degree-1 crossings are field-edge
truncation, not chaining failures — the parallax regions run off the border.

And the last sentence above, which was an inference at the time, is now measured directly. Four
single-region shapes, current seed:

| scene | crossings | degree-2 | deg>2 | deg<2 |
|---|---|---|---|---|
| three blocks (the gate fixture) | 42 | **42** | 0 | 0 |
| disc r=8 | 68 | **68** | 0 | 0 |
| diamond, every edge diagonal | 60 | **60** | 0 | 0 |
| two blocks touching at a CORNER | 32 | 28 | **4** | 0 |

**100% degree-2 on every simple closed region, including the all-diagonal diamond** — so the
branching is entirely between regions, as claimed. The one scene that does branch is two blocks
meeting at a corner, and that ambiguity is REAL: whether the blocks connect through the corner is
the classic marching-squares saddle, and it is not decidable from adjacency alone. Leaving it
visible as degree is therefore the correct behaviour, not an unfinished one.

The tie-break is now gated rather than carried as a caveat. Measured on the corner fixture before
any assertion was written: **both walks resolve the four ambiguous crossings the same way, and
both resolve them correctly** — two separate closed contours of 16 cells each, the blocks kept
apart. Pinned by `test_both_walks_agree_where_the_boundary_graph_is_genuinely_ambiguous`, which
also asserts the fixture still produces 4 saddles so it cannot go quietly inert.

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

> **RE-CHECKED, AND THIS ONE STRENGTHENS.** The table above used absolute `ScTpsDist` on pre-fix
> contours. Re-run with the chaining fix and the canonical L2 turning metric:
>
> | | midpoint | sub-cell | |
> |---|---|---|---|
> | soft 15 deg | 0.3248 | **0.1834** | −44% |
> | soft 30 deg | 0.2467 | **0.1110** | −55% |
> | soft 45 deg | 0.1592 | **0.0599** | −62% |
> | soft 90 deg | 0.0514 | **0.0387** | −25% |
>
> On a soft edge sub-cell placement now roughly **halves the distance at every rotation**, rather
> than helping at three angles of four. On a hard mask it stays mixed and small, which is the
> prediction: a hard mask carries no sub-cell information for any fit to recover, and no
> improvement in the comparison can manufacture it.
>
> **Four pre-fix claims have now been re-checked: three retracted, this one strengthened.** The
> pattern is not that everything measured before the fixes was wrong — it is that anything
> measured through a broken contour or a rotation-blind metric was unsafe in EITHER direction, and
> the only way to know which was to re-run it.

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

### POWERED, and the thin margin does not survive

The margin above — 0.1127 against 0.1486, 1.3x — was **one synthetic pair**, which is exactly
what this repo's own rule (*power the gate before the endgame*) exists to catch. Measured properly
across 5 shapes x 7 angles, 32 contours, 88 same-shape and 408 different-shape pairs:

```
within-shape  : median 0.2205   max 0.5995
between-shape : median 0.3383   min 0.0594
74 of 88 within-shape distances exceed the SMALLEST between-shape distance
best single threshold misclassifies 14.3%
```

**It does not separate.** Nor is that an artifact of two awkward shapes: excluding the
rotationally symmetric square (whose principal axis is degenerate, so canonicalisation has
nothing to find) leaves 18.8% error, and excluding the rect/ellipse pair as well still leaves
14.1%.

The cause is complete and it inverts the decomposition above. Within-shape distance is explained
almost entirely by **how far the rotation sits from an exact lattice rotation**:

| offset from a multiple of 90 | pairs | median distance |
|---|---|---|
| 0 (exact) | 4 | **0.0026** |
| 15 | 34 | 0.1463 |
| 30 | 33 | 0.2926 |
| 45 | 17 | 0.3093 |

**85x between exact and oblique, monotone in offset.** So pose alignment works essentially
perfectly where the lattice renders the rotation faithfully, and the entire residual is grid
damage — which at 45 degrees exceeds most between-shape distances outright.

### The absolute frame was still smuggled in — and removing it does not save it either

Everything above compares dense point lists in CELL COORDINATES and then asks a point-set metric
to undo the frame. That still carries an absolute reference. A closed contour's intrinsic content
is a cyclic sequence of **(turn, edge length)**: translation does not appear because no positions
are stored, rotation does not appear because turns are relative to the previous edge, scale is
one global factor removed by normalising against the perimeter, and the only residual freedom is
where the cycle starts and which way it runs. That is also what `StrokeQuantize`'s `seg`
relations always were — and they were being fed absolute points.

Built and measured on the same 5 shapes x 7 angles:

| representation | pairs | misclassified |
|---|---|---|
| absolute points, `ScTpsDist` | 496 | 14.3% |
| intrinsic (turn, length), equal vertex counts only | 65 | **4.6%** |
| intrinsic, held `DtwTo` over ALL pairs | 276 | **15.9%** |

The middle row is a **3x improvement that does not survive its own coverage**. Requiring equal
vertex counts silently skipped 71 of 88 within-shape pairs — and those are exactly the hard ones,
because **vertex extraction is itself unstable under rotation**: the same rectangle simplifies to
`[4, 6, 6, 4, 6, 3, 4]` vertices across seven angles. Comparing only the pairs where extraction
happened to agree is an easy subset by construction, and this repo's standing rule says the
subset is part of the claim. Using the held `DtwTo`, which tolerates differing lengths, restores
the hard cases and the advantage evaporates.

### Same SHAPE, not same bytes — the turning function, and an honest null

Requiring equal vertex counts is demanding BYTE correspondence, not shape identity: a straight
edge sampled with two points or twenty is the same edge, and a spurious collinear vertex has
turn ~0 and contributes nothing. The object blind to that is the cumulative **turning function**
phi(s) — turn accumulated against normalised arc length. Inserting a collinear vertex does not
change it at all; rotation is a constant offset; scale vanishes under arc-length normalisation;
the residual freedom is a cyclic shift. No vertex extraction, no RDP, no threshold on what counts
as a corner.

Built, with two implementation bugs found by control rather than by inspection — the closing turn
was dropped (so phi never reached 2pi) and a non-periodic ramp was being smoothed with circular
padding. Corrected, the controls look spectacular:

```
self                : 0.0000
rect@0 vs rect@90   : 0.0281      (exact lattice rotation)
rect@0 vs rect@45   : 0.0293      (oblique, maximal staircase)
rect@0 vs square@0  : 0.2348      (different shape, 8x)
```

45 degrees as close as 90 degrees — the grid damage apparently gone.

**It is not.** Those are the two BEST pairs for that shape; the rectangle's median across all its
valid pairs is **0.1864**, six times worse. Quoting the controls as the result would have been the
same single-sample error this document has already recorded twice.

The full series, on 5 shapes x 7 angles:

| representation | coverage | misclassified |
|---|---|---|
| absolute points, `ScTpsDist` | 496 pairs | 14.3% |
| intrinsic, equal vertex counts only | 65 (26%) | 4.6% — invalid subset |
| intrinsic + held `DtwTo`, all | 276 | 15.9% |
| turning function, all | 496 | 14.9% |
| turning function, closed curves only | 253 | **13.0%** |
| turning function, reliably-extracted shapes | 136 | 19.9% |

**No representation tried removes the grid damage, and the spread between them (13–16%) is not a
result.** Coordinate-free helps at the margin and only when the contour is a valid simple closed
curve — and 9 of 32 extractions are not one, accumulating ~0 total turning instead of 2pi.

> **SUPERSEDED — the null was an extraction artifact.** Every figure in the table above was
> measured BEFORE the `bt_chain_perpendicular` adjacent-sides fix, when a boundary that turned
> produced chord shortcuts and roughly a third of the contours were invalid. Re-run on corrected
> extraction, 35 contours instead of 32, same 5 shapes x 7 angles, 595 pairs:
>
> | representation | misclassified |
> |---|---|
> | absolute coordinates, `ScTpsDist` | 12.8% |
> | turning function, L1 (my variant) | 8.2% |
> | turning function, **L2 — Arkin et al. as defined** | **6.6%** |
>
> **Coordinate-free beats absolute by roughly 2x**, which is what the theory says and what the
> broken contours were hiding. Two corrections compound: the chaining fix alone took the turning
> function from 14.9% to 8.2%, and then using the metric as its authors define it took it to 6.6%.
>
> My variant minimised **L1** while still subtracting the **L2-optimal** offset — the closed-form
> mean difference is optimal for the squared norm, not the absolute one, so the offset I removed
> was not the best one for the quantity I was measuring. That is the direct payoff of checking the
> prior art rather than continuing to re-derive: the canonical form was better than my variant,
> and the reason was a norm/offset mismatch I would not have found by inspection.

### The answer is not a shape, it is a MANIFOLD

Every measurement above compares two rasterisations as if they were two objects. They are two
POINTS ON ONE FAMILY — the orbit of a single object under the transform group. What should be
held is not a picture but a **generator**, and recognition is **membership in the reachable set**,
not equality with a stored sample.

That also dissolves the grid problem instead of fighting it, and the mechanism is structural
rather than statistical. **The staircase is not removable — ten measurements say so — but it IS
REPRODUCIBLE.** Render the hypothesis through the SAME sampling the observation went through and
both sides carry the same damage, so it cancels. Measured: when a candidate angle matches the
observed angle, the distance is **exactly 0.0000**, because the render and the observation are
the same raster. Comparing against a stored picture fights the grid; comparing against a rendered
hypothesis never encounters it.

This is the repo's own AbS result — `StrokeRender` as `StrokeQuantize`'s exact inverse,
*propose, render, compare* — arriving independently at region boundaries.

Apples-to-apples, 5-way nearest-hypothesis classification of observations at angles no hypothesis
was stored at (7/22/38/53/68 degrees, none in the candidate set):

| held representation | correct |
|---|---|
| ONE stored exemplar (a picture at 0 degrees) | 11/21 = 52% |
| RENDERED ORBIT (a generator, sampled) | **14/21 = 67%** |
| chance | 20% |

**Power, stated rather than buried:** n=21, so one observation is 4.8pp and the 15pp delta is
3.1x the per-episode step — right at this repo's own bar for what counts as a result. Supporting,
not established.

### A close-enough guess that context can improve IS a win

Hard 5-way accuracy is the wrong question to ask a proposal layer. The right one is whether the
truth SURVIVES into a small candidate set, because a later stage can convert that and cannot
recover what was dropped. Measured on the same 21 observations:

| held | cov@1 | cov@2 | cov@3 |
|---|---|---|---|
| one stored exemplar | 52% | 62% | 71% |
| **rendered orbit** | **67%** | **86%** | **95%** |

**The orbit keeps the truth in the top three 95% of the time.** As a proposer it is close enough

> **RE-CHECKED ON CORRECTED CONTOURS, AND THIS CLAIM DOES NOT SURVIVE AS STATED.** The table above
> was measured before the `bt_chain_perpendicular` fix AND with absolute `ScTpsDist`, a
> rotation-VARIANT comparison. Re-run with corrected extraction and the canonical L2 turning-
> function metric, same 25 off-manifold observations:
>
> | held | cov@1 | cov@2 | cov@3 |
> |---|---|---|---|
> | one stored exemplar | **100%** | 100% | 100% |
> | rendered orbit | **100%** | 100% | 100% |
>
> Both saturate, so the test can no longer tell them apart — and the reason is theoretical rather
> than lucky: **the turning function is rotation-invariant by construction, so an orbit of
> rotations collapses toward a point in that representation and a single exemplar already covers
> it.** Most of what the orbit was buying was compensation for a metric that could not see through
> rotation.
>
> It is NOT redundant in principle, and the measurement says so: the worst within-orbit spread
> (0.3916, `ell`) still EXCEEDS the closest between-shape distance (0.3346, rect vs ellipse), so a
> harder test could separate them. I have not run one that does. What stands is the coverage
> ARGUMENT — accuracy is recoverable downstream and coverage is not — not the specific advantage
> claimed for the orbit here.
essentially always, even where its top-1 is wrong a third of the time.

And context does convert it. The cheapest context available is MORE LOOKS — several observations
of the same object at different angles, evidence summed, no single look needing to be right
(every subset of L looks is a trial, so the trial count scales rather than sitting at n=5):

| looks | trials | exemplar | orbit |
|---|---|---|---|
| 1 | 21 | 52% | 67% |
| 2 | 40 | 68% | **82%** |
| 3 | 40 | 75% | **88%** |

**67% to 88% on three looks**, with the orbit holding +13 to +15pp at every level. Both
representations improve with context — that is what context is for — but the orbit starts higher
and stays ahead, and it converges toward its own coverage ceiling rather than past it.

### SNAPPING: enumerate the orbit, do not sample it

The candidate set was spaced every 15 degrees — an arbitrary grid laid over a family that is not
continuous in observation space. The orbit is DISCRETE, and its cardinality is set by the
sampling, not by angular precision. Sweeping one degree at a time and deduping on the raster
gives the reachable set exactly:

| shape | 180 angles collapse to |
|---|---|
| square_6 | **9** distinct rasters |
| ellipse | 40 |
| rect_9x4.5 | 56 |
| ell | 104 |
| triangle | 122 |

A 6x6 square has nine distinguishable orientations at this resolution — it is symmetric AND
small, so almost every rotation is below the lattice's resolving power. Deduping happens on the
raster before settling, so only genuinely distinct members cost work.

With candidates snapped to that set:

| candidates | cov@1 | cov@2 | cov@3 |
|---|---|---|---|
| 15-degree grid | 67% | 86% | 95% |
| **snapped, observation ON the manifold** | 100% | 100% | 100% |
| **snapped, observation OFF the manifold** | **74%** | **91%** | **100%** |

The on-manifold row is near-tautological and is reported as such: a 1-degree sweep contains the
observation's own angle, so 21/21 match at distance exactly 0. It establishes the ceiling, not
the capability. **The off-manifold row is the real result** — the observation is 8% larger than
anything held, so only 1 of 23 has an exact match, and snapping still gains +7pp at rank 1 and
closes coverage@3 to 100%.

So the missing piece was not a better metric or a better representation: it was that the
candidate set must BE the reachable set. Sampling a discrete family on an arbitrary grid puts
candidates where no member exists and leaves gaps where members do.

### When does the manifold matter? A better sensor makes it matter MORE

If the orbit's advantage were merely compensation for a coarse lattice, it should shrink as
resolution rises — a finer grid renders a rotation more faithfully, so one stored picture should
start to suffice. Measured across four grid resolutions, 3 shapes x 5 off-manifold angles per row
(15 observations, so one observation is 6.7pp):

| grid | orbit sizes | exemplar cov@1 | orbit cov@1 | delta |
|---|---|---|---|---|
| 13 | [44, 14, 24] | 64% | 79% | +15 |
| 19 | [72, 34, 28] | 73% | **100%** | +27 |
| 25 | [108, 52, 72] | 80% | 87% | +7 |
| 33 | [156, 74, 104] | 47% | **93%** | **+46** |

**The opposite happens.** The exemplar does not improve with resolution and is WORST at the
finest grid tested, while the orbit stays at 93%. The mechanism is in the second column: orbit
size grows monotonically with resolution (44 -> 72 -> 108 -> 156 for one shape), because a finer
lattice RESOLVES MORE OF THE ORBIT — rotations that collapsed to one raster at grid 13 become
distinct at grid 33. So one stored exemplar covers a shrinking fraction of a growing family.

**A better sensor increases the need for a generator rather than removing it.** That is the

> **RETRACTED.** This was measured with absolute `ScTpsDist`, a rotation-VARIANT comparison, on
> pre-fix contours. Its own stated mechanism predicts the retraction: if the effect is that a finer
> lattice resolves more orbit members, then under a rotation-INVARIANT representation those members
> collapse to nearly one signature and the effect must vanish. Re-run with the canonical L2
> turning-function metric:
>
> | grid | distinct rasters | exemplar | orbit |
> |---|---|---|---|
> | 13 | [44, 14, 24] | 87% | 100% |
> | 19 | [72, 34, 28] | **100%** | 93% |
> | 25 | [108, 52, 72] | **100%** | 100% |
> | 33 | [156, 74, 104] | **100%** | 100% |
>
> **The exemplar IMPROVES with resolution and then holds**, rather than collapsing to 47%. The
> orbit's dip at grid 19 is one observation of fifteen. So the opposite of the claim is what the
> evidence supports: with an invariant representation a better sensor makes a single exemplar
> SUFFICIENT, and the generator is not needed for rotation at all.
opposite of the intuition that finer sampling makes matching easier, and it follows directly from
the orbit being discrete: resolution does not reduce the damage, it increases the number of
distinguishable members you must cover.

Honest limits: 15 observations per row, so the non-monotone exemplar column (64/73/80/47) carries
real noise, and the orbit advantage — present at every resolution, +7 to +46pp — is the claim,
not the individual figures. One shape family, one comparator.

### A circle has one point: shapes are PROGRAMS, and the codebook is tiny

The orbit enumeration above stores 156 rasters of a square. That is the wrong cost model, and
the reason is the same "bytes not shape" error one level up: **a slightly deformed square is not a
different shape, it is a square with a residual.** So the codebook should hold a handful of
PRIMITIVES, and everything else is (primitive, pose, residual). A pie chart is not ten bite
shapes; it is a circle with blocks taken out of it.

That also says what a primitive IS: a **program** of straight and curved connections, not a point
list. **A circle has one point** — one arc, constant curvature, closed. A square has four lines.
Storing 100 boundary samples for a square and 27 for a circle is storing the sampling.

Fitted directly — greedy segmentation of a contour into maximal line and arc pieces:

| primitive | contour points | program | pieces |
|---|---|---|---|
| square | 100 | **4 lines** | 4 — minimal |
| circle | 100 | **1 arc** + 1 line | 2 — minimal is 1 |
| triangle | 92 | 2 arcs + 3 lines | 5 — minimal is 3 |

**A square is recovered as exactly four lines, and a circle as one arc, from 100 boundary points
each.** The program is the shape; the point list was the sampling.

#### BISECT rather than walk

Greedy fitting extends a piece forward from an arbitrary start, so the segmentation depends on
where the walk began — an absolute reference smuggled back in — and it cannot fold its final
piece into its first, which is exactly the circle's trailing `line`. **Bisection splits at the
point of maximum deviation**, a property of the curve rather than of the traversal, and is
coarse-to-fine: try the whole closed curve as ONE primitive first and split only where the
residual demands. That is the substrate's own decode/residual/refine shape, and it yields a valid
description at every depth instead of only at the end.

| primitive | greedy | bisect | minimal |
|---|---|---|---|
| square | 4 line | 4 line | 4 |
| circle | 1 arc + 1 line | **1 arc** | 1 |
| triangle | 2 arc + 3 line | 6 line | 3 |

Bisection gets the circle exactly right and the wrap remnant disappears, ties on the square, and
is WORSE on the triangle. Reported rather than tuned away.

**The tolerance is not a magic number — it is the observation resolution.** Sweeping it:

| tol (cells) | square | circle | triangle |
|---|---|---|---|
| 0.6 | 4 line | **4 arc** | 6 line |
| 0.9 | 4 line | **1 arc** | 6 line |
| 1.2 | 4 line | 1 arc | 6 line |
| 1.6 | 4 line | 1 arc | 1 arc + 3 line |

Below about one cell the circle FRAGMENTS into four arcs — the fit is chasing staircase noise
that carries no information. At one cell and above it is a single arc. So the knob is set by what
the sampling can actually resolve, which is derivable rather than chosen, and asking for sub-cell
fidelity from a hard raster buys fragments (the same conclusion the sub-cell section reached from
the other direction).

#### FOLDING, not bisecting — bisection still chooses a split

Bisection picks a split point and "into two" is a chosen number. **Folding picks nothing**:
compare the shape against shifts of ITSELF and read off where it coincides. What survives is the
FUNDAMENTAL DOMAIN plus the fold group, both measured. It is also the exact sense in which a
circle has one point — every rotation maps a circle to itself, so its fundamental domain is a
single point and the description is "this point, repeated".

The instrument is already built: the turning function psi(s), periodic and free of position,
rotation and scale, compared against cyclic shifts of itself. Scoring integer candidate ORDERS
(a true N-fold shape coincides at every multiple of M/N, so the score is the worst of those)
rather than thresholding the profile:

| shape | N=2 | N=3 | N=4 | N=5 | verdict |
|---|---|---|---|---|---|
| square | 0.00 | 0.89 | **0.00** | 0.96 | 4-fold |
| circle | 0.00 | 0.83 | **0.00** | 0.71 | 4-fold |
| ellipse | **0.00** | 0.84 | 0.75 | 0.89 | 2-fold |
| triangle | 0.99 | **0.32** | 0.99 | 0.97 | 3-fold |
| pentagon | 0.95 | 0.96 | 0.95 | **0.51** | 5-fold |

**All five correct**, reading the LARGEST N with a near-zero score — a 4-fold shape is also
2-fold, so the smallest coincidence is a subgroup and reporting it was my error, not the
detector's. A first attempt thresholded the self-distance profile at `0.12 * max`, which is
itself a magic number and duly failed: it matched shift +/-1 on every shape, which is smoothness
rather than symmetry.

**The circle reads 4-fold, not continuous, and that is correct** — a circle rasterised on a
square lattice IS 4-fold symmetric. The detector reports the observation, not the intent.

#### Folding tracks IRREGULAR shapes, not just symmetric ones

Folding a shape against itself finds symmetry; folding one observation against the NEXT finds
correspondence, and that needs no symmetry at all. The cyclic shift minimising the distance IS the
motion between looks — no feature matching, no point-correspondence search, cost linear in the
boundary description rather than quadratic in points.

Measured on irregular blobs (random radial lobes, no symmetry to exploit):

| rotation between looks | median angular error | best-shift residual vs mean |
|---|---|---|
| large (23, 57 degrees) | 48.2 degrees | 0.28-1.14 vs 0.53-1.30 — no clear minimum |
| frame-to-frame (3-12 degrees) | **11.2 degrees** | 2-3x below mean — a real minimum |

Chance is ~90 degrees, and one fold-match costs **2.8 ms** over a 78-point boundary.

Large jumps fail for the reason everything else in this document fails: a blob rotated 23 degrees
is a DIFFERENT RASTER. Frame to frame it works, coarsely — the error is comparable to the
rotation itself, so this is a proposer and not a decider, which by the coverage argument above is
the win rather than the consolation.

An intermediate version of the bisector also cut the closed curve at the worst point AND its
ANTIPODE (`i + n/2`) — an invented convention, which on a triangle sliced a straight side in half.
Cutting at the single worst point turns the closed curve into one open curve and needs no second
point. It did not change the triangle's count, so the antipode was not the cause there; the
triangle's cost is unattributed, and the "three corners furthest from the centroid" diagnostic
written to attribute it returned two ADJACENT indices and is itself broken.

(A second fitter bug, also caught by the output rather than by reading: the arc scan started at
three points, `arc_err` needs four to fit anything, so it returned its sentinel on the first
candidate and never extended — a circle came back as **8 lines**. Arcs now start scanning at their
own minimum length.)

And program length is a **direct measure of grid damage**, far sharper than any distance: the
triangle's slanted sides staircase, so each splits into two pieces instead of one, and the excess
is countable. A perfect extraction yields the minimal program; every extra piece is an artifact.

Two failures, both now flagged rather than silent:

- **The circle contour was invalid** — 27 points, bbox 12x13 for a RADIUS-12 figure, i.e. half
  the boundary. **FIXED, and the first diagnosis of it was wrong.** I attributed it to "the
  chaining rules, not the walk"; measuring the rim graph showed the chaining was almost right —
  one connected component, 100 crossings, 92 of them already at degree 2. The fault was the 8 at
  degree **3**. `bt_chain_perpendicular` linked EVERY pair of crossings at a shared cell,
  including the two on OPPOSITE sides, which is a chord across the rim rather than a rim step;
  the walk took the chord and closed a loop half the figure's size. Two crossings are consecutive
  only when they sit on ADJACENT sides, and that is expressible without coordinates: the other
  two cells are diagonal exactly when they share a SECOND common neighbour besides the shared
  cell (the fourth corner of the 2x2 block), where opposite cells share only the one. With that
  guard the circle's rim is degree 2 everywhere, one component — a clean cycle (v1.4.0).

  The bug was invisible on axis-aligned shapes: the square measured degree 2 everywhere both
  before and after, so only a boundary that TURNS exposes it. The gate therefore asserts on the
  circle, and is mutation-checked by restoring the all-pairs rule.
- **The first fitter returned four ARCS for a square.** It tested line-then-arc at each extent, so
  the greedy ran past a corner — an arc can bend around one and a line cannot. Preferring
  whichever piece explains MORE, tie to line, gives four lines.

What this implies and does not: the codebook of programs is small by construction, and a deformed
square should decode as square-plus-residual rather than as a new entry. That last step is
**not measured** — the residual comparison it needs was run against the invalid circle contour and
has to be redone once smooth boundaries extract.

### The check that should have run first, now gated

Three conclusions in this document were retracted because they were measured on contours that
were quietly broken — a radius-12 circle producing a 27-point contour with bbox 12x13, half its
boundary, which every downstream comparison accepted and reported numbers on. The check that
catches it is five lines: **a simple closed curve accumulates exactly +/-2pi.**

`test_every_extracted_contour_is_a_simple_closed_curve` runs it over a battery and fails loudly
rather than letting an extraction regression silently degrade whatever is measured on top. The
battery deliberately includes shapes whose boundaries TURN — circle, ellipse, diamond, triangle —
because the adjacent-sides defect was invisible on axis-aligned ones: a square passed both before
and after the fix, so a suite of rectangles would have gated nothing.

Verified against the actual historical defect: restoring the all-pairs chaining rule makes the
ellipse come back as 20 points with turning +0.00 and bbox 14x5, and the gate fails on it.


### Landed as a gate

The coverage measurements above are research and stay in this document — each observation is a
full rasterise-and-settle, so they run in minutes. The MECHANISM is gated, at a scale that runs
in ~1s (`test_orbit_recognition_snaps_to_distinct_members_and_decides_in_the_graph`), and it
pins all three findings at once:

- **snapping**: 180 angles must collapse to a smaller distinct-raster set, deduped before
  settling so only genuinely different members cost work;
- **off-manifold**: the observation is 15% larger than anything held and at an angle nothing was
  stored at, so the test cannot pass by containing its own answer — the on-manifold version
  scored 100% and was measuring its own construction;
- **graph-native verdict**: the decision is one `Argmin` over `OrbitMember` nodes with
  `ScTpsDist` as the value, not a Python `min`.

Mutation-checked: inverting the expected verdict fails the test.

That ceiling is the architectural point: **coverage is the bound on what any amount of context
can reach.** Accuracy is recoverable downstream; coverage is not. It is also the same shape as
this repo's Omniglot finding, where coverage@5 of 53.8% was the measured bottleneck and re-rank
converted ~70% of the cases where the true exemplar was present at all.

Two further facts the orbit view makes visible, which the shape view could not:

- **The orbit is QUANTISED by the sampling.** A 6x6 square rotated 7 degrees rasterises
  *identically* to 0 degrees — the rotation is below the grid's resolving power. The family is
  not a continuum in observation space but a finite set of distinct rasters, and asking which
  member an observation IS becomes a well-posed discrete question.
- **The first version of this test scored 100% and was a tautology.** The candidate angles
  contained the observed angles exactly, so the "render" WAS the observation byte-for-byte. Moving
  the observations off the candidate grid dropped it to 59%. A perfect score is the strongest
  signal available that the test is measuring itself.

**So the intrinsic representation is right and the extraction is the blocker.** Vertices and
angles carry no frame, exactly as intended; but a stable vertex SET cannot be recovered from a
lattice raster at this resolution, because the staircase invents and destroys corners as the
shape turns. The root cause is unchanged from the section below — it has simply been pushed from
the metric into the vertex set, which is where it was always going to end up.

(The two intrinsic rows cover 24 of the 32 contours: some contours simplified below three
vertices and produced no intrinsic signature at all, so the populations are not perfectly
matched to the 496-pair baseline.)

**CORRECTION.** An earlier version of this section concluded that the comparator was "the larger
of the two" failures. That was measured on the single 0-vs-90 pair — **the one case with zero grid
damage**, since a 90-degree rotation is exact on a lattice. It is precisely the wrong basis for
that comparison. Powered across real angles the ordering reverses: **the grid is the dominant
term**, the comparator fix is real but only exposes it, and no comparator can recover a rotation
the lattice has already destroyed.

### And the verdict is ONE held Term, not a Python loop

The alignment above loops in Python and takes a min — composition in Python, which is precisely
what this project forbids. It is not necessary. The candidate poses are graph DATA
(`PoseCandidate` nodes holding transformed point lists; applying a 2x2 symmetry to a point list
is mechanical geometry, adapter work), and the whole verdict is a single Term over them:

```
Attr(Argmin(Neighbours(agent, "pose_candidate"), pc,
            ScTpsDist(observed, pc.points)), "idx")
```

`ScTpsDist` accepts an `Attr` as its argument, so a held point list feeds the comparator
directly — no marshalling, no loop, and the winning candidate's `idx` IS the pose delta the
caller wanted. Gated by parity: the Term and the Python loop select the same candidate on the
0-vs-90-degree contours, so the Python version is demonstrably replaceable rather than merely
analogous.

The split this lands on is the architecture's own: **the adapter computes the candidate geometry,
the graph decides which candidate wins.**

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
