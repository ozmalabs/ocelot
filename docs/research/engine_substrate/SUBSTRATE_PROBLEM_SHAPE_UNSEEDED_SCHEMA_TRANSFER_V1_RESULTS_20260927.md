# ProblemShape unseeded-schema transfer v1 results (2026-09-27)

## Outcome

All ten fresh full-seed workers completed on stable, source-locked inputs. The runner gates and an independent raw-data analyzer pass. The underlying CAN Goals resolved, and every observation's post-observation closure reached a fixed point.

The seeded `solve_can_exact` control was recognized with no mint. In both singleton-control workers, one `solve_can_relax` Goal and one `solve_can_bp` Goal remained residual, with distinct keys and no mint. Repeating relax Goals with different `k_starts` values caused one shape to be minted and both observations to end recognized; repeating BP Goals with `max_product` and `sum_product` behaved likewise. The mixed condition minted two distinct shapes, one for each family, and all four Goals ended recognized under their own family key. Both replicates of all five conditions matched these outcomes.

| Scenario (two workers) | Observations | ProblemShape candidate pairs | Term evaluations | Mint events / new shapes |
|---|---:|---:|---:|---:|
| Seeded exact control | 4 | 42 | 362 | 0 / 0 |
| Singleton controls | 4 | 48 | 516 | 0 / 0 |
| Relax recurrence | 4 | 64 | 980 | 2 / 2 |
| BP recurrence | 4 | 64 | 980 | 2 / 2 |
| Mixed family separation | 8 | 222 | 3,158 | 4 / 4 |

Counts aggregate both replicates. In recurrence runs, the second observation triggers minting; closure then re-decodes the first residual observation. The singleton controls provide a local check against minting from one observation alone. The mixed result supports structural separation of these two hand-selected schema families, while the varying parameter values test the codebook's presence-based abstraction.

## Interpretation and limits

This is evidence for a narrow form of rung-3 acquisition: repeated examples of two known-to-the-experimenter but unseeded CAN Goal schemas are grouped by `ProblemShape`, minted once per schema per worker, and reused for transfer. It does not show open-ended concept invention, broad false-mint precision, natural residual frequency, behaviorally safe abstraction over omitted parameter values, or downstream solver improvement. Each worker began with full seeds, scenarios were authored, and there were only two replicates per scenario. Instrumented candidate and Term counts are not uninstrumented latency; cold full-seed boot was roughly 13–15 seconds in these workers and dominates this experiment's setup.

The result narrows one empirical part of the tractability report: repeated held-out schema acquisition works for these two categorical signatures and singleton residuals do not trigger minting. The general rung-3/4 induction wall remains open. The next useful capability measurement is a larger, preregistered schema panel containing held-out positive variants, near-neighbor negatives, nuisance changes, and behavioral-equivalence checks, with precision/recall, residual-to-mint latency, transfer, and false-mint costs measured separately.

## Artifacts

- Preregistration: [SUBSTRATE_PROBLEM_SHAPE_UNSEEDED_SCHEMA_TRANSFER_V1_PREREG_20260927.md](SUBSTRATE_PROBLEM_SHAPE_UNSEEDED_SCHEMA_TRANSFER_V1_PREREG_20260927.md)
- Runner: [substrate_problem_shape_unseeded_schema_transfer_v1.py](../../../scripts/substrate_problem_shape_unseeded_schema_transfer_v1.py)
- Input lock: [problem_shape_unseeded_schema_transfer_v1_lock_20260927.json](../../../evaluation/substrate_capability/problem_shape_unseeded_schema_transfer_v1_lock_20260927.json)
- Raw workers: [problem_shape_unseeded_schema_transfer_v1_20260927.json](../../../evaluation/reports/problem_shape_unseeded_schema_transfer_v1_20260927.json)
- Independent analyzer: [analyze_substrate_problem_shape_unseeded_schema_transfer_v1.py](../../../scripts/analyze_substrate_problem_shape_unseeded_schema_transfer_v1.py)
- Independent analysis: [problem_shape_unseeded_schema_transfer_v1_analysis_20260927.json](../../../evaluation/reports/problem_shape_unseeded_schema_transfer_v1_analysis_20260927.json)
