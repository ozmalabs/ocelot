# Generated-pool active query versus iterative resynthesis v1.5 results

## Result

The confirmatory source-locked capture completed **60 fresh-process workers**: three authored target functions × four arms × five randomized blocks. The independent analyzer passes **215/215 checks**, including current source and binary hashes, worker completeness, monotone survivor filtering, unique pool queries, complete-pool stop reasons, and held-out target survival. All four arms return an exactly held-out-correct result in all five runs for all three tasks.

Every generated pool is complete and contains a held-out-correct behavior:

| Target | Pool size | Terms explored | Entropy queries | Fixed-first queries | Random queries | MDL-CEGIS queries |
|---|---:|---:|---:|---:|---:|---:|
| Triangular number | 9 | 8,709 | 1 | 2 | 1 | 11 |
| Square | 1 | 945 | 0 | 0 | 0 | 10 |
| Euler characteristic | 34 | 10,269 | 2 | 5 | 2, 3, 2, 2, 2 | 17 |

The square pool is already behaviorally unique from its two training examples, so no query is needed. On Euler, entropy reduces queries against fixed-first but ties the median seeded-random count. All pool policies reach the correct survivor behavior.

## Cost

The primary learner-wall measure sums timed synthesis/pool construction, query selection plus prediction/filtering, and labeled training/query oracle calls. It excludes evaluator-only held-out support/scoring and task setup; those have separate timers in the raw capture. Paired median baseline-to-entropy ratios are **0.167 for triangular**, **0.0130 for square**, and **0.0317 for Euler**. In this bounded workload, complete-pool entropy learning is therefore about **6×, 77×, and 32× slower** than single-survivor MDL resynthesis, respectively. Fixed-first and random pool policies have similar costs because version-space generation dominates. Parent-observed process wall shows the same direction, with larger fixed startup/setup components.

The query reduction does not translate into end-to-end learner efficiency here. Single-survivor CEGIS explores fewer candidates and stops after one correct recipe; the generated-pool path pays to enumerate every fitting behavior before selecting queries. Entropy ranking and cached prediction cost little relative to that enumeration on these task sizes. These measurements directly identify a tractability boundary for the full-pool strategy.

## Scope and limits

The targets, input families, and bounded grammars are authored and small. This does not estimate a natural task distribution or prove the current strategy's behavior on larger hypothesis spaces. The MDL control is a source-locked inline replay of `cegis_synthesize`'s smallest-fit / first-disagreement / resynthesize loop. It calls `generator.synthesize` directly so both arms share the same fixed grammar; the production faculty API does not currently expose those grammar controls. This compares the algorithms under matched settings, not integration into the production CEGIS API. The experiment does not evaluate forgetting, persistent adoption, or LLM meta-improvement.

The v1.1 missing-fixture capture, v1.2 model-class diagnostic, v1.3 timing pilot, and v1.4 fixed-random-seed timing capture are retained at their original paths. Only v1.5 is used for the five-seed random-policy and corrected cost-accounting claims.

## Reproduction

Run `python3 scripts/substrate_generated_pool_cegis_comparison_v1.py --lock` and compare with the [v1.5 lock](../../../evaluation/substrate_capability/substrate_generated_pool_cegis_comparison_v1_5_20261001_lock.json). Then run the script and `python3 scripts/analyze_substrate_generated_pool_cegis_comparison_v1.py`. The [raw 60-worker capture](../../../evaluation/reports/substrate_generated_pool_cegis_comparison_v1_5_20261001_raw.json) and [215-check analysis](../../../evaluation/reports/substrate_generated_pool_cegis_comparison_v1_5_20261001_analysis.json) preserve the measured rows and computed summaries.
