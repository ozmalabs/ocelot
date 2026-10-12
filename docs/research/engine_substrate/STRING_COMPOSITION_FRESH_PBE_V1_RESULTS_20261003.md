# Fresh string-composition PBE v1 results

Date: 2026-10-03

## Results

The prelocked suite completed all 18 tasks in four arms. The independent analyzer recomputed all 126 fixture outputs, re-evaluated accepted IRs on held-out rows, and found zero errors; main and its fresh-substrate replay had identical outcome fingerprints.

| Arm | Exact held-out passes | Accepted wrong | Gaps | Tested candidates | Route seconds |
|---|---:|---:|---:|---:|---:|
| Main | 1/18 | 2 | 15 | 3.00M | 11.43 |
| Retrieval bypass | 0/18 | 2 | 16 | 3.09M | 6.05 |
| Retrieval bypass, 500k escalation | 2/18 | 2 | 14 | 7.58M | 16.16 |
| Main replay | 1/18 | 2 | 15 | 3.00M | 11.29 |

The main arm's only exact result was in casefold-then-count; the escalation arm's two exact results were in split-then-reverse-each-token. The other five composition strata had no exact passes in any arm. Retrieval changed one outcome to an exact pass relative to bypass, while the paired bootstrap interval was [0, 0.167] over only three examples per stratum. Raising the candidate ceiling recovered two exact cases and reduced gaps by two, but still left 14/18 gaps and two accepted false programs.

This is evidence of a narrow route boundary: the P4 path can solve some supported string compositions, but most of these newly generated compositions either gap under the fixed search limits or are accepted incorrectly. The 500k escalation materially raises candidate work for modest recovery. Task functions and operator compositions were human specified, so this is not operator invention, natural task prevalence, or a general capability estimate.

## Artifacts

- [Preregistration](STRING_COMPOSITION_FRESH_PBE_V1_PREREG_20261003.md)
- [Task generator](../../../tests/fixtures/substrate_string_composition_fresh/build_tasks.py) and [frozen suite](../../../tests/fixtures/substrate_string_composition_fresh/tasks.json)
- [Runner](../../../scripts/string_composition_fresh_pbe_v1.py) and [analyzer](../../../evaluation/substrate_capability/analyze_string_composition_fresh_pbe_v1.py)
- [Source lock](../../../evaluation/substrate_capability/string_composition_fresh_pbe_v1_lock_20261003.json), [capture](../../../evaluation/reports/string_composition_fresh_pbe_v1_20261003.json), and [analysis](../../../evaluation/reports/string_composition_fresh_pbe_v1_analysis_20261003.json)
