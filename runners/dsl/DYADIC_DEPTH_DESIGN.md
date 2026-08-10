# Refinement-depth as a first-class additive dimension — DESIGN

Status: **DESIGN ONLY. NOT IMPLEMENTED.** This hits the task's STOP
condition (it needs a new node attr + edges and/or a change to
`build_candidate`'s cardinality contract — it does NOT reduce to a clean
`DimensionGenerator` diff of the scale2/modular shape). See §2/§5.

Invariant honoured throughout: GROUNDED signatures are integer-lattice
only; refinement depth is a DISCRETE integer count. Nothing below
introduces a continuous coordinate. (`coord_ints` returning `None` on a
`Float` slot stays correct and untouched.)

## 1. What "refinement-depth +1" maps, exactly

The natural coordinate candidate is the **dyadic / quadtree child
origin**: at depth `d` a coordinate `x` maps to `2x` at depth `d+1`
(each cell's origin becomes the lowest corner of its 2^ndim children),
and the NEW detail is the residual children that do not exist at the
coarser level.

The problem: **that coordinate map is `x -> 2x`, which is byte-for-byte
what `scale2` (`scale_pow2_once`, `v -> 2*(v-min)`) already computes.**
At the level of an observed signature (a set of occupied-cell
relations) a pure `x -> 2x` depth step and a `scale2` k=1 step produce
the *identical* transformed signature. They are **mathematically
indistinguishable at the signature level.**

The distinction the concept wants is real but lives OFF the occupied-cell
coordinates:

| | scale2 | refinement-depth |
|---|---|---|
| what changes | the SHAPE grows in a FIXED lattice | the LATTICE gets finer under a FIXED shape |
| cell count | preserved (3 cells → 3 cells, spread out) | area-preserving subdivision MULTIPLIES it (1 cell → 2^ndim filled children) |
| new structure | none — same cells, farther apart | residual children (finer detail) that had no coarse-level existence |
| semantics | "bigger" | "same thing, seen closer" |

Neither differentiator is a count-preserving coordinate remap:

- The **count-preserving** reading (`x -> 2x`, child origin only) carries
  none of the "children / finer grain" meaning — it is an ALIAS of
  scale2. To separate "same shape at finer grain" from "bigger shape in
  same grid" you must add graph data the signature does not currently
  carry: a `depth` integer attr on the region/quantum, and/or
  `child_of` / `refines` edges linking a fine quantum to its coarse
  parent. Only with that data is depth a distinct dimension rather than
  a second name for scale2.
- The **count-multiplying** reading (real subdivision: one filled coarse
  cell → 2^ndim filled fine children) is the physically-correct one, and
  it changes the relation count (e.g. a 3-cell tromino → 12 cells at
  depth+1). That is exactly what a `DimensionGenerator` cannot express.

## 2. Does it reduce to a `DimensionGenerator`? — NO

A `DimensionGenerator` is, by the code's contract, a **count-preserving
per-relation coordinate remap applied k times**:

- `apply_generator_once` / `apply_generator_k` rewrite each relation's
  coord slots via `set_coord` and return a signature of the SAME length
  (`out.len() == sig.len()`).
- `eval_dim_infer` hands the transformed signature to `build_candidate`,
  whose FIRST check is:

```
// runners/dsl/src/shape_decode.rs, build_candidate
if sorted_h.len() != sorted_o.len() {
    return None; // relation-count mismatch — not a candidate at all
}
```

So the generator framework structurally CANNOT:

1. Multiply relations (the area-preserving subdivision, §1 row 2) — the
   transformed candidate would have `len 12` against a `len 12` goal
   only if the generator itself emitted 12 relations, which
   `apply_generator_k` never does (it is 1-relation-in-1-relation-out).
   A subdivision generator would need `build_candidate` (or a new
   count-aware candidate builder) to accept a cardinality change — a
   change to the sd-loop's core consistency contract, not an additive
   arm.
2. Distinguish depth from scale in the count-preserving reading — a
   `kind:"dyadic"` arm calling the SAME `x->2x` math as scale2 adds no
   capability (scale2 already recognises every ×2^k), only a redundant
   name. Worse, both generators would "explain" the same observation and
   DimInfer's Occam tie-break (fewest dims, then base name, then k) would
   pick a winner by generator-name string ordering — an arbitrary,
   fragile alias, not a new dimension.

**Therefore refinement-depth does NOT reduce to a clean generator diff
of the scale2/modular shape.** It requires either new node/edge types
(`depth` attr, `refines`/`child_of` edges) or a change to
`build_candidate`'s equal-count contract — both explicitly outside the
safety-valve's "clean generator diff" branch.

## 3. Occam / termination (how it WOULD stay mint-once) — for the record

Had it been a generator, it would ride the existing
`sd_infer_dimension` / `sd_recognize_dim` pipeline unchanged: the
`has_transform`-edge guard mints the `latent:*` dimension exactly once
and re-recognises without re-minting under `codebook_epoch` growth,
exactly as scale2/modular do. Occam order (existing-basis transform <
new dimension < new quantum) is enforced by the rung guards, untouched.

This is precisely why the ALIAS reading is tempting and precisely why it
is wrong: it would inherit all the machinery for free while realising
none of the concept. The termination story is not the hard part; the
representation is.

## 4. Concrete gate fixtures (asymmetric, so "depth k" is meaningful)

For whichever integration is eventually chosen, the discriminating
fixtures must SEPARATE depth from scale (a symmetric fixture proves
nothing, per the existing suite's tromino note):

- **Subdivision fixture (count-multiplying):** coarse shape = one filled
  cell `[("cell",0,0,"red")]`; depth+1 goal = the 2×2 filled block
  `[("cell",0,0,"red"),("cell",0,1,"red"),("cell",1,0,"red"),("cell",1,1,"red")]`.
  Asymmetric vs scale2 k=1 of the same input, which is still the single
  cell `[("cell",0,0,"red")]` — so a correct depth op and scale2 give
  DIFFERENT outputs on the same input (the discriminator).
- **Depth-2 fixture:** the single cell → 4×4 = 16 filled children, to
  assert the reported `k` is 2 not 1.
- **Alias null:** a ×2-spread tromino (`{(0,0),(0,2),(2,0)}`) must remain
  scale2's win, NOT a depth win — proving depth does not cannibalise
  scale2's family (would fail immediately for a `kind:"scale2"` alias).
- **Termination:** epoch bump re-arms, `refines`/`child_of` (or the
  `depth` attr) minted exactly once.

## 5. Proposed minimal correct integration + risk assessment

Recommendation: **do NOT add a depth `DimensionGenerator`.** Realise
refinement depth where it actually lives — the `space_quantize.rs` flood
ladder ("the remainder goes to more detail"), which already owns the
residual→refine loop, `epoch`, `body_key`, per-dim `lo`/`hi`,
`stale`/`stale_dim`, and `split_along_dim`.

Minimal correct shape (Part-B-style, graph-data-first):

1. **`SpaceQuantum` gains a `depth` Int attr** (default 0), stamped when
   a quantum is created. Additive, int-lattice-only — honours the
   invariant directly (depth is a discrete count).
2. **A `refines` (or `child_of`) edge** (fine quantum → coarse parent),
   the graph-data expression of "this detail is the residual of that
   coarser region at depth+1". This is the datum that makes depth a
   DISTINCT dimension from scale2 (§1).
3. **A `qf_refine_residual` seed Rule** that, when a quantum's residual
   cannot be covered at the current grain, mints a child quantum at
   `depth+1` with a `refines` edge — the flood ladder's "remainder goes
   to more detail" made explicit at quantum grain, mint-once via a
   no-`refines`-edge-yet guard mirroring `sd_recognize_dim`'s
   `has_transform` guard.
4. Optionally, a `latent:depth` `LatentDimension` minted alongside so
   the depth dimension is first-class graph data like `latent:scale2`
   — but keyed off the quantum `depth`/`refines` structure, NOT off a
   signature coordinate remap.

Risk assessment:

- **Touching `space_quantize.rs`** is the exact sprawl the task warns
  against. The primitive already documents an *unbuilt* `qf_stale_on_block`
  residual→refine contract (see its module header §"stale_dim /
  stale_pose"); a `depth`/`refines` addition should be co-designed WITH
  that Part-B rule set, not bolted on, or the two refine loops will
  diverge. HIGH risk of interacting with in-flight quanta-navigation work.
- **Changing `build_candidate`'s equal-count contract** to admit
  subdivision would ripple into ShapeDecode, TransformDecode, and every
  rung-2 test that relies on count-equality as a prefilter. HIGH risk;
  not additive; out of scope.
- **Adding a `kind:"dyadic"` scale2-alias generator** is LOW risk but
  WRONG (no capability, arbitrary Occam aliasing, does not realise the
  concept). Explicitly rejected.

Net: the clean, additive, low-blast-radius realisation is the
`SpaceQuantum.depth` + `refines`-edge + `qf_refine_residual` rule route,
co-designed with the flood ladder's existing residual→refine contract —
NOT a `DimensionGenerator`. That work exceeds a clean generator diff and
is deferred for review per the STOP condition.
