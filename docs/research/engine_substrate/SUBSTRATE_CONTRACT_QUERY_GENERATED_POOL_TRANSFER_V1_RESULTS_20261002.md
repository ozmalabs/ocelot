# Generated-pool lazy query-matrix transfer v1 — results

## Result

The source-locked transfer panel completed nine fresh workers: three repetitions each for triangular numbers, scalar squares, and Euler characteristic. The independent analyzer reports zero errors across the source/native lock, complete pools, pool digests, independent Term replay, query replay, oracle labels, paired semantic parity, and held-out checks. Generated pool sizes were 9, 1, and 34 respectively; all three pools were complete and contained at least one hypothesis matching every held-out label.

Uncached and lazy-matrix arms selected identical query histories, entropy scores, predictions, oracle labels, terminal states, and survivors in every worker. All surviving hypotheses predicted every held-out answer exactly. The square control was singleton from generation and performed zero queries and zero matrix evaluations.

## Cost

| Task | Pool generation median | Queries | Uncached selector median | Lazy selector median | Native calls, uncached → lazy |
|---|---:|---:|---:|---:|---:|
| Triangular (H=9) | 560.66 ms | 1 | 0.874 ms | 0.878 ms | 144 → 117 |
| Square (H=1) | 45.52 ms | 0 | 0 ms | 0 ms | 0 → 0 |
| Euler (H=34) | 682.96 ms | 2 | 3.622 ms | 2.780 ms | 842 → 510 |

On the two nontrivial generated pools, lazy evaluation reduced measured native calls by 18.8% for triangular and 39.4% for Euler. Timing was effectively tied on the one-query triangular task and 1.30× faster on Euler. Pool generation took 46–683 ms, versus 0.9–3.6 ms for selection, so these selector results do not produce a measurable end-to-end learner speedup claim.

## Interpretation and limits

This establishes transfer of the lazy selector's semantic parity and a selective work reduction to the exact hypothesis pools produced by the bounded synthesis grammar for three previously authored tasks. It is not evidence of fresh task discovery, general hypothesis induction, or a favorable end-to-end learning cost. Task families, candidate domains, grammar, and held-outs remain authored and finite; only three repetitions were run. The square pool is a useful zero-query control but provides no matrix performance evidence.

## Reproduction artifacts

- Protocol: [preregistration](SUBSTRATE_CONTRACT_QUERY_GENERATED_POOL_TRANSFER_V1_PREREG_20261002.md)
- Runner: [source-locked runner](../../../evaluation/substrate_capability/substrate_contract_query_generated_pool_transfer_v1.py)
- Analyzer: [independent replay analyzer](../../../evaluation/substrate_capability/analyze_substrate_query_generated_pool_transfer_v1.py)
- Lock: [source/native lock](../../../evaluation/substrate_capability/substrate_contract_query_generated_pool_transfer_v1_lock_20261002.json)
- Capture: [raw worker data](../../../evaluation/reports/substrate_contract_query_generated_pool_transfer_v1_raw_20261002.json)
- Analysis: [machine-readable analysis](../../../evaluation/reports/substrate_contract_query_generated_pool_transfer_v1_analysis_20261002.json)
