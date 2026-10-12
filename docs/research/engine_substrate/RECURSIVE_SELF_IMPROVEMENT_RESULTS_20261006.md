# Recursive self-improvement plan: execution results (2026-10-06)

Plan: [RECURSIVE_SELF_IMPROVEMENT_PLAN_20261006.md](RECURSIVE_SELF_IMPROVEMENT_PLAN_20261006.md).
Each work package (WP) has its own raw report. WP2 and WP4 have a separate
results document:
[SUBSTRATE_VARIATION_CREDIT_ADOPTION_V1_RESULTS_20261006.md](SUBSTRATE_VARIATION_CREDIT_ADOPTION_V1_RESULTS_20261006.md).

## Summary

| WP | Claim | Result |
|---|---|---|
| 1 | Mints carry the aperture they were minted at; finer mints refine coarser ones exactly | **Pass.** 12 random panels (up to 72 observers): mints exact; 0 false and 0 missed refinement links against an independent oracle |
| 2+4 | The improver improves from its own outcomes, under P3-E1 statistics | **Pass.** 9/12 distributions improve, 0 harm, aggregate Δ +39.4 (lower CI 22.3); stale credit after a shift is a measured harm |
| 5 | Composition depth grows from minted structure | **Pass (v1.1).** 28/28 genuinely deep targets (length 3–6) recognised on a held-out base with chunking, 0/28 without; 0 false chunks |
| 3a | Grain ladder: the substrate picks a grain at which a map is exact | **Negative on real data.** 4/60 jittered handwriting cases recognised versus 8/60 cross-character controls: no discrimination |
| 3b | MDL witness: exact map explaining all but a few rows | **Pass (exploratory).** 30/30 equal-count outlier cases recover the planted map; 0/60 false explains on cross-character pairs |

All runtime behaviour is opt-in:

- `aperture_minting` and `variation_credit` are `self_load_only` seeds.
- Chunking needs `agent.gen_chunk_enabled`.
- The grain ladder needs `agent.gen_grains` (a list of grains to try).
- MDL needs both the `geninfer_grain_mdl` Cargo feature and `mdl_enabled`.

With none of these set, decode decisions are unchanged.

## WP1: aperture provenance and refinement

- `seeds/shape_decode_loop.json` v1.10.0. Every sd-loop mint records
  `minted_aperture`, `minted_grain`, `minted_dim_types`,
  `minted_from_signature` and `minted_epoch`. These are written through one
  shared idiom, `scripts/emit_mint_aperture_provenance.py`, so it can be
  applied to further mint sites. The first mint's value is kept, so dedup
  keys are unchanged.
- `seeds/aperture_minting.json`:
  - `am_mint_at_aperture`: an observer that opts in mints from a projected
    residual, and the axis inherits its aperture.
  - `am_refine_along_aperture`: axis F refines axis C iff C's aperture is a
    strict subset of F's and F's residual projected onto C's aperture equals
    C's residual exactly.
- `tests/test_aperture_minting_migrated.py`: 8 pass.
- Measurement: random 2-relation shapes, observers at three apertures, and
  an independent Python oracle. All 12 panels are exact. Closure takes
  19.7 ms at 72 observers.
  [Report](../../../evaluation/reports/aperture_minting_refinement_v1_20261006.json).

The 182-site gap named in `MINTING_AT_APERTURE.md` is closed for the four
sd-loop mint sites and the new aperture mint. The remaining mint sites in
other seeds do not yet use the idiom.

## WP5: chunking (compositional growth)

- `DimensionGenerator{kind:"composite", steps, ks}` is resolved in
  `shape_decode.rs::load_generators` into a flattened primitive sequence. A
  composite may name another composite; sequences are capped at 32 steps.
  `DimInfer`'s length-≤2 search is unchanged.
- `sd_chunk_composite` (v1.11.0) mints a recognised length-2 composition as
  a composite, with WP1 provenance.
- `tests/test_chunk_composite_migrated.py`: 4 pass. They cover a chunk of a
  chunk, recognition at depth 4, transfer to a different base, and that
  length-1 and scrambled observations chunk nothing.
- Measurement, v1.1:
  [report](../../../evaluation/reports/chunk_composite_depth_v1_1_20261006.json).
  The v1 run is preserved
  ([report](../../../evaluation/reports/chunk_composite_depth_v1_20261006.json)).
  It failed its "nontrivial" gate: under rotation, reflections and ×2 scale,
  most random sequences collapse to length ≤2, leaving only 5 of 30 cases
  genuinely deep. v1.1 added two held integer shears, whose group is
  infinite. Gates and arms were unchanged.

| depth | deep cases | chunking + curriculum | chunking, no curriculum | off |
|---:|---:|---:|---:|---:|
| 3 | 10 | 10 | 0 | 0 |
| 4 | 3 | 3 | 0 | 0 |
| 5 | 8 | 8 | 0 | 0 |
| 6 | 7 | 7 | 0 | 0 |

Depth comes from the curriculum, meaning exposure to the prefixes. Without
it, nothing deep is reached. Chunk count grows by one per new composition
(median 5 at depth 6). Each chunk enlarges `DimInfer`'s pairwise search, so
codebook growth needs a retention policy before broad use; this is not
measured yet.

## WP3: grain ladder and MDL witness

- `GenInfer` gains a `grain` field. Coordinates are re-quantised to
  `⌊(v − min)/2^g⌋`, and relations that coincide at that grain collapse.
- `sd_gen_check` (v1.12.0) picks the finest grain in `agent.gen_grains` with
  an exact invertible map; at coarser grains, a singular map is refused. The
  choice uses list membership rather than a numeric comparator, so the seed
  keeps its audited "no verdict bound" shape.
- `sd_recognize_at_grain` recognises the observation at that grain. It
  carries the sub-grain detail as a `CapabilityAxis{source:"grain_residual"}`
  rather than leaving the observation silently `decoded`.
- `infer_mdl_2d_linear` (feature `geninfer_grain_mdl`) works from
  correspondences on up to four disjoint anchor triples. It counts exact
  whole-tuple matches and accepts a map only if unexplained rows are fewer
  than half and the description length beats the raw cost. Unexplained rows
  are returned as `outliers`.
- [Report](../../../evaluation/reports/geninfer_grain_ladder_omniglot_v1_20261006.json):
  20 Omniglot drawings at 16×16, three planted maps outside the held
  codebook, four conditions. Native binary SHA-256 prefix `a11492771df9`,
  built with `geninfer_linear_exact_prefilter,geninfer_grain_mdl`.
  Exploratory: no preregistration. The first capture (`…_v1a_…`) used an
  integer `gen_grain_levels` and `Lte`/`Gt` comparators. Those broke four
  seed-audit tests (`tripwire_repair`, `uniqueness`, `ast_attr`), which pin
  that `shape_decode_loop` has no bound-like comparator. The seed was
  rewritten to use list membership and the measurement rerun; the counts are
  identical.

| condition | g0 (current) | ladder | MDL |
|---|---|---|---|
| exact `M·A` | 60/60 | 60/60 (grain 0) | 60/60 |
| jitter ±0.35 cell | 0/60 | 3 recovered, 1 wrong | 0/60 |
| 2 cells displaced | 0/60 | 2 recovered, 2 wrong | 30/60 recovered, 0 wrong |
| cross-character (false-explain control) | 0/60 | 3 + 5 false explains | 0/60 |

All 30 outlier cases where MDL refused had a changed relation count (two
displaced cells landed on occupied cells). MDL recovered every one of the 30
count-preserving cases.

The ladder fails for a structural reason. Dyadic coarse-graining commutes
only with maps that preserve the lattice grid, i.e. signed permutations and
scaling. For a shear, `⌊x + y⌋ ≠ ⌊x⌋ + ⌊y⌋`, so an exact fine map does not
become an exact coarse map, and a coarse grain explains unrelated shapes as
often as related ones. Leave `gen_grains` unset. The ladder is the
right mechanism for the held rotation/reflection/×2 generators (`DimInfer`),
which this package did not cover.

## Dual-process scheduling

- `dual_process_core` is available but not required. It moved from
  `CORE_SEEDS` to `OPTIONAL_CORE_SEEDS`, and `adaptive_control_core` and
  `default_mode_core` no longer depend on it.
- Loading it still selects the DualProcess cycle plan. Unlabelled rules then
  settle after System 1/2: this is fix `3460f381`, ported from
  `experiment/marys-room-eye-qualia`.
- The 5 failures in dual-process-adjacent tests (doom, embodied, metacognitive
  and program-self-modification) fail identically with and without the
  `CORE_SEEDS` change.

## Regression check

I ran the 88 `*_migrated` test files that reference the changed seeds or
functions, comparing against a baseline with this session's seed and Python
edits reverted. The engine was the same in both runs; its Rust changes are
opt-in.

- 47 failed with the changes, 40 with them reverted.
- Of the 7 new failures:
  - 6 were the seed-audit comparator shape, fixed as above.
  - 1 was `test_composer_driver_migrated.py::test_induce_concern_parity`,
    caused by the new additive `minted_*` keys. The test now strips and
    separately asserts that provenance, and still requires every
    pre-existing attribute to match the fixture.
- All 7 pass after the fixes. The 40 baseline failures predate this session's
  work.
- The full `-k migrated` suite (about 5,000 tests, an estimated 8+ hours on
  this host) was not run to completion.

## What this does and does not establish

**Established, on authored inputs and selected real handwriting:**

- Mints carry aperture provenance and refine exactly along it.
- The variation policy improves from its own experiment outcomes, held-out,
  under P3-E1's decision rule.
- Composition grows past the search depth from minted chunks.
- An exact MDL witness recovers maps under partial corruption, with no false
  explains in the control.

**Not established:**

- Unattended recursive improvement. Candidate construction, the WP2
  experiment world, the curriculum in WP5 and adoption custody are authored
  or human-gated.
- That the credit rule itself, rather than its values, is learned.
- That growth is bounded: chunks and credit both accumulate without
  retention.
- Natural-task benefit.
