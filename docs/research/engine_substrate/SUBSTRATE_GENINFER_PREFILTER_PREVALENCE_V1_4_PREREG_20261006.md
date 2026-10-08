# GenInfer exact-linear prefilter v1.4: soundness repair, row-factorized search, and fast-path prevalence — preregistration (2026-10-06)

## Why a v1.4

The v1 three-build panel (480 workers, 15/15 gates) used only single-predicate
fixtures (`["cell", id, r, c, "red"]`). An exploratory Rust differential run
after that panel compared the prefilter dispatch with the historical
enumerator on two-predicate, id-bearing inputs at `max_dims=2` (the value all
51 `GenInfer` Terms in `seeds/shape_decode_loop.json` use). It found
divergences in every family tried, including exact linear images (253/1,488)
and predicate-local shifts (701/1,488). Cause: the enumerator aligns relations
by canonical sort and accepts generator-plus-residual decompositions,
including per-predicate (tier-2) coordinate shifts; the v1 prefilter's
identity-joined affine proof only models a single global shift. The panel's
semantic-parity result therefore holds for its single-predicate fixtures
only. This was found before any v1.4 measurement below and is disclosed as an
exploratory finding; the v1 panel is not rerun.

## Changes under test (feature `geninfer_linear_exact_prefilter`, runtime flag unchanged)

1. Guards: the affine proof is used only when every slot before the first
   coordinate is `id`, no `id` follows a coordinate, and all source/target
   rows share one predicate value. Otherwise `Fallback("identity_not_sort_prefix" | "multiple_predicates")`.
   The relation-count proof stays unconditional.
2. Row-factorized exact search, tried on every affine fallback: when source
   rows have a unique pre-coordinate prefix (so sort alignment is
   matrix-independent), compute the enumerator's Occam winner over each
   output row separately — O(n·(2b+1)^2) per row instead of O(n·(2b+1)^4) —
   and validate the winner through `build_candidate`. Non-unique prefixes,
   symbolic coordinate targets and non-integer base coordinates still use the
   enumerator. A validator disagreement also falls back (counted).

## Gates

- G1 (guard census, Rust, exploratory build): with guards only, zero
  divergence on single-predicate sets across six residual families.
- G2 (row-factorized census, Rust): full production dispatch equals the
  historical enumerator in every case across 7 families × 6 point sets
  (multi-predicate, rank-1, repeated coordinates, identity swap, missing and
  duplicate identity), all 625 matrices in [-2,2] including singular ones.
- G3 (frozen oracle): the v1.2 finite oracle still reports 2,500 cases and
  digest `a8529e7d68e1c625`.
- G4 (real-data parity): on every Omniglot pair where the prefilter-off arm
  runs, prefilter-on and prefilter-off `GenInfer` results are identical apart
  from the `checked` work field.
- G5 (expensive-fallback fixtures): the v1 panel's rank-deficient,
  missing-identity and duplicate-identity training inputs give identical
  results on/off at the Term level; record which path handled each.
- G6: zero `validation_mismatch` row-factorized fallbacks anywhere.

## Prevalence measurement (descriptive; no thresholds)

Representative inputs:

- Static schema census of every `dim_types` declaration in `domains/`,
  `worlds/`, `substrate/` (production producers): whether each schema can
  ever reach the affine or row-factorized path (needs an `id` prefix).
- Omniglot `strokes_background` real handwriting, deterministic sample
  (first 10 alphabets by name, first 2 characters each, drawers 1–5, all
  within-character drawer pairs plus an equal number of cross-character
  pairs), three schemas on an 8×8 lattice:
  `prod` = `["cell", r, c]` occupied cells (the ARC/vision producer form);
  `id1` = 8 arc-length resampled points `["pt", k, r, c]`;
  `id2` = the same points with predicate `first`/`rest` stroke.
- `sdloop_vision.bar_frame` orientation pairs (production producer, two
  predicates, no id).

For each pair: prefilter outcome class (affine solved / affine no-fit by
reason / row-factorized solved / no-candidate / enumerator fallback by
reason), wall time on/off, and whether a generator was explained. The
prefilter-off arm runs only when the enumerator's `(2b+1)^4` bound is at most
3·10^6 matrices.

## Claim boundary

A pass supports semantic equivalence of the v1.4 dispatch with the historical
enumerator on the tested finite corpora and real-data pairs, and reports how
often production-shaped inputs can use the fast paths. It does not establish
natural-task benefit, general GenInfer tractability, or rung-three
hypothesis induction.
