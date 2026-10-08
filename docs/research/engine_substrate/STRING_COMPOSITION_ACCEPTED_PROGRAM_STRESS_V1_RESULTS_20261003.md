# Accepted string-program stress generalization v1 results

Date: 2026-10-03

## Results

The source-locked stress run generated 50 deterministic, unique, fixture-disjoint strings per task and scored each accepted artifact with native ProgEval. All 900 generated oracle outputs matched an independent formula implementation. Across 12 accepted task-arm artifacts (600 program-input evaluations), 258 outputs were correct (43.0%), no execution errors occurred, and only 2 artifacts were exact on all 50 rows.

| Arm | Accepted artifacts | Correct rows | Evaluated rows | Exact on 50 |
|---|---:|---:|---:|---:|
| Main | 3 | 63 | 150 | 0 |
| Retrieval bypass | 2 | 16 | 100 | 0 |
| Retrieval bypass, 500k | 4 | 116 | 200 | 2 |
| Main replay | 3 | 63 | 150 | 0 |

Both exact artifacts are escalated-arm solutions to the split-then-reverse-tokens family. Main and replay repeat the same candidates, and some no-retrieval arms also return the same candidate for the same task; therefore 12 artifacts are not independent samples. The sole main-arm candidate that passed the original three heldouts in casefold-count scored 47/50 on the new sample. Other accepted casefold-count programs scored 0/50 or 16/50. The deterministic prefix curve flagged 4/12 artifacts after one validation row, 8/12 by two rows, and 10/12 by 20 rows; the remaining two artifacts were exact over all 50. All ten non-exact artifacts had a first observed error by row 14. These are duplicated artifacts for three unique candidate programs: the two incorrect task-01/task-03 programs recur across arms, and the task-02 candidate recurs in main/replay. The candidate that passed the original three heldouts failed first at stress row 14, then had 47/50 correct. Thus three additional rows would not have caught that candidate; a larger randomized sample matters.

## Prefix calibration

The v1.1 capture stores per-row correctness in generation order. Prefix sizes count how many of the 12 accepted artifacts show at least one error by that row. This is a retrospective calibration using known benchmark oracles, with duplicates across arms and only three unique candidate programs. It is not an independent estimate of a production verifier threshold. The source-locked [v1.1 amendment](STRING_COMPOSITION_ACCEPTED_PROGRAM_STRESS_V1_1_AMENDMENT_20261003.md) defines this additional analysis.

## Interpretation

The new sample confirms a high false-acceptance risk in this synthetic suite, in addition to the previously measured search gaps. The 43% row accuracy is pooled across a heavily duplicated set of outputs and only two task families have accepted candidates, so it is not a general capability estimate. It does indicate that the acceptance/verification protocol needs larger or adaptive validation sets, and that exactness on the original three holdouts should be described as a small-sample result.

This scores existing accepted programs only. It does not rerun search, identify the internal cause of false acceptance, or prove correctness on all inputs. Candidate-level traces and verifier-path attribution remain open because SynthEnumerate exposes only aggregate counters and the returned training-consistent candidate.

## Artifacts

- [Preregistration](STRING_COMPOSITION_ACCEPTED_PROGRAM_STRESS_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/stress_test_accepted_string_programs_v1.py)
- [Source lock](../../../evaluation/substrate_capability/accepted_string_program_stress_v1_lock_20261003.json) and [capture](../../../evaluation/reports/accepted_string_program_stress_v1_20261003.json)
