# Dynamic quantization (the sd loop)

The core learning mechanism shared by every capability in this tree. If you
read one feature doc, read this one — vision, handwriting, program synthesis,
and spatial navigation are all this same loop applied to a different
observation stream.

## The idea

An observation is **decoded** against a held codebook of learned "shapes"
(recurring structural patterns). Parts of the codebook compete to cover the
observation; whatever isn't covered is a **residual**. A residual that
recurs — rather than being noise — **mints a new codebook entry** (a
`CapabilityAxis` quantum, or for a spatial/coordinate residual, a
`LatentDimension`). The next decode has a bigger codebook, so it covers more,
so the residual shrinks. Growth *is* this loop reaching fixpoint, not a
separate training phase bolted onto it.

This is literally quantization — an observation is expressed as indices into
a discrete codebook, like vector quantization in a compressed-sensing sense —
except the codebook is not fixed in advance. It is *dynamic*: the codebook
itself grows as a side effect of the same decode operation that uses it.
Hence "dynamic quantization."

## Where it lives

- **Rust:** `runners/dsl/src/shape_decode.rs` implements the `ShapeDecode`
  Term (the decode/dequantization operation itself) plus the growth-ladder
  operations: `TransformDecode` (rung 2 — read a residual as one uniform
  delta along an *existing* dimension), `DimInfer` (rung 3 — infer that the
  residual needs a *new* dimension, minting a `LatentDimension` against a
  held `DimensionGenerator` codebook: rotation/reflection, log-scale `×2^k`,
  modular/cyclic wrap, ...), and plain novelty minting (rung 4, only after
  rungs 1–3 fail — Occam-ordered).
- **Graph rules:** `seeds/shape_decode_loop.json` — `sd_decode` /
  `sd_recognize` / `sd_mint_quantum` / `sd_redecode` and the rung-2/3 rules
  (`sd_transform_decode`, `sd_recognize_transformed`, `sd_infer_dimension`,
  `sd_recognize_dim`). The **`run_rules` fixpoint IS the decode → grow →
  re-decode loop** — there is no Python iteration anywhere in it.
- **Composer / driver:** `compose_design_for_goal` and `induce_concern`
  (formerly a Python beam search in `reflective_faculty.py`) are the same
  `ShapeDecode` op applied at two points of one loop; `ground_concern`'s
  dispatch is a data table (`seeds/composer_dispatch.json`) plus a
  name-keyed Python registry lookup on the Term's verdict — not a Python
  decision tree.

## The growth ladder, in order (cheapest hypothesis first)

1. **Exact recognize** — the codebook already covers this, no growth needed.
2. **Transform in the existing basis** — the residual is one consistent
   delta along a dimension already known (e.g. every point rotated by the
   same 90°). A `Transform{dim, delta}` is minted; no new dimension.
3. **Infer the dimension** — the residual is coupled *across* the observed
   dimensions in a way no existing dimension explains (e.g. a 2D shape's
   rotation produces an XY coupling that can't be replicated without a Z
   axis). Decoded against a `DimensionGenerator` codebook; a
   `LatentDimension` is minted.
4. **Mint novelty** — only after 1–3 all fail. A genuinely new
   `CapabilityAxis` quantum is created.

This ordering matters: it is what keeps growth from exploding into "mint a
new quantum for every superficial variation" — most apparent novelty is
actually rung-2 or rung-3, a transform of something already known.

## The frame/continuum invariant this loop obeys

A late but load-bearing refinement: **in-frame values are integer; only the
maps *between* frames may be real-valued.** A `DimensionGenerator` may carry
a continuous parameter (an angle, a log-base) intensionally, but what lands
in the graph is always the stepped, integer *rendering* of it. Concretely:
`shape_decode.rs::coord_ints` returning `None` on a float slot is correct
and load-bearing, not a bug to "fix" by adding continuous coordinates. See
`CLAUDE.md`'s "BASE-AS-DIMENSION" section for the full argument (a "base" —
log-scale, modular cycle — is itself just another `DimensionGenerator`, not
hand-set config).

## What this loop has grown, concretely

- **Handwriting/ink** (`runners/dsl/src/strokes.rs` + the Omniglot arc) —
  strokes quantized into `seg` (turn/length) relations plus separate pose
  relations, so a rotated stroke reads as one rung-1 pose delta.
- **Program-synthesis constructions** (`docs/features/program-synthesis.md`)
  — the P3 "training run" is this loop decoding 24,778 statement instances
  into construction quanta + bigram rows.
- **Spatial/quanta navigation** (`docs/features/ls20-spatial.md`) — the same
  reframe applied to *space itself*: `SpaceQuantum` boxes decoded per body
  shape, per dimension, foveated.
- **Writer/speaker style** — per-writer or per-speaker pose deltas that
  cohere across one individual's output mint a `WriterStyle`/speaker
  dimension (rung 2 at the individual grain).

## For the full history

The growth-ladder design, the transform/dimension-inference rungs, and the
frame invariant are documented in depth across `CLAUDE.md`'s own body text
(search for "dynamic quantization", "BASE-AS-DIMENSION", "THE OMNIGLOT ARC").
For the underlying engine/rule-matching mechanics this loop depends on (the
`run_rules` fixpoint itself, incremental match, predicate retraction), see
`docs/research/engine_substrate/`.
