# GenInfer exact-linear prefilter v1.4 results: soundness repair, exact fallback stages, and fast-path prevalence (2026-10-06)

## Outcome

1. **The v1 prefilter was not semantics-preserving outside its panel.** With
   two predicates and identity slots, at the `max_dims=2` every seed
   `GenInfer` Term uses, the v1 dispatch disagreed with the historical
   enumerator in 145–701 of 1,488 cases per perturbation family, including
   253/1,488 exact linear images. The enumerator aligns relations by canonical
   sort and accepts per-predicate shift residuals; the v1 affine proof models
   only one global shift. The v1 panel's 15/15 parity result stands for its
   single-predicate fixtures only. No production path was affected: the
   runtime flag is off by default and no production producer emits identity
   slots (below).
2. **Repair plus two exact stages.** v1.4 restricts the affine proof to inputs
   where it provably coincides with the enumerator, then tries a
   row-factorized exact search and a correspondence-complete candidate
   generator before falling back to the enumerator. Over 37,500 finite cases
   (10 families × 6 point sets × all 625 matrices in [-2,2], including
   singular matrices), the full dispatch selected exactly the enumerator's
   result (matrix, residual count, transforms) in every case. The frozen v1.2
   oracle still reports 2,500 cases with digest `a8529e7d68e1c625`.
3. **Fast-path prevalence on production-shaped inputs is low for exact
   solves, high for fast refusal.** 0 of 10 production `dim_types`
   declarations carry an identity slot, so the v1 exact solve cannot be
   reached from any current producer. On production-shaped real handwriting
   (Omniglot, `["cell", r, c]`), 265/300 pairs were refused by the
   unconditional relation-count proof and 33/300 by the new correspondence
   stage; 1/300 still needed the enumerator. No pair of real drawings was
   related by a nonsingular integer map: every Omniglot "explained" result
   involved Braille dot drawings and a singular matrix.
4. **The three expensive v1 fallbacks are resolved at Term level**, with
   identical results on and off: rank-deficient 73.2 s → 0.56 ms, missing
   identity 4.0 s → 0.12 ms, duplicate identity 3.1 s → 0.67 ms.
5. **Real-data parity:** 914/914 pairs on/off identical apart from the
   `checked` work field; zero validator mismatches; stage counters conserve
   in every record. The independent analyzer passes 10/10 checks.

## What changed (feature `geninfer_linear_exact_prefilter`, runtime flag `agent.gen_linear_exact_enabled`, both still default off)

| Stage | Applies when | Cost per base | Output |
|---|---|---|---|
| Relation-count proof | always | O(1) | no fit (unconditional) |
| Affine identity-join solve (v1, now guarded) | single predicate; every slot before the first coordinate is `id`; full rank; unique, complete identity join | O(n) | the unique matrix, or a proven no-fit |
| Row-factorized search (new) | source rows have a unique pre-coordinate prefix (any number of predicates, any rank, mismatched identities) | O(n·(2b+1)²) per output row | the enumerator's Occam winner, or no candidate |
| Correspondence-complete generation (new) | no unique prefix, but some predicate block has three source rows with independent displacements | O(n_p³) hypotheses + validator per distinct integral in-bound hypothesis | the enumerator's winner, or no candidate |
| Historical enumerator | otherwise | O((2b+1)⁴·n log n) | unchanged |

Soundness arguments are in the source comments on
`infer_row_factorized_2d_linear` and `infer_correspondence_2d_linear`
(`runners/dsl/src/shape_decode.rs`). Briefly: with a unique prefix, sort
alignment does not depend on the matrix and `build_candidate`'s decision
factors over output rows; without one, any accepted matrix maps a full-rank
source triple in one predicate block to some target triple in that block, so
enumerating target triples covers every accepted matrix, and each hypothesis
is judged by the enumerator's own validator. A validator disagreement on the
row-factorized winner falls back (never observed).

## Gates

| Gate | Result | Evidence |
|---|---|---|
| G1 guard census: single-predicate divergence 0 with guards only | pass: 0/5,952 single-predicate, 0/8,928 multi-predicate (all fell back) | guard census log |
| G2 full dispatch = enumerator on 37,500 finite cases | pass: 0 divergences | release census log |
| G3 frozen v1.2 oracle unchanged | pass: 2,500 cases, `a8529e7d68e1c625` | release census log |
| G4 real-data parity | pass: 914/914 | v1.4b raw + analysis |
| G5 panel fallback fixtures identical on/off | pass: 4/4 | v1.4b raw + analysis |
| G6 zero validation mismatches | pass | v1.4b raw + analysis |

G2 path coverage (per 3,750-case family): the affine stage solved up to
1,250 and proved no-fit in up to 625; row-factorized solved up to 2,499 and
refused up to 3,750; correspondence found the winner in 635–1,874 and refused
1–1,240 in the three constant-identity families. The enumerator still handled
625 duplicate-identity cases and 1,875 cases in each constant-identity family
(the three rank-1 or repeated-coordinate point sets, which have no full-rank
predicate block and no unique prefix). Missing- and
duplicate-identity families produced no accepted matrices at `max_dims=2`,
so they check refusals only.

## Prevalence (v1.4b capture, 920 jobs)

| Input | Pairs | Path mix | Median on / off (ms) |
|---|---:|---|---:|
| Omniglot `prod` `["cell", r, c]` | 300 | 265 count proof, 33 correspondence no-candidate, 1 enumerator, 1 not attempted | 0.026 / 196 |
| Omniglot `id1` `["pt", k, r, c]` | 300 | 278 affine no-fit, 14 affine solved (all singular), 6 row-factorized, 2 not attempted | 0.020 / 114 |
| Omniglot `id2` (first/rest stroke predicates) | 300 | 219 row-factorized no-candidate, 70 affine no-fit, 9 affine solved (singular), 2 not attempted | 0.019 / 74 |
| `sdloop_vision` bars, 16×16 | 6 | 4 count proof, 2 correspondence found (90° rotation; reflection) | 0.08 / 14,960 |
| v1 panel training inputs | 4 | affine solved, 2 row-factorized, 1 correspondence | 0.34 / 3,542 |

"Not attempted" means the base had zero coordinate extent (`b=0`), which
`GenInfer` skips before any matrix work. The 23 Omniglot affine solves are
Braille dots: zero-length strokes make the arc-length resampler emit eight
copies of one point, and the zero matrix explains them. The one explained
`prod` pair (two Braille cells, matrix `[1,0,0,0]`) is the single enumerator
fallback. These are input-construction artifacts, reported as captured. Treat the Omniglot sample as
real-data coverage of the dispatch, not as a learning result.

The static census scanned literal `dim_types` in `domains/`, `worlds/`,
`substrate/`: 10 declarations, 9 with two coordinates, 0 with an `id` slot.
The fast exact solve and the row-factorized stage are therefore reachable
only from experiment fixtures today. The relation-count proof and the
correspondence stage apply to production-shaped frames.

## Scaling of the correspondence stage (`sdloop_vision.bar_frame`)

| Side | Relations (0°/90° ; 45°/135°) | b | Hypotheses | On (ms) | Off (ms) |
|---:|---|---:|---|---|---|
| 8 | 32 ; 44 | 7 | 4,096 ; 10,648 | 10 ; 33 | 468 ; 722 |
| 12 | 48 ; 72 | 11 | 13,824 ; 39,304 | 38 ; 144 | 3,932 ; 6,181 |
| 16 | 64 ; 100 | 15 | 32,768 ; 97,336 | 93 ; 373 | 17,815 ; 27,764 |
| 24 | 96 ; 156 | 23 | 110,592 ; 343,000 | 385 ; 1,475 | not run |
| 32 | 128 ; 212 | 31 | 262,144 ; 830,584 | 906 ; 3,691 | not run |
| 48 | 192 ; 324 | 47 | 884,736 ; 2,863,288 | 2,843 ; 12,563 | not run |

All recovered the same matrices as the enumerator wherever the enumerator ran
(`[0,1,-1,0]` with one residual dimension, `[-1,0,0,1]` with one). The
off arm was skipped above 3·10⁶ candidate matrices; at side 48 the
enumerator's bound is 95⁴ ≈ 8.1·10⁷ matrices. The new stage scales as the
cube of the smallest full-rank predicate block, so it is polynomial and much
cheaper than the quartic-in-`b` enumeration, but 12.6 s at 324 relations is
still not cheap. A larger frame will need an anchor or invariant that prunes
triples before validation.

## Limits

- Semantic equivalence is established on finite corpora (G2), the frozen
  oracle, and 914 real-data pairs, plus written arguments. It is not a
  machine-checked proof.
- Timings are single-host, in-process, minimum-of-three for the on arm and
  one run for the off arm. They measure the `GenInfer` Term alone, not
  full-seed closure.
- The Omniglot and bar inputs exercise the dispatch on real or production
  geometry. They do not show that GenInfer learns anything useful from
  natural data; on real handwriting the honest answer to "is there an exact
  integer linear map?" is almost always no, and v1.4 mainly makes that
  answer fast.
- Rung-three hypothesis induction and open-ended primitive minting are not
  addressed.

## Artifacts

- Preregistration: [v1.4](SUBSTRATE_GENINFER_PREFILTER_PREVALENCE_V1_4_PREREG_20261006.md); [v1.4b amendment](SUBSTRATE_GENINFER_PREFILTER_PREVALENCE_V1_4B_AMENDMENT_20261006.md)
- Exploratory v1.3 divergence census (transcribed console output): [`geninfer_prefilter_v1_3_residual_divergence_census_20261006.txt`](../../../evaluation/reports/geninfer_prefilter_v1_3_residual_divergence_census_20261006.txt)
- G1 guard census: [`geninfer_prefilter_v1_4_guard_census_20261006.log`](../../../evaluation/reports/geninfer_prefilter_v1_4_guard_census_20261006.log)
- G2/G3 release test run (10/10 prefilter tests including both censuses): [`geninfer_prefilter_v1_4_release_census_20261006.log`](../../../evaluation/reports/geninfer_prefilter_v1_4_release_census_20261006.log), SHA-256 `3bb0d544…`
- v1.4a capture, superseded by the amendment and kept unchanged: [raw](../../../evaluation/reports/geninfer_prefilter_prevalence_v1_4a_20261006.json), SHA-256 `c5496faa…`, native `08cd0a32…`
- v1.4b capture: [raw](../../../evaluation/reports/geninfer_prefilter_prevalence_v1_4b_20261006.json), SHA-256 `c2e86a2d…`; [analysis](../../../evaluation/reports/geninfer_prefilter_prevalence_v1_4b_analysis_20261006.json), SHA-256 `4bbad6a3…`; native `c0b4011c0d1dccde9d2e365c593982345a0aa74c8e50be27720ee280ba30b0ae` built from `shape_decode.rs` `41c2c67e…` and `scale_audit.rs` `bc57b37b…` with features `geninfer_quadratic_map_solver,geninfer_linear_exact_prefilter`
- [Runner](../../../evaluation/substrate_capability/geninfer_prefilter_prevalence_v1_4.py) and [independent analyzer](../../../evaluation/substrate_capability/analyze_geninfer_prefilter_prevalence_v1_4b.py)

## Next

1. Prune the correspondence stage (e.g., anchor the target's lexicographic
   minimum per block, or check a fourth row before calling the validator) and
   rerun the scale series with the same parity gate.
2. Handle rank-1 blocks without a unique prefix exactly (one correspondence
   plus one free direction), the remaining enumerator case in G2.
3. Measure the v1.4 dispatch inside full-seed closure on production-shaped
   workloads (`sdloop_vision`, ARC-style `["cell", r, c, val]`), with the
   locked v1 baselines, before considering a default-on change.
