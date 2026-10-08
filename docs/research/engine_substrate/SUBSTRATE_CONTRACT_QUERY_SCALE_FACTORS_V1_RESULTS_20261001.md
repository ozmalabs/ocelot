# Contract query scaling factors v1 — results

All 14 source-locked workers completed without errors. The independent analyzer verifies each maximum-entropy query, label, final singleton, and native evaluator call count. Each factor is reported against the shared H=32, D=0, N=20 baseline.

| Factor | Setting | Median native evaluations | Median loop time | Relative to baseline |
|---|---:|---:|---:|---:|
| Hypothesis count | H=32, K=5, N=20 | 1,638 | 24.96 ms | 1.0× |
|  | H=256, K=8, N=32 | 21,716 | 501.05 ms | 20.1× |
|  | H=512, K=9, N=36 | 49,102 | 1,302.13 ms | 52.2× |
| Neutral Term depth | D=0, total depth 5 | 1,638 | 24.96 ms | 1.0× |
|  | D=16, total depth 21 | 1,638 | 87.38 ms | 3.5× |
|  | D=64, total depth 69 | 1,638 | 304.23 ms | 12.2× |
| Candidate grid | N=20 | 1,638 | 24.96 ms | 1.0× |
|  | N=100 | 6,598 | 100.69 ms | 4.0× |
|  | N=500 | 31,398 | 467.46 ms | 18.7× |

The evaluator-call counts reflect the selector's nested work directly. Grid-size calls rise almost linearly with N at fixed H and Term depth. Term padding leaves call count constant but increases cost per evaluation, from 15.2 μs median per counted evaluation at the baseline to 185.7 μs at depth 69. Hypothesis growth also increases per-evaluation cost in this particular binary-code construction (15.2→26.5 μs), in addition to increasing the number of evaluations. At H=512, the full selected-query loop takes about 1.3 seconds on this host. The results indicate that candidate evaluation—not merely the number of oracle queries—will constrain open-ended exploration unless caching, batching, or search pruning reduces repeated work.

## Limits

The Terms use nested equality branches with a controlled neutral-depth wrapper, and all candidate inputs are small integers. Only two fresh processes were used per cell on one host. This is a source-locked workload scaling result, not an asymptotic theorem, a general Term operator profile, or a natural-task cost estimate. The earlier open-world control still applies: more hypotheses and more queries do not prove the intended program exists in the candidate set.

## Artifacts

- [Preregistration](SUBSTRATE_CONTRACT_QUERY_SCALE_FACTORS_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/substrate_contract_query_scale_factors_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_contract_query_scale_factors_v1.py)
- [Lock](../../../evaluation/substrate_capability/substrate_contract_query_scale_factors_v1_lock_20261001.json)
- [Capture](../../../evaluation/reports/substrate_contract_query_scale_factors_v1_raw_20261001.json)
- [Analysis](../../../evaluation/reports/substrate_contract_query_scale_factors_v1_analysis_20261001.json)
